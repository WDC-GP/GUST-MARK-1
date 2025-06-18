/**
 * GUST Bot Enhanced - Storage Service
 * =================================
 * Manages local storage, session storage, and in-memory caching
 */

class StorageService {
    constructor(options = {}) {
        this.options = { ...this.defaultOptions, ...options };
        this.cache = new Map();
        this.eventBus = options.eventBus || window.App?.eventBus || window.EventBus;
        this.prefix = this.options.prefix;
        this.encryptionKey = this.options.encryptionKey;
        
        this.init();
    }
    
    get defaultOptions() {
        return {
            prefix: 'gust_',
            enableCompression: true,
            enableEncryption: false,
            encryptionKey: null,
            enableCache: true,
            cacheExpiry: 30 * 60 * 1000, // 30 minutes
            maxCacheSize: 100,
            enableQuota: true,
            quotaWarningPercent: 80,
            enableMigration: true,
            version: '1.0.0',
            enableBackup: true,
            backupInterval: 60 * 60 * 1000, // 1 hour
            enableSyncAcrossTabs: true,
            enableValidation: true,
            debug: false
        };
    }
    
    init() {
        this.checkSupport();
        this.setupQuotaMonitoring();
        this.setupBackup();
        this.setupCrossTabSync();
        this.migrateData();
        this.loadCache();
        
        this.log('Storage service initialized');
    }
    
    /**
     * Check browser storage support
     */
    checkSupport() {
        this.support = {
            localStorage: this.isStorageSupported('localStorage'),
            sessionStorage: this.isStorageSupported('sessionStorage'),
            indexedDB: 'indexedDB' in window,
            webSQL: 'openDatabase' in window
        };
        
        if (!this.support.localStorage && !this.support.sessionStorage) {
            console.warn('[StorageService] No storage support detected - using memory only');
        }
    }
    
    isStorageSupported(type) {
        try {
            const storage = window[type];
            const testKey = '__storage_test__';
            storage.setItem(testKey, 'test');
            storage.removeItem(testKey);
            return true;
        } catch (e) {
            return false;
        }
    }
    
    /**
     * Set item in storage
     * @param {string} key - Storage key
     * @param {*} value - Value to store
     * @param {Object} options - Storage options
     * @param {string} options.type - Storage type (local, session, memory)
     * @param {number} options.expires - Expiration timestamp
     * @param {boolean} options.encrypt - Whether to encrypt the data
     * @param {boolean} options.compress - Whether to compress the data
     */
    set(key, value, options = {}) {
        const config = { ...this.options, ...options };
        const storageKey = this.getStorageKey(key);
        
        try {
            const data = this.prepareData(value, config);
            
            // Store in specified storage type
            const storageType = config.type || 'local';
            this.storeData(storageKey, data, storageType);
            
            // Update cache if enabled
            if (config.enableCache) {
                this.updateCache(key, value, config);
            }
            
            // Emit storage event
            this.emitStorageEvent('set', key, value, config);
            
            this.log(`Stored '${key}' in ${storageType} storage`);
            return true;
            
        } catch (error) {
            this.log(`Failed to store '${key}':`, error, 'error');
            return false;
        }
    }
    
    /**
     * Get item from storage
     * @param {string} key - Storage key
     * @param {*} defaultValue - Default value if key not found
     * @param {Object} options - Retrieval options
     */
    get(key, defaultValue = null, options = {}) {
        const config = { ...this.options, ...options };
        
        try {
            // Check cache first
            if (config.enableCache && this.cache.has(key)) {
                const cached = this.cache.get(key);
                if (!this.isExpired(cached.expires)) {
                    this.log(`Retrieved '${key}' from cache`);
                    return cached.value;
                } else {
                    this.cache.delete(key);
                }
            }
            
            const storageKey = this.getStorageKey(key);
            const storageType = config.type || 'local';
            
            // Get from storage
            const rawData = this.retrieveData(storageKey, storageType);
            if (!rawData) {
                return defaultValue;
            }
            
            // Parse and validate data
            const data = this.parseData(rawData, config);
            if (!data) {
                return defaultValue;
            }
            
            // Check expiration
            if (data.expires && this.isExpired(data.expires)) {
                this.remove(key, { type: storageType });
                return defaultValue;
            }
            
            // Update cache
            if (config.enableCache) {
                this.updateCache(key, data.value, config);
            }
            
            this.log(`Retrieved '${key}' from ${storageType} storage`);
            return data.value;
            
        } catch (error) {
            this.log(`Failed to retrieve '${key}':`, error, 'error');
            return defaultValue;
        }
    }
    
