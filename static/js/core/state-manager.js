/**
 * GUST Bot Enhanced - Centralized State Management
 * ===============================================
 * Global application state management with reactive updates
 */

import { Config } from './config.js';
import { EventBus } from './event-bus.js';

export class StateManager {
    constructor() {
        this.state = new Map();
        this.eventBus = new EventBus();
        this.watchers = new Map();
        this.computed = new Map();
        this.initialized = false;
        
        // State change history for debugging
        this.history = [];
        this.maxHistorySize = 100;
    }

    /**
     * Initialize state manager
     */
    init() {
        if (this.initialized) return;

        // Initialize default state
        this.initializeDefaultState();
        
        // Setup computed properties
        this.setupComputedProperties();
        
        // Load persisted state
        this.loadPersistedState();
        
        this.initialized = true;
        console.log('📊 State Manager initialized');
    }

    /**
     * Initialize default application state
     */
    initializeDefaultState() {
        const defaultState = {
            // Application State
            currentRoute: Config.ROUTES.DEFAULT,
            initialized: false,
            loading: false,
            
            // Authentication State
            isAuthenticated: false,
            demoMode: true,
            tokenStatus: null,
            username: null,
            
            // System State
            websocketsAvailable: false,
            mongodbAvailable: false,
            systemStatus: 'checking',
            
            // Server Management
            managedServers: [],
            selectedServers: new Set(),
            serverFilter: '',
            
            // Console State
            consoleOutput: [],
            messageTypeFilter: 'all',
            autoScroll: true,
            connectionStatus: {},
            liveConnections: {},
            
            // Events State
            activeEvents: [],
            eventTemplates: [],
            arenaLocations: [],
            
            // Economy State
            userBalances: new Map(),
            economyStats: null,
            economyLeaderboard: [],
            
            // Gambling State
            gamblingHistory: new Map(),
            gamblingStats: new Map(),
            gamblingLeaderboard: [],
            
            // Clans State
            clans: [],
            userClans: new Map(),
            clanStats: null,
            
            // User Management State
            activeBans: [],
            userHistory: new Map(),
            userStats: null,
            
            // UI State
            sidebarCollapsed: false,
            notifications: [],
            modals: new Set(),
            loadingStates: new Map(),
            
            // Preferences
            preferences: {
                theme: 'dark',
                autoRefresh: true,
                notifications: true,
                animations: true
            }
        };

        // Set initial state
        Object.entries(defaultState).forEach(([key, value]) => {
            this.state.set(key, value);
        });
    }

    /**
     * Setup computed properties
     */
    setupComputedProperties() {
        // Active server count
        this.computed.set('activeServerCount', () => {
            const servers = this.get('managedServers', []);
            return servers.filter(server => server.isActive).length;
        });

        // Online server count
        this.computed.set('onlineServerCount', () => {
            const servers = this.get('managedServers', []);
            return servers.filter(server => server.status === 'online').length;
        });

        // Live connection count
        this.computed.set('liveConnectionCount', () => {
            const connections = this.get('connectionStatus', {});
            return Object.values(connections).filter(conn => conn.connected).length;
        });

        // Total clan members
        this.computed.set('totalClanMembers', () => {
            const clans = this.get('clans', []);
            return clans.reduce((total, clan) => total + (clan.memberCount || 0), 0);
        });

        // Filter managed servers
        this.computed.set('filteredServers', () => {
            const servers = this.get('managedServers', []);
            const filter = this.get('serverFilter', '').toLowerCase();
            
            if (!filter) return servers;
            
            return servers.filter(server => 
                server.serverName.toLowerCase().includes(filter) ||
                server.serverId.toString().includes(filter) ||
                server.serverRegion.toLowerCase().includes(filter)
            );
        });

        // Console message count by type
        this.computed.set('messageCountByType', () => {
            const output = this.get('consoleOutput', []);
            const counts = {};
            
            Config.CONSOLE.MESSAGE_TYPES.forEach(type => {
                counts[type] = type === 'all' 
                    ? output.length 
                    : output.filter(msg => msg.type === type).length;
            });
            
            return counts;
        });
    }

    /**
     * Get state value
     */
    get(key, defaultValue = undefined) {
        if (this.computed.has(key)) {
            // Return computed property
            return this.computed.get(key)();
        }
        
        return this.state.has(key) ? this.state.get(key) : defaultValue;
    }

