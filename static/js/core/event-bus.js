/**
 * GUST Bot Enhanced - Event Bus
 * =============================
 * Component communication and event management system
 */

import { Config } from './config.js';

export class EventBus {
    constructor() {
        this.events = new Map();
        this.onceEvents = new Set();
        this.middleware = [];
        this.history = [];
        this.maxHistorySize = 100;
        this.paused = false;
        this.eventCount = 0;
        
        // Performance monitoring
        this.metrics = {
            totalEvents: 0,
            totalListeners: 0,
            averageListeners: 0,
            slowEvents: []
        };
    }

    /**
     * Subscribe to an event
     */
    on(event, callback, options = {}) {
        if (typeof callback !== 'function') {
            throw new Error('Callback must be a function');
        }

        const { 
            priority = 0, 
            once = false, 
            context = null,
            debounce = false,
            throttle = false 
        } = options;

        // Create wrapped callback with options
        const wrappedCallback = this.wrapCallback(callback, {
            priority,
            once,
            context,
            debounce: debounce ? Config.PERFORMANCE.DEBOUNCE_DELAY : false,
            throttle: throttle ? Config.PERFORMANCE.THROTTLE_DELAY : false
        });

        // Initialize event listeners array if it doesn't exist
        if (!this.events.has(event)) {
            this.events.set(event, []);
        }

        // Add listener
        const listener = {
            callback: wrappedCallback,
            originalCallback: callback,
            priority,
            once,
            context,
            id: this.generateListenerId()
        };

        this.events.get(event).push(listener);

        // Sort by priority (higher priority first)
        this.events.get(event).sort((a, b) => b.priority - a.priority);

        // Track for once events
        if (once) {
            this.onceEvents.add(listener.id);
        }

        this.updateMetrics();

        if (Config.DEBUG.LOG_EVENTS) {
            console.log(`📡 Event listener added: ${event}`, { priority, once, context });
        }

        // Return unsubscribe function
        return () => this.off(event, callback);
    }

    /**
     * Subscribe to an event (one-time)
     */
    once(event, callback, options = {}) {
        return this.on(event, callback, { ...options, once: true });
    }

    /**
     * Unsubscribe from an event
     */
    off(event, callback = null) {
        if (!this.events.has(event)) {
            return false;
        }

        const listeners = this.events.get(event);

        if (callback === null) {
            // Remove all listeners for this event
            const removedCount = listeners.length;
            this.events.delete(event);
            this.updateMetrics();
            
            if (Config.DEBUG.LOG_EVENTS) {
                console.log(`📡 All event listeners removed: ${event} (${removedCount})`);
            }
            
            return true;
        }

        // Remove specific listener
        const initialLength = listeners.length;
        const filteredListeners = listeners.filter(listener => 
            listener.originalCallback !== callback
        );

        if (filteredListeners.length === 0) {
            this.events.delete(event);
        } else {
            this.events.set(event, filteredListeners);
        }

        const removed = initialLength !== (filteredListeners.length || 0);
        
        if (removed) {
            this.updateMetrics();
            
            if (Config.DEBUG.LOG_EVENTS) {
                console.log(`📡 Event listener removed: ${event}`);
            }
        }

        return removed;
    }