    /**
     * Remove item from storage
     */
    remove(key, options = {}) {
        const config = { ...this.options, ...options };
        const storageKey = this.getStorageKey(key);
        const storageType = config.type || 'local';
        
        try {
            // Remove from storage
            this.removeData(storageKey, storageType);
            
            // Remove from cache
            this.cache.delete(key);
            
            // Emit storage event
            this.emitStorageEvent('remove', key, null, config);
            
            this.log(`Removed '${key}' from ${storageType} storage`);
            return true;
            
        } catch (error) {
            this.log(`Failed to remove '${key}':`, error, 'error');
            return false;
        }
    }
    
    /**
     * Check if key exists in storage
     */
    has(key, options = {}) {
        const value = this.get(key, Symbol('not-found'), options);
        return value !== Symbol('not-found');
    }
    
    /**
     * Clear storage
     */
    clear(options = {}) {
        const config = { ...this.options, ...options };
        const storageType = config.type || 'local';
        
        try {
            if (config.onlyPrefix) {
                // Clear only items with our prefix
                this.clearPrefixed(storageType);
            } else {
                // Clear all storage
                this.clearStorage(storageType);
            }
            
            // Clear cache
            if (storageType === 'local' || storageType === 'all') {
                this.cache.clear();
            }
            
            this.emitStorageEvent('clear', null, null, config);
            this.log(`Cleared ${storageType} storage`);
            return true;
            
        } catch (error) {
            this.log(`Failed to clear storage:`, error, 'error');
            return false;
        }
    }
    
    /**
     * Get all keys with our prefix
     */
    keys(options = {}) {
        const config = { ...this.options, ...options };
        const storageType = config.type || 'local';
        const keys = [];
        
        try {
            const storage = this.getStorage(storageType);
            if (storage) {
                for (let i = 0; i < storage.length; i++) {
                    const key = storage.key(i);
                    if (key && key.startsWith(this.prefix)) {
                        keys.push(key.substring(this.prefix.length));
                    }
                }
            }
            
            return keys;
        } catch (error) {
            this.log(`Failed to get keys:`, error, 'error');
            return [];
        }
    }
    
    /**
     * Get storage usage statistics
     */
    getUsage(options = {}) {
        const config = { ...this.options, ...options };
        const storageType = config.type || 'local';
        
        try {
            const storage = this.getStorage(storageType);
            if (!storage) return null;
            
            let totalSize = 0;
            let itemCount = 0;
            const items = {};
            
            for (let i = 0; i < storage.length; i++) {
                const key = storage.key(i);
                if (key) {
                    const value = storage.getItem(key);
                    const size = this.getItemSize(key, value);
                    
                    if (key.startsWith(this.prefix)) {
                        const cleanKey = key.substring(this.prefix.length);
                        items[cleanKey] = { size, key };
                        itemCount++;
                    }
                    
                    totalSize += size;
                }
            }
            
            // Estimate quota
            const quota = this.estimateQuota(storageType);
            const usagePercent = quota ? (totalSize / quota) * 100 : 0;
            
            return {
                totalSize,
                itemCount,
                items,
                quota,
                usagePercent,
                available: quota ? quota - totalSize : null
            };
            
        } catch (error) {
            this.log(`Failed to get usage:`, error, 'error');
            return null;
        }
    }
    