    /**
     * Set state value
     */
    set(key, value, options = {}) {
        const { silent = false, persist = false } = options;
        const oldValue = this.state.get(key);
        
        // Check if value actually changed
        if (this.deepEqual(oldValue, value)) {
            return;
        }
        
        // Update state
        this.state.set(key, value);
        
        // Add to history
        if (Config.DEBUG.LOG_STATE_CHANGES) {
            this.addToHistory(key, oldValue, value);
        }
        
        // Persist if requested
        if (persist) {
            this.persistState(key, value);
        }
        
        // Notify watchers
        if (!silent) {
            this.notifyWatchers(key, value, oldValue);
            this.eventBus.emit('state:changed', { key, value, oldValue });
        }
        
        if (Config.DEBUG.LOG_STATE_CHANGES) {
            console.log(`📊 State changed: ${key}`, { oldValue, newValue: value });
        }
    }

    /**
     * Update state value (partial update for objects)
     */
    update(key, updater, options = {}) {
        const currentValue = this.get(key);
        
        if (typeof updater === 'function') {
            const newValue = updater(currentValue);
            this.set(key, newValue, options);
        } else if (typeof updater === 'object' && currentValue !== null && typeof currentValue === 'object') {
            const newValue = { ...currentValue, ...updater };
            this.set(key, newValue, options);
        } else {
            this.set(key, updater, options);
        }
    }

    /**
     * Delete state value
     */
    delete(key, options = {}) {
        const { silent = false } = options;
        const oldValue = this.state.get(key);
        
        if (this.state.has(key)) {
            this.state.delete(key);
            
            if (!silent) {
                this.notifyWatchers(key, undefined, oldValue);
                this.eventBus.emit('state:deleted', { key, oldValue });
            }
        }
    }

    /**
     * Watch state changes
     */
    watch(key, callback, options = {}) {
        const { immediate = false } = options;
        
        if (!this.watchers.has(key)) {
            this.watchers.set(key, new Set());
        }
        
        this.watchers.get(key).add(callback);
        
        // Call immediately if requested
        if (immediate) {
            callback(this.get(key), undefined);
        }
        
        // Return unwatch function
        return () => {
            this.unwatch(key, callback);
        };
    }

    /**
     * Stop watching state changes
     */
    unwatch(key, callback) {
        if (this.watchers.has(key)) {
            this.watchers.get(key).delete(callback);
            
            // Clean up empty watcher sets
            if (this.watchers.get(key).size === 0) {
                this.watchers.delete(key);
            }
        }
    }

    /**
     * Notify watchers of state changes
     */
    notifyWatchers(key, newValue, oldValue) {
        if (this.watchers.has(key)) {
            this.watchers.get(key).forEach(callback => {
                try {
                    callback(newValue, oldValue);
                } catch (error) {
                    console.error(`❌ Error in state watcher for ${key}:`, error);
                }
            });
        }
    }

    /**
     * Subscribe to multiple state changes
     */
    subscribe(keys, callback) {
        const unsubscribers = keys.map(key => this.watch(key, callback));
        
        return () => {
            unsubscribers.forEach(unsubscribe => unsubscribe());
        };
    }

    /**
     * Batch state updates
     */
    batch(updates, options = {}) {
        const { silent = false } = options;
        const changes = [];
        
        // Temporarily disable notifications
        const originalSilent = true;
        
        Object.entries(updates).forEach(([key, value]) => {
            const oldValue = this.get(key);
            this.set(key, value, { silent: originalSilent });
            changes.push({ key, value, oldValue });
        });
        
        // Notify all changes at once
        if (!silent) {
            changes.forEach(({ key, value, oldValue }) => {
                this.notifyWatchers(key, value, oldValue);
            });
            
            this.eventBus.emit('state:batchChanged', { changes });
        }
    }

    /**
     * Reset state to default values
     */
    reset(keys = null) {
        if (keys) {
            // Reset specific keys
            keys.forEach(key => {
                this.delete(key);
            });
        } else {
            // Reset all state
            this.state.clear();
            this.watchers.clear();
            this.initializeDefaultState();
        }
        
        this.eventBus.emit('state:reset', { keys });
    }

    /**
     * Get all state
     */
    getAll() {
        const stateObject = {};
        this.state.forEach((value, key) => {
            stateObject[key] = value;
        });
        return stateObject;
    }

    /**
     * Import state
     */
    import(stateData, options = {}) {
        const { merge = true, silent = false } = options;
        
        if (!merge) {
            this.state.clear();
        }
        
        Object.entries(stateData).forEach(([key, value]) => {
            this.set(key, value, { silent });
        });
        
        if (!silent) {
            this.eventBus.emit('state:imported', { stateData, merge });
        }
    }

    /**
     * Export state
     */
    export(keys = null) {
        if (keys) {
            const exportData = {};
            keys.forEach(key => {
                if (this.state.has(key)) {
                    exportData[key] = this.get(key);
                }
            });
            return exportData;
        }
        
        return this.getAll();
    }

    /**
     * Persist state to localStorage
     */
    persistState(key, value) {
        try {
            const persistedState = this.getPersistedState();
            persistedState[key] = value;
            localStorage.setItem(Config.STORAGE.UI_STATE, JSON.stringify(persistedState));
        } catch (error) {
            console.error('❌ Error persisting state:', error);
        }
    }

    /**
     * Load persisted state from localStorage
     */
    loadPersistedState() {
        try {
            const persistedState = this.getPersistedState();
            
            // Only load specific keys that should be persisted
            const persistKeys = ['preferences', 'sidebarCollapsed', 'messageTypeFilter', 'autoScroll'];
            
            persistKeys.forEach(key => {
                if (persistedState[key] !== undefined) {
                    this.set(key, persistedState[key], { silent: true });
                }
            });
            
        } catch (error) {
            console.error('❌ Error loading persisted state:', error);
        }
    }

    /**
     * Get persisted state object
     */
    getPersistedState() {
        try {
            const stored = localStorage.getItem(Config.STORAGE.UI_STATE);
            return stored ? JSON.parse(stored) : {};
        } catch (error) {
            return {};
        }
    }

    /**
     * Clear persisted state
     */
    clearPersistedState() {
        try {
            localStorage.removeItem(Config.STORAGE.UI_STATE);
        } catch (error) {
            console.error('❌ Error clearing persisted state:', error);
        }
    }

    /**
     * Add state change to history
     */
    addToHistory(key, oldValue, newValue) {
        this.history.push({
            timestamp: Date.now(),
            key,
            oldValue,
            newValue
        });
        
        // Limit history size
        if (this.history.length > this.maxHistorySize) {
            this.history.shift();
        }
    }

    /**
     * Get state change history
     */
    getHistory(key = null) {
        if (key) {
            return this.history.filter(entry => entry.key === key);
        }
        return [...this.history];
    }

    /**
     * Clear state change history
     */
    clearHistory() {
        this.history = [];
    }

    /**
     * Deep equality check
     */
    deepEqual(a, b) {
        if (a === b) return true;
        
        if (a instanceof Date && b instanceof Date) {
            return a.getTime() === b.getTime();
        }
        
        if (!a || !b || (typeof a !== 'object' && typeof b !== 'object')) {
            return a === b;
        }
        
        if (a === null || a === undefined || b === null || b === undefined) {
            return false;
        }
        
        if (a.prototype !== b.prototype) return false;
        
        let keys = Object.keys(a);
        if (keys.length !== Object.keys(b).length) {
            return false;
        }
        
        return keys.every(k => this.deepEqual(a[k], b[k]));
    }

    /**
     * Create a reactive proxy for an object
     */
    reactive(target) {
        return new Proxy(target, {
            get: (obj, prop) => {
                return obj[prop];
            },
            set: (obj, prop, value) => {
                const oldValue = obj[prop];
                obj[prop] = value;
                this.eventBus.emit('reactive:changed', { target: obj, prop, value, oldValue });
                return true;
            }
        });
    }

    /**
     * Get state statistics
     */
    getStats() {
        return {
            stateCount: this.state.size,
            watcherCount: Array.from(this.watchers.values()).reduce((total, set) => total + set.size, 0),
            computedCount: this.computed.size,
            historyCount: this.history.length
        };
    }

    /**
     * Debug information
     */
    debug() {
        console.log('📊 State Manager Debug Info:', {
            state: this.getAll(),
            watchers: Object.fromEntries(
                Array.from(this.watchers.entries()).map(([key, set]) => [key, set.size])
            ),
            computed: Array.from(this.computed.keys()),
            history: this.history.slice(-10), // Last 10 changes
            stats: this.getStats()
        });
    }

    /**
     * Cleanup state manager
     */
    cleanup() {
        this.state.clear();
        this.watchers.clear();
        this.computed.clear();
        this.history = [];
        this.eventBus.cleanup();
        console.log('📊 State Manager cleaned up');
    }
}