    /**
     * Emit an event
     */
    async emit(event, data = null, options = {}) {
        if (this.paused) {
            if (Config.DEBUG.LOG_EVENTS) {
                console.log(`📡 Event paused: ${event}`);
            }
            return false;
        }

        const { 
            async = false, 
            timeout = 5000,
            stopOnError = false 
        } = options;

        this.eventCount++;
        this.metrics.totalEvents++;

        // Add to history
        this.addToHistory(event, data);

        // Apply middleware
        const processedData = await this.applyMiddleware(event, data);

        if (!this.events.has(event)) {
            if (Config.DEBUG.LOG_EVENTS) {
                console.log(`📡 No listeners for event: ${event}`);
            }
            return true;
        }

        const listeners = [...this.events.get(event)]; // Copy to avoid modification during iteration
        const results = [];
        const startTime = performance.now();

        if (Config.DEBUG.LOG_EVENTS) {
            console.log(`📡 Emitting event: ${event}`, { data: processedData, listeners: listeners.length });
        }

        try {
            if (async) {
                // Execute all listeners in parallel
                const promises = listeners.map(listener => 
                    this.executeListener(listener, event, processedData, { timeout })
                );
                
                results.push(...await Promise.allSettled(promises));
            } else {
                // Execute listeners sequentially
                for (const listener of listeners) {
                    try {
                        const result = await this.executeListener(listener, event, processedData, { timeout });
                        results.push({ status: 'fulfilled', value: result });
                        
                        // Stop on error if requested
                        if (stopOnError && result instanceof Error) {
                            break;
                        }
                    } catch (error) {
                        results.push({ status: 'rejected', reason: error });
                        
                        if (stopOnError) {
                            break;
                        }
                    }
                }
            }

            // Clean up once listeners
            this.cleanupOnceListeners(event);

            // Track performance
            const duration = performance.now() - startTime;
            if (duration > 100) { // Log slow events
                this.metrics.slowEvents.push({ event, duration, timestamp: Date.now() });
                console.warn(`⚠️ Slow event: ${event} took ${duration.toFixed(2)}ms`);
            }

            return results;

        } catch (error) {
            console.error(`❌ Error emitting event ${event}:`, error);
            return false;
        }
    }

    /**
     * Execute a single listener
     */
    async executeListener(listener, event, data, options = {}) {
        const { timeout = 5000 } = options;

        try {
            const promise = listener.context 
                ? listener.callback.call(listener.context, data, event)
                : listener.callback(data, event);

            // Add timeout for async operations
            if (promise instanceof Promise) {
                return await Promise.race([
                    promise,
                    new Promise((_, reject) => 
                        setTimeout(() => reject(new Error(`Listener timeout for ${event}`)), timeout)
                    )
                ]);
            }

            return promise;

        } catch (error) {
            console.error(`❌ Error in event listener for ${event}:`, error);
            throw error;
        }
    }

    /**
     * Wrap callback with additional functionality
     */
    wrapCallback(callback, options) {
        let { debounce, throttle, once, context } = options;
        let wrappedCallback = callback;

        // Apply debouncing
        if (debounce) {
            wrappedCallback = this.debounce(wrappedCallback, debounce);
        }

        // Apply throttling
        if (throttle) {
            wrappedCallback = this.throttle(wrappedCallback, throttle);
        }

        return wrappedCallback;
    }

    /**
     * Debounce function
     */
    debounce(func, delay) {
        let timeoutId;
        return function (...args) {
            clearTimeout(timeoutId);
            timeoutId = setTimeout(() => func.apply(this, args), delay);
        };
    }

    /**
     * Throttle function
     */
    throttle(func, delay) {
        let lastCall = 0;
        return function (...args) {
            const now = Date.now();
            if (now - lastCall >= delay) {
                lastCall = now;
                return func.apply(this, args);
            }
        };
    }

    /**
     * Add middleware
     */
    use(middleware) {
        if (typeof middleware !== 'function') {
            throw new Error('Middleware must be a function');
        }

        this.middleware.push(middleware);
        
        if (Config.DEBUG.LOG_EVENTS) {
            console.log('📡 Middleware added');
        }
    }

    /**
     * Apply middleware to event data
     */
    async applyMiddleware(event, data) {
        let processedData = data;

        for (const middleware of this.middleware) {
            try {
                const result = await middleware(event, processedData);
                if (result !== undefined) {
                    processedData = result;
                }
            } catch (error) {
                console.error('❌ Middleware error:', error);
            }
        }

        return processedData;
    }

    /**
     * Clean up once listeners
     */
    cleanupOnceListeners(event) {
        if (!this.events.has(event)) return;

        const listeners = this.events.get(event);
        const filtered = listeners.filter(listener => {
            if (listener.once) {
                this.onceEvents.delete(listener.id);
                return false;
            }
            return true;
        });

        if (filtered.length === 0) {
            this.events.delete(event);
        } else {
            this.events.set(event, filtered);
        }

        this.updateMetrics();
    }