    /**
     * Backup storage data
     */
    backup(options = {}) {
        const config = { ...this.options, ...options };
        const data = {};
        
        try {
            // Backup localStorage
            if (this.support.localStorage) {
                data.localStorage = this.backupStorage('localStorage');
            }
            
            // Backup sessionStorage
            if (this.support.sessionStorage) {
                data.sessionStorage = this.backupStorage('sessionStorage');
            }
            
            // Backup cache
            data.cache = this.backupCache();
            
            // Add metadata
            data.metadata = {
                version: this.options.version,
                timestamp: Date.now(),
                userAgent: navigator.userAgent
            };
            
            const backupData = JSON.stringify(data);
            
            // Store backup
            if (config.download) {
                this.downloadBackup(backupData);
            }
            
            if (config.store) {
                this.storeBackup(backupData);
            }
            
            this.log('Storage backup created');
            return backupData;
            
        } catch (error) {
            this.log('Failed to create backup:', error, 'error');
            return null;
        }
    }
    
    /**
     * Restore storage data from backup
     */
    restore(backupData, options = {}) {
        const config = { ...this.options, ...options };
        
        try {
            const data = typeof backupData === 'string' ? JSON.parse(backupData) : backupData;
            
            // Validate backup
            if (!data.metadata || !data.metadata.version) {
                throw new Error('Invalid backup format');
            }
            
            // Clear existing data if requested
            if (config.clearExisting) {
                this.clear({ type: 'all', onlyPrefix: true });
            }
            
            // Restore localStorage
            if (data.localStorage && this.support.localStorage) {
                this.restoreStorage(data.localStorage, 'localStorage');
            }
            
            // Restore sessionStorage
            if (data.sessionStorage && this.support.sessionStorage) {
                this.restoreStorage(data.sessionStorage, 'sessionStorage');
            }
            
            // Restore cache
            if (data.cache) {
                this.restoreCache(data.cache);
            }
            
            this.emitStorageEvent('restore', null, data, config);
            this.log('Storage restored from backup');
            return true;
            
        } catch (error) {
            this.log('Failed to restore backup:', error, 'error');
            return false;
        }
    }
    
    /**
     * Watch for changes to a key
     */
    watch(key, callback, options = {}) {
        const config = { ...this.options, ...options };
        const watchId = `watch_${Date.now()}_${Math.random()}`;
        
        const watcher = {
            id: watchId,
            key,
            callback,
            immediate: config.immediate || false,
            storageType: config.type || 'local'
        };
        
        // Initialize watchers map if needed
        if (!this.watchers) {
            this.watchers = new Map();
        }
        
        this.watchers.set(watchId, watcher);
        
        // Set up storage event listener
        if (config.crossTab) {
            this.setupStorageListener();
        }
        
        // Call immediately if requested
        if (watcher.immediate) {
            const currentValue = this.get(key, null, { type: watcher.storageType });
            callback(currentValue, null, key);
        }
        
        // Return unwatch function
        return () => {
            this.watchers.delete(watchId);
        };
    }
    
    /**
     * Helper methods
     */
    
    getStorageKey(key) {
        return `${this.prefix}${key}`;
    }
    
    getStorage(type) {
        switch (type) {
            case 'local':
                return this.support.localStorage ? localStorage : null;
            case 'session':
                return this.support.sessionStorage ? sessionStorage : null;
            case 'memory':
                return null; // Use cache only
            default:
                return this.support.localStorage ? localStorage : null;
        }
    }
    
    prepareData(value, config) {
        const data = {
            value,
            version: this.options.version,
            timestamp: Date.now()
        };
        
        // Add expiration
        if (config.expires) {
            data.expires = typeof config.expires === 'number' ? 
                Date.now() + config.expires : config.expires;
        }
        
        let serialized = JSON.stringify(data);
        
        // Compress if enabled
        if (config.enableCompression && this.shouldCompress(serialized)) {
            serialized = this.compress(serialized);
            data.compressed = true;
        }
        
        // Encrypt if enabled
        if (config.enableEncryption && this.encryptionKey) {
            serialized = this.encrypt(serialized);
            data.encrypted = true;
        }
        
        return serialized;
    }
    
    parseData(rawData, config) {
        try {
            let data = rawData;
            
            // Decrypt if needed
            if (config.enableEncryption && this.encryptionKey) {
                data = this.decrypt(data);
            }
            
            // Decompress if needed
            if (data.startsWith('{"compressed":true')) {
                const tempData = JSON.parse(data);
                if (tempData.compressed) {
                    data = this.decompress(data);
                }
            }
            
            const parsed = JSON.parse(data);
            
            // Validate data structure
            if (config.enableValidation && !this.validateData(parsed)) {
                throw new Error('Invalid data structure');
            }
            
            return parsed;
            
        } catch (error) {
            this.log('Failed to parse data:', error, 'error');
            return null;
        }
    }
    
    storeData(key, data, type) {
        if (type === 'memory') {
            // Store in cache only
            return;
        }
        
        const storage = this.getStorage(type);
        if (storage) {
            storage.setItem(key, data);
        } else {
            throw new Error(`Storage type '${type}' not available`);
        }
    }
    
    retrieveData(key, type) {
        if (type === 'memory') {
            return null; // Use cache only
        }
        
        const storage = this.getStorage(type);
        return storage ? storage.getItem(key) : null;
    }
    
    removeData(key, type) {
        if (type === 'memory') {
            return; // Cache handled separately
        }
        
        const storage = this.getStorage(type);
        if (storage) {
            storage.removeItem(key);
        }
    }
    
    clearStorage(type) {
        const storage = this.getStorage(type);
        if (storage) {
            storage.clear();
        }
    }
    
    clearPrefixed(type) {
        const storage = this.getStorage(type);
        if (!storage) return;
        
        const keysToRemove = [];
        for (let i = 0; i < storage.length; i++) {
            const key = storage.key(i);
            if (key && key.startsWith(this.prefix)) {
                keysToRemove.push(key);
            }
        }
        
        keysToRemove.forEach(key => storage.removeItem(key));
    }
    
    updateCache(key, value, config) {
        if (!config.enableCache) return;
        
        // Check cache size limit
        if (this.cache.size >= this.options.maxCacheSize) {
            // Remove oldest entry
            const firstKey = this.cache.keys().next().value;
            this.cache.delete(firstKey);
        }
        
        this.cache.set(key, {
            value,
            timestamp: Date.now(),
            expires: config.expires ? Date.now() + config.expires : null
        });
    }
    
    isExpired(expires) {
        return expires && Date.now() > expires;
    }
    
    shouldCompress(data) {
        return data.length > 1024; // Compress if larger than 1KB
    }
    
    compress(data) {
        // Simple compression - in real implementation use LZ-string or similar
        return btoa(data);
    }
    
    decompress(data) {
        return atob(data);
    }
    
    encrypt(data) {
        // Simple XOR encryption - in real implementation use crypto-js
        if (!this.encryptionKey) return data;
        
        let result = '';
        for (let i = 0; i < data.length; i++) {
            result += String.fromCharCode(
                data.charCodeAt(i) ^ this.encryptionKey.charCodeAt(i % this.encryptionKey.length)
            );
        }
        return btoa(result);
    }
    
    decrypt(data) {
        if (!this.encryptionKey) return data;
        
        const decoded = atob(data);
        let result = '';
        for (let i = 0; i < decoded.length; i++) {
            result += String.fromCharCode(
                decoded.charCodeAt(i) ^ this.encryptionKey.charCodeAt(i % this.encryptionKey.length)
            );
        }
        return result;
    }
    
    validateData(data) {
        return data && typeof data === 'object' && 'value' in data && 'timestamp' in data;
    }
    
    getItemSize(key, value) {
        return new Blob([key + value]).size;
    }
    
    estimateQuota(type) {
        // Rough estimate - actual quota varies by browser
        if (type === 'local') {
            return 5 * 1024 * 1024; // 5MB
        } else if (type === 'session') {
            return 5 * 1024 * 1024; // 5MB
        }
        return null;
    }
    
    setupQuotaMonitoring() {
        if (!this.options.enableQuota) return;
        
        setInterval(() => {
            const usage = this.getUsage();
            if (usage && usage.usagePercent > this.options.quotaWarningPercent) {
                this.emitStorageEvent('quota-warning', null, usage);
            }
        }, 60000); // Check every minute
    }
    
    setupBackup() {
        if (!this.options.enableBackup) return;
        
        setInterval(() => {
            this.backup({ store: true });
        }, this.options.backupInterval);
    }
    
    setupCrossTabSync() {
        if (!this.options.enableSyncAcrossTabs) return;
        
        window.addEventListener('storage', (e) => {
            if (e.key && e.key.startsWith(this.prefix)) {
                const key = e.key.substring(this.prefix.length);
                this.emitStorageEvent('external-change', key, e.newValue, { oldValue: e.oldValue });
                
                // Update cache
                this.cache.delete(key);
            }
        });
    }
    
    migrateData() {
        if (!this.options.enableMigration) return;
        
        // Check for version changes and migrate if needed
        const currentVersion = this.get('__version__', null, { type: 'local' });
        if (currentVersion !== this.options.version) {
            this.performMigration(currentVersion, this.options.version);
            this.set('__version__', this.options.version, { type: 'local' });
        }
    }
    
    performMigration(oldVersion, newVersion) {
        this.log(`Migrating storage from ${oldVersion} to ${newVersion}`);
        // Implement migration logic here
    }
    
    loadCache() {
        // Pre-load frequently accessed items into cache
        const cacheKeys = this.get('__cache_keys__', [], { type: 'local' });
        cacheKeys.forEach(key => {
            this.get(key); // This will load it into cache
        });
    }
    
    backupStorage(type) {
        const storage = this.getStorage(type);
        const backup = {};
        
        if (storage) {
            for (let i = 0; i < storage.length; i++) {
                const key = storage.key(i);
                if (key && key.startsWith(this.prefix)) {
                    backup[key] = storage.getItem(key);
                }
            }
        }
        
        return backup;
    }
    
    backupCache() {
        const backup = {};
        this.cache.forEach((value, key) => {
            backup[key] = value;
        });
        return backup;
    }
    
    restoreStorage(backup, type) {
        const storage = this.getStorage(type);
        if (!storage) return;
        
        Object.entries(backup).forEach(([key, value]) => {
            storage.setItem(key, value);
        });
    }
    
    restoreCache(backup) {
        this.cache.clear();
        Object.entries(backup).forEach(([key, value]) => {
            this.cache.set(key, value);
        });
    }
    
    downloadBackup(data) {
        const blob = new Blob([data], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `gust-backup-${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }
    
    storeBackup(data) {
        this.set('__backup__', data, { type: 'local', expires: 7 * 24 * 60 * 60 * 1000 }); // 7 days
    }
    
    emitStorageEvent(action, key, value, config) {
        if (this.eventBus) {
            this.eventBus.emit('storage:change', { action, key, value, config });
            this.eventBus.emit(`storage:${action}`, { key, value, config });
        }
    }
    
    log(message, data = null, level = 'info') {
        if (!this.options.debug && level === 'debug') return;
        
        const prefix = '[StorageService]';
        
        switch (level) {
            case 'error':
                console.error(prefix, message, data);
                break;
            case 'warn':
                console.warn(prefix, message, data);
                break;
            default:
                console.log(prefix, message, data);
        }
    }
    
    /**
     * Destroy service and cleanup
     */
    destroy() {
        if (this.watchers) {
            this.watchers.clear();
        }
        
        this.cache.clear();
        
        // Remove event listeners
        window.removeEventListener('storage', this.storageListener);
    }
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = StorageService;
} else {
    window.StorageService = StorageService;
}