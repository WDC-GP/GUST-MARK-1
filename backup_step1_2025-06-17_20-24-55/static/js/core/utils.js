/**
 * GUST Bot Enhanced - Shared Utility Functions
 * ===========================================
 * Common utility functions used across the application
 */

import { Config } from './config.js';

export class Utils {
    constructor() {
        this.cache = new Map();
        this.timers = new Map();
    }

    // ===========================================
    // STRING UTILITIES
    // ===========================================

    /**
     * Escape HTML characters
     */
    escapeHtml(text) {
        if (!text) return '';
        
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Strip HTML tags
     */
    stripHtml(html) {
        const div = document.createElement('div');
        div.innerHTML = html;
        return div.textContent || div.innerText || '';
    }

    /**
     * Truncate text with ellipsis
     */
    truncate(text, length = 100, suffix = '...') {
        if (!text || text.length <= length) return text;
        return text.substring(0, length) + suffix;
    }

    /**
     * Capitalize first letter
     */
    capitalize(text) {
        if (!text) return '';
        return text.charAt(0).toUpperCase() + text.slice(1).toLowerCase();
    }

    /**
     * Convert to title case
     */
    titleCase(text) {
        if (!text) return '';
        return text.split(' ')
            .map(word => this.capitalize(word))
            .join(' ');
    }

    /**
     * Generate random string
     */
    randomString(length = 8, charset = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789') {
        let result = '';
        for (let i = 0; i < length; i++) {
            result += charset.charAt(Math.floor(Math.random() * charset.length));
        }
        return result;
    }

    /**
     * Format file size
     */
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    // ===========================================
    // NUMBER UTILITIES
    // ===========================================

    /**
     * Safe integer conversion
     */
    safeInt(value, defaultValue = 0) {
        try {
            const num = parseInt(value, 10);
            return isNaN(num) ? defaultValue : num;
        } catch {
            return defaultValue;
        }
    }

    /**
     * Safe float conversion
     */
    safeFloat(value, defaultValue = 0.0) {
        try {
            const num = parseFloat(value);
            return isNaN(num) ? defaultValue : num;
        } catch {
            return defaultValue;
        }
    }

    /**
     * Format number with commas
     */
    formatNumber(num) {
        return new Intl.NumberFormat().format(num);
    }

    /**
     * Format currency
     */
    formatCurrency(amount, currency = 'USD') {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: currency
        }).format(amount);
    }

    /**
     * Format percentage
     */
    formatPercentage(value, decimals = 1) {
        return `${(value * 100).toFixed(decimals)}%`;
    }

    /**
     * Clamp number between min and max
     */
    clamp(value, min, max) {
        return Math.min(Math.max(value, min), max);
    }

    /**
     * Generate random number between min and max
     */
    randomInt(min, max) {
        return Math.floor(Math.random() * (max - min + 1)) + min;
    }

    // ===========================================
    // DATE/TIME UTILITIES
    // ===========================================

    /**
     * Format timestamp to readable string
     */
    formatTime(timestamp) {
        if (!timestamp) return '';
        
        try {
            const date = new Date(timestamp);
            return date.toLocaleTimeString();
        } catch {
            return '';
        }
    }

    /**
     * Format date to readable string
     */
    formatDate(timestamp, options = {}) {
        if (!timestamp) return '';
        
        try {
            const date = new Date(timestamp);
            return date.toLocaleDateString('en-US', options);
        } catch {
            return '';
        }
    }

    /**
     * Format relative time (e.g., "5 minutes ago")
     */
    formatRelativeTime(timestamp) {
        if (!timestamp) return '';
        
        try {
            const now = new Date();
            const date = new Date(timestamp);
            const diffMs = now - date;
            const diffSeconds = Math.floor(diffMs / 1000);
            const diffMinutes = Math.floor(diffSeconds / 60);
            const diffHours = Math.floor(diffMinutes / 60);
            const diffDays = Math.floor(diffHours / 24);

            if (diffSeconds < 60) return 'just now';
            if (diffMinutes < 60) return `${diffMinutes} minute${diffMinutes !== 1 ? 's' : ''} ago`;
            if (diffHours < 24) return `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`;
            if (diffDays < 7) return `${diffDays} day${diffDays !== 1 ? 's' : ''} ago`;
            
            return this.formatDate(timestamp);
        } catch {
            return '';
        }
    }

    /**
     * Get current timestamp
     */
    now() {
        return new Date().toISOString();
    }

    /**
     * Sleep/delay function
     */
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    // ===========================================
    // VALIDATION UTILITIES
    // ===========================================

    /**
     * Validate server ID
     */
    validateServerId(serverId) {
        try {
            // Handle test server IDs that might have suffixes
            if (typeof serverId === 'string' && serverId.includes('_test')) {
                const cleanId = parseInt(serverId.split('_')[0], 10);
                return {
                    isValid: !isNaN(cleanId) && cleanId >= Config.VALIDATION.SERVER_ID.MIN && cleanId <= Config.VALIDATION.SERVER_ID.MAX,
                    cleanId: cleanId
                };
            } else {
                const cleanId = parseInt(serverId, 10);
                return {
                    isValid: !isNaN(cleanId) && cleanId >= Config.VALIDATION.SERVER_ID.MIN && cleanId <= Config.VALIDATION.SERVER_ID.MAX,
                    cleanId: cleanId
                };
            }
        } catch {
            return { isValid: false, cleanId: null };
        }
    }

    /**
     * Validate region code
     */
    validateRegion(region) {
        const validRegions = Config.REGIONS.map(r => r.code);
        return validRegions.includes(region?.toUpperCase());
    }

    /**
     * Validate email address
     */
    validateEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    /**
     * Validate required fields
     */
    validateRequired(data, requiredFields) {
        const missing = [];
        
        requiredFields.forEach(field => {
            if (!data[field] || (typeof data[field] === 'string' && data[field].trim() === '')) {
                missing.push(field);
            }
        });
        
        return {
            isValid: missing.length === 0,
            missing: missing
        };
    }

    // ===========================================
    // CONSOLE/MESSAGE UTILITIES
    // ===========================================

    /**
     * Classify console message type
     */
    classifyMessage(message) {
        if (!message) return 'system';
        
        const messageLower = message.toLowerCase();
        
        const patterns = {
            save: ['[save]', 'saving', 'saved', 'save to', 'beginning save'],
            chat: ['[chat]', 'global.say', 'player chat', 'say '],
            auth: ['vip', 'admin', 'moderator', 'owner', 'auth'],
            kill: ['[kill]', 'killed', 'died', 'death', 'suicide'],
            error: ['error', 'exception', 'failed', 'fail', 'crash'],
            warning: ['warning', 'warn', 'alert'],
            command: ['executing console', 'command', 'executed'],
            player: ['player', 'connected', 'disconnected', 'joined', 'left'],
            server: ['server', 'startup', 'shutdown', 'restart']
        };
        
        for (const [type, typePatterns] of Object.entries(patterns)) {
            if (typePatterns.some(pattern => messageLower.includes(pattern))) {
                return type;
            }
        }
        
        return 'system';
    }

    /**
     * Get type icon for message
     */
    getTypeIcon(messageType) {
        return Config.CONSOLE.TYPE_ICONS[messageType] || '📋';
    }

    /**
     * Format console command
     */
    formatCommand(command) {
        if (!command) return '';
        
        command = command.trim();
        
        if (command.startsWith('say ')) {
            return `global.say "${command.substring(4)}"`;
        } else if (command.startsWith('global.')) {
            return command;
        } else {
            return command;
        }
    }

    // ===========================================
    // STATUS/UI UTILITIES
    // ===========================================

    /**
     * Get status class for server status
     */
    getStatusClass(status) {
        return Config.STATUS_CLASSES[status] || Config.STATUS_CLASSES.unknown;
    }

    /**
     * Get status text with emoji
     */
    getStatusText(status) {
        return Config.STATUS_TEXT[status] || Config.STATUS_TEXT.unknown;
    }

    /**
     * Get server region flag
     */
    getRegionFlag(region) {
        const regionData = Config.REGIONS.find(r => r.code === region?.toUpperCase());
        return regionData ? regionData.flag : '🌍';
    }

    /**
     * Generate unique ID
     */
    generateId(prefix = '') {
        const timestamp = Date.now().toString(36);
        const random = Math.random().toString(36).substring(2);
        return prefix + timestamp + random;
    }

    // ===========================================
    // ARRAY/OBJECT UTILITIES
    // ===========================================

    /**
     * Deep clone object
     */
    deepClone(obj) {
        if (obj === null || typeof obj !== 'object') return obj;
        if (obj instanceof Date) return new Date(obj.getTime());
        if (obj instanceof Array) return obj.map(item => this.deepClone(item));
        if (typeof obj === 'object') {
            const cloned = {};
            Object.keys(obj).forEach(key => {
                cloned[key] = this.deepClone(obj[key]);
            });
            return cloned;
        }
        return obj;
    }

    /**
     * Merge objects deeply
     */
    deepMerge(target, source) {
        const result = { ...target };
        
        for (const key in source) {
            if (source[key] instanceof Object && target[key] instanceof Object) {
                result[key] = this.deepMerge(target[key], source[key]);
            } else {
                result[key] = source[key];
            }
        }
        
        return result;
    }

    /**
     * Group array by key
     */
    groupBy(array, key) {
        return array.reduce((groups, item) => {
            const groupKey = typeof key === 'function' ? key(item) : item[key];
            if (!groups[groupKey]) {
                groups[groupKey] = [];
            }
            groups[groupKey].push(item);
            return groups;
        }, {});
    }

    /**
     * Remove duplicates from array
     */
    unique(array, key = null) {
        if (!key) {
            return [...new Set(array)];
        }
        
        const seen = new Set();
        return array.filter(item => {
            const value = typeof key === 'function' ? key(item) : item[key];
            if (seen.has(value)) {
                return false;
            }
            seen.add(value);
            return true;
        });
    }

    /**
     * Sort array by multiple keys
     */
    sortBy(array, ...keys) {
        return array.sort((a, b) => {
            for (const key of keys) {
                const aVal = typeof key === 'function' ? key(a) : a[key];
                const bVal = typeof key === 'function' ? key(b) : b[key];
                
                if (aVal < bVal) return -1;
                if (aVal > bVal) return 1;
            }
            return 0;
        });
    }

    // ===========================================
    // CACHING UTILITIES
    // ===========================================

    /**
     * Cache a value with TTL
     */
    setCache(key, value, ttlMs = 300000) { // 5 minutes default
        this.cache.set(key, {
            value,
            expires: Date.now() + ttlMs
        });
    }

    /**
     * Get cached value
     */
    getCache(key) {
        const cached = this.cache.get(key);
        if (!cached) return null;
        
        if (Date.now() > cached.expires) {
            this.cache.delete(key);
            return null;
        }
        
        return cached.value;
    }

    /**
     * Clear cache
     */
    clearCache(key = null) {
        if (key) {
            this.cache.delete(key);
        } else {
            this.cache.clear();
        }
    }

    // ===========================================
    // PERFORMANCE UTILITIES
    // ===========================================

    /**
     * Debounce function calls
     */
    debounce(func, delay = Config.PERFORMANCE.DEBOUNCE_DELAY) {
        const key = func.name || 'anonymous';
        
        return (...args) => {
            if (this.timers.has(key)) {
                clearTimeout(this.timers.get(key));
            }
            
            this.timers.set(key, setTimeout(() => {
                func.apply(this, args);
                this.timers.delete(key);
            }, delay));
        };
    }

    /**
     * Throttle function calls
     */
    throttle(func, delay = Config.PERFORMANCE.THROTTLE_DELAY) {
        const key = func.name || 'anonymous';
        let lastCall = 0;
        
        return (...args) => {
            const now = Date.now();
            if (now - lastCall >= delay) {
                lastCall = now;
                return func.apply(this, args);
            }
        };
    }

    /**
     * Measure execution time
     */
    async measure(func, label = 'operation') {
        const start = performance.now();
        const result = await func();
        const end = performance.now();
        
        console.log(`⏱️ ${label} took ${(end - start).toFixed(2)}ms`);
        return result;
    }

    // ===========================================
    // DOM UTILITIES
    // ===========================================

    /**
     * Query selector with error handling
     */
    $(selector, context = document) {
        try {
            return context.querySelector(selector);
        } catch (error) {
            console.error(`❌ Invalid selector: ${selector}`, error);
            return null;
        }
    }

    /**
     * Query all with error handling
     */
    $$(selector, context = document) {
        try {
            return Array.from(context.querySelectorAll(selector));
        } catch (error) {
            console.error(`❌ Invalid selector: ${selector}`, error);
            return [];
        }
    }

    /**
     * Add event listener with cleanup
     */
    addEventListener(element, event, handler, options = {}) {
        if (!element) return null;
        
        element.addEventListener(event, handler, options);
        
        // Return cleanup function
        return () => {
            element.removeEventListener(event, handler, options);
        };
    }

    /**
     * Create element with attributes
     */
    createElement(tag, attributes = {}, textContent = null) {
        const element = document.createElement(tag);
        
        Object.entries(attributes).forEach(([key, value]) => {
            if (key === 'className') {
                element.className = value;
            } else if (key === 'style' && typeof value === 'object') {
                Object.assign(element.style, value);
            } else {
                element.setAttribute(key, value);
            }
        });
        
        if (textContent) {
            element.textContent = textContent;
        }
        
        return element;
    }

    // ===========================================
    // STORAGE UTILITIES
    // ===========================================

    /**
     * Safe localStorage operations
     */
    setStorage(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
            return true;
        } catch (error) {
            console.error('❌ localStorage write error:', error);
            return false;
        }
    }

    getStorage(key, defaultValue = null) {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : defaultValue;
        } catch (error) {
            console.error('❌ localStorage read error:', error);
            return defaultValue;
        }
    }

    removeStorage(key) {
        try {
            localStorage.removeItem(key);
            return true;
        } catch (error) {
            console.error('❌ localStorage remove error:', error);
            return false;
        }
    }

    // ===========================================
    // ERROR HANDLING UTILITIES
    // ===========================================

    /**
     * Safe function execution with error handling
     */
    async safeExecute(func, fallback = null, context = null) {
        try {
            return await (context ? func.call(context) : func());
        } catch (error) {
            console.error('❌ Safe execution error:', error);
            return fallback;
        }
    }

    /**
     * Retry function with exponential backoff
     */
    async retry(func, maxAttempts = 3, delay = 1000) {
        for (let attempt = 1; attempt <= maxAttempts; attempt++) {
            try {
                return await func();
            } catch (error) {
                if (attempt === maxAttempts) {
                    throw error;
                }
                
                const backoffDelay = delay * Math.pow(2, attempt - 1);
                await this.delay(backoffDelay);
            }
        }
    }

    // ===========================================
    // CLEANUP
    // ===========================================

    /**
     * Cleanup utilities
     */
    cleanup() {
        this.cache.clear();
        this.timers.forEach(timer => clearTimeout(timer));
        this.timers.clear();
        console.log('🧹 Utils cleaned up');
    }
}