    /**
     * Pause event emission
     */
    pause() {
        this.paused = true;
        console.log('📡 Event bus paused');
    }

    /**
     * Resume event emission
     */
    resume() {
        this.paused = false;
        console.log('📡 Event bus resumed');
    }

    /**
     * Check if event bus is paused
     */
    isPaused() {
        return this.paused;
    }

    /**
     * Get all event names
     */
    getEvents() {
        return Array.from(this.events.keys());
    }

    /**
     * Get listener count for an event
     */
    getListenerCount(event) {
        return this.events.has(event) ? this.events.get(event).length : 0;
    }

    /**
     * Get total listener count
     */
    getTotalListenerCount() {
        return Array.from(this.events.values()).reduce((total, listeners) => total + listeners.length, 0);
    }

    /**
     * Check if event has listeners
     */
    hasListeners(event) {
        return this.events.has(event) && this.events.get(event).length > 0;
    }

    /**
     * Clear all listeners for an event
     */
    clear(event = null) {
        if (event) {
            this.events.delete(event);
        } else {
            this.events.clear();
            this.onceEvents.clear();
        }

        this.updateMetrics();
        
        const target = event || 'all events';
        console.log(`📡 Cleared listeners for: ${target}`);
    }

    /**
     * Add event to history
     */
    addToHistory(event, data) {
        this.history.push({
            event,
            data,
            timestamp: Date.now(),
            id: this.eventCount
        });

        // Limit history size
        if (this.history.length > this.maxHistorySize) {
            this.history.shift();
        }
    }

    /**
     * Get event history
     */
    getHistory(event = null, limit = null) {
        let history = event 
            ? this.history.filter(entry => entry.event === event)
            : [...this.history];

        if (limit) {
            history = history.slice(-limit);
        }

        return history;
    }

    /**
     * Clear event history
     */
    clearHistory() {
        this.history = [];
        console.log('📡 Event history cleared');
    }

    /**
     * Generate unique listener ID
     */
    generateListenerId() {
        return `listener_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    /**
     * Update metrics
     */
    updateMetrics() {
        this.metrics.totalListeners = this.getTotalListenerCount();
        this.metrics.averageListeners = this.events.size > 0 
            ? this.metrics.totalListeners / this.events.size 
            : 0;
    }

    /**
     * Get performance metrics
     */
    getMetrics() {
        // Clean old slow events (older than 1 minute)
        const oneMinuteAgo = Date.now() - 60000;
        this.metrics.slowEvents = this.metrics.slowEvents.filter(
            event => event.timestamp > oneMinuteAgo
        );

        return {
            ...this.metrics,
            eventCount: this.eventCount,
            activeEvents: this.events.size,
            historySize: this.history.length,
            isPaused: this.paused
        };
    }

    /**
     * Create a namespaced event bus
     */
    namespace(name) {
        return {
            on: (event, callback, options) => this.on(`${name}:${event}`, callback, options),
            once: (event, callback, options) => this.once(`${name}:${event}`, callback, options),
            off: (event, callback) => this.off(`${name}:${event}`, callback),
            emit: (event, data, options) => this.emit(`${name}:${event}`, data, options),
            clear: (event) => this.clear(event ? `${name}:${event}` : null)
        };
    }

    /**
     * Debug information
     */
    debug() {
        console.log('📡 Event Bus Debug Info:', {
            events: Object.fromEntries(
                Array.from(this.events.entries()).map(([event, listeners]) => [
                    event,
                    listeners.map(l => ({
                        priority: l.priority,
                        once: l.once,
                        context: l.context?.constructor?.name || null
                    }))
                ])
            ),
            metrics: this.getMetrics(),
            history: this.history.slice(-10),
            middleware: this.middleware.length,
            paused: this.paused
        });
    }

    /**
     * Cleanup event bus
     */
    cleanup() {
        this.events.clear();
        this.onceEvents.clear();
        this.middleware = [];
        this.history = [];
        this.paused = false;
        this.eventCount = 0;
        this.metrics = {
            totalEvents: 0,
            totalListeners: 0,
            averageListeners: 0,
            slowEvents: []
        };
        
        console.log('📡 Event bus cleaned up');
    }
}