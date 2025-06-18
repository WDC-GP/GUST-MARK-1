/**
 * GUST Bot Enhanced - WebSocket Service
 * ===================================
 * Manages WebSocket connections for live console monitoring
 */

class WebSocketService {
    constructor(options = {}) {
        this.options = { ...this.defaultOptions, ...options };
        this.connections = new Map();
        this.eventBus = options.eventBus || window.App?.eventBus || window.EventBus;
        this.api = options.api || window.App?.api;
        this.messageHandlers = new Map();
        this.reconnectTimeouts = new Map();
        this.connectionStates = new Map();
        
        this.init();
    }
    
    get defaultOptions() {
        return {
            reconnectDelay: 3000,
            maxReconnectAttempts: 5,
            pingInterval: 30000,
            connectionTimeout: 15000,
            messageBufferSize: 1000,
            autoReconnect: true,
            debug: false
        };
    }
    
    init() {
        this.bindEvents();
        this.log('WebSocket service initialized');
    }
    
    bindEvents() {
        if (this.eventBus) {
            this.eventBus.on('server:added', (data) => this.handleServerAdded(data));
            this.eventBus.on('server:deleted', (data) => this.handleServerDeleted(data));
            this.eventBus.on('console:connect', (data) => this.connect(data.serverId, data.region));
            this.eventBus.on('console:disconnect', (data) => this.disconnect(data.serverId));
        }
        
        // Handle page visibility changes
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.pauseConnections();
            } else {
                this.resumeConnections();
            }
        });
        
        // Handle page unload
        window.addEventListener('beforeunload', () => {
            this.disconnectAll();
        });
    }
    
    /**
     * Connect to live console for a server
     * @param {string} serverId - Server ID
     * @param {string} region - Server region
     * @param {Object} options - Connection options
     */
    async connect(serverId, region = 'US', options = {}) {
        const connectionKey = this.getConnectionKey(serverId);
        
        if (this.connections.has(connectionKey)) {
            this.log(`Already connected to server ${serverId}`);
            return this.connections.get(connectionKey);
        }
        
        try {
            this.log(`Connecting to server ${serverId} (${region})`);
            
            // Get authentication token
            const token = await this.getAuthToken();
            if (!token) {
                throw new Error('No authentication token available');
            }
            
            // Create connection
            const connection = await this.createConnection(serverId, region, token, options);
            
            // Store connection
            this.connections.set(connectionKey, connection);
            this.connectionStates.set(connectionKey, {
                serverId,
                region,
                connected: true,
                reconnectAttempts: 0,
                lastConnected: Date.now(),
                messageCount: 0
            });
            
            // Emit connected event
            this.emitEvent('websocket:connected', { serverId, region });
            
            this.log(`Connected to server ${serverId}`);
            return connection;
            
        } catch (error) {
            this.log(`Failed to connect to server ${serverId}: ${error.message}`, 'error');
            this.emitEvent('websocket:error', { serverId, error: error.message });
            throw error;
        }
    }
    
    /**
     * Create WebSocket connection to G-Portal
     */
    async createConnection(serverId, region, token, options = {}) {
        return new Promise((resolve, reject) => {
            const connectionKey = this.getConnectionKey(serverId);
            let ws;
            let isConnected = false;
            let subscribed = false;
            
            try {
                // Create WebSocket connection
                ws = new WebSocket('wss://www.g-portal.com/ngpapi/', ['graphql-ws']);
                
                // Connection timeout
                const timeoutId = setTimeout(() => {
                    if (!isConnected) {
                        ws.close();
                        reject(new Error('Connection timeout'));
                    }
                }, this.options.connectionTimeout);
                
                ws.onopen = () => {
                    this.log(`WebSocket opened for server ${serverId}`);
                    
                    // Send connection init
                    const initMessage = {
                        type: 'connection_init',
                        payload: {
                            authorization: `Bearer ${token}`
                        }
                    };
                    
                    ws.send(JSON.stringify(initMessage));
                };
                
                ws.onmessage = (event) => {
                    try {
                        const data = JSON.parse(event.data);
                        
                        if (data.type === 'connection_ack' && !isConnected) {
                            clearTimeout(timeoutId);
                            isConnected = true;
                            
                            // Subscribe to console messages
                            this.subscribeToConsole(ws, serverId, region)
                                .then(() => {
                                    subscribed = true;
                                    resolve(ws);
                                })
                                .catch(reject);
                                
                        } else if (data.type === 'data' && subscribed) {
                            this.handleConsoleMessage(serverId, data);
                            
                        } else if (data.type === 'error') {
                            this.log(`WebSocket error for server ${serverId}:`, data.payload, 'error');
                            this.emitEvent('websocket:error', { serverId, error: data.payload });
                        }
                        
                    } catch (error) {
                        this.log(`Error parsing message from server ${serverId}:`, error, 'error');
                    }
                };
                
                ws.onclose = (event) => {
                    this.log(`WebSocket closed for server ${serverId}:`, event.code, event.reason);
                    this.handleConnectionClosed(serverId, event);
                };
                
                ws.onerror = (error) => {
                    this.log(`WebSocket error for server ${serverId}:`, error, 'error');
                    if (!isConnected) {
                        clearTimeout(timeoutId);
                        reject(new Error('WebSocket connection failed'));
                    }
                };
                
            } catch (error) {
                reject(error);
            }
        });
    }
    
    /**
     * Subscribe to console messages for a server
     */
    async subscribeToConsole(ws, serverId, region) {
        const subscriptionMessage = {
            id: `console_stream_${serverId}`,
            type: 'start',
            payload: {
                variables: {
                    sid: parseInt(serverId),
                    region: region.toUpperCase()
                },
                extensions: {},
                operationName: 'consoleMessages',
                query: `
                    subscription consoleMessages($sid: Int!, $region: REGION!) {
                        consoleMessages(rsid: {id: $sid, region: $region}) {
                            stream
                            channel
                            message
                            __typename
                        }
                    }
                `
            }
        };
        
        ws.send(JSON.stringify(subscriptionMessage));
        this.log(`Subscribed to console messages for server ${serverId}`);
    }
    
    /**
     * Handle incoming console message
     */
    handleConsoleMessage(serverId, data) {
        const connectionKey = this.getConnectionKey(serverId);
        const state = this.connectionStates.get(connectionKey);
        
        if (!state) return;
        
        try {
            const payload = data.payload?.data?.consoleMessages;
            if (!payload?.message) return;
            
            // Create structured message
            const message = {
                timestamp: new Date().toISOString(),
                serverId: serverId,
                message: payload.message,
                stream: payload.stream || '',
                channel: payload.channel || '',
                type: this.classifyMessage(payload.message),
                source: 'websocket_live'
            };
            
            // Update message count
            state.messageCount++;
            
            // Store message in buffer
            this.storeMessage(serverId, message);
            
            // Emit message event
            this.emitEvent('console:message', message);
            this.emitEvent(`console:message:${serverId}`, message);
            
            // Call registered handlers
            this.callMessageHandlers(serverId, message);
            
            this.log(`Console message from server ${serverId}: ${payload.message.substring(0, 100)}...`);
            
        } catch (error) {
            this.log(`Error processing console message from server ${serverId}:`, error, 'error');
        }
    }
    
    /**
     * Classify message type based on content
     */
    classifyMessage(message) {
        if (!message) return 'system';
        
        const msgLower = message.toLowerCase();
        
        if (msgLower.includes('[save]') || msgLower.includes('saving')) return 'save';
        if (msgLower.includes('[chat]') || msgLower.includes('say ')) return 'chat';
        if (msgLower.includes('vip') || msgLower.includes('admin')) return 'auth';
        if (msgLower.includes('killed') || msgLower.includes('died')) return 'kill';
        if (msgLower.includes('error') || msgLower.includes('exception')) return 'error';
        if (msgLower.includes('warning') || msgLower.includes('warn')) return 'warning';
        if (msgLower.includes('connected') || msgLower.includes('joined')) return 'player';
        if (msgLower.includes('command') || msgLower.includes('executing')) return 'command';
        
        return 'system';
    }
    
    /**
     * Store message in buffer
     */
    storeMessage(serverId, message) {
        const bufferKey = `messages_${serverId}`;
        
        if (!this.messageHandlers.has(bufferKey)) {
            this.messageHandlers.set(bufferKey, []);
        }
        
        const buffer = this.messageHandlers.get(bufferKey);
        buffer.push(message);
        
        // Limit buffer size
        if (buffer.length > this.options.messageBufferSize) {
            buffer.shift();
        }
    }
    
    /**
     * Get messages for a server
     */
    getMessages(serverId, limit = 50, messageType = null) {
        const bufferKey = `messages_${serverId}`;
        const buffer = this.messageHandlers.get(bufferKey) || [];
        
        let messages = [...buffer];
        
        // Filter by type
        if (messageType && messageType !== 'all') {
            messages = messages.filter(msg => msg.type === messageType);
        }
        
        // Sort by timestamp
        messages.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
        
        // Return limited results
        return limit ? messages.slice(-limit) : messages;
    }
    
    /**
     * Register message handler
     */
    onMessage(serverId, handler) {
        const handlerKey = `handler_${serverId}`;
        
        if (!this.messageHandlers.has(handlerKey)) {
            this.messageHandlers.set(handlerKey, []);
        }
        
        this.messageHandlers.get(handlerKey).push(handler);
        
        // Return unregister function
        return () => {
            const handlers = this.messageHandlers.get(handlerKey);
            if (handlers) {
                const index = handlers.indexOf(handler);
                if (index !== -1) {
                    handlers.splice(index, 1);
                }
            }
        };
    }
    
    /**
     * Call registered message handlers
     */
    callMessageHandlers(serverId, message) {
        const handlerKey = `handler_${serverId}`;
        const handlers = this.messageHandlers.get(handlerKey) || [];
        
        handlers.forEach(handler => {
            try {
                handler(message);
            } catch (error) {
                this.log(`Error in message handler for server ${serverId}:`, error, 'error');
            }
        });
    }
    
    /**
     * Handle connection closed
     */
    handleConnectionClosed(serverId, event) {
        const connectionKey = this.getConnectionKey(serverId);
        const state = this.connectionStates.get(connectionKey);
        
        if (state) {
            state.connected = false;
        }
        
        // Remove connection
        this.connections.delete(connectionKey);
        
        // Emit disconnected event
        this.emitEvent('websocket:disconnected', { serverId, code: event.code, reason: event.reason });
        
        // Attempt reconnection if enabled
        if (this.options.autoReconnect && state && state.reconnectAttempts < this.options.maxReconnectAttempts) {
            this.scheduleReconnect(serverId, state.region);
        }
    }
    
    /**
     * Schedule reconnection attempt
     */
    scheduleReconnect(serverId, region) {
        const connectionKey = this.getConnectionKey(serverId);
        const state = this.connectionStates.get(connectionKey);
        
        if (!state) return;
        
        state.reconnectAttempts++;
        
        const delay = this.options.reconnectDelay * Math.pow(2, state.reconnectAttempts - 1);
        
        this.log(`Scheduling reconnect for server ${serverId} in ${delay}ms (attempt ${state.reconnectAttempts})`);
        
        const timeoutId = setTimeout(() => {
            this.reconnectTimeouts.delete(connectionKey);
            this.connect(serverId, region).catch(error => {
                this.log(`Reconnection failed for server ${serverId}:`, error.message, 'error');
            });
        }, delay);
        
        this.reconnectTimeouts.set(connectionKey, timeoutId);
    }
    
    /**
     * Disconnect from server
     */
    disconnect(serverId) {
        const connectionKey = this.getConnectionKey(serverId);
        const connection = this.connections.get(connectionKey);
        
        if (connection) {
            // Send stop subscription
            try {
                const stopMessage = {
                    id: `console_stream_${serverId}`,
                    type: 'stop'
                };
                connection.send(JSON.stringify(stopMessage));
            } catch (error) {
                this.log(`Error sending stop message for server ${serverId}:`, error, 'error');
            }
            
            // Close connection
            connection.close();
            this.connections.delete(connectionKey);
        }
        
        // Clear reconnect timeout
        const timeoutId = this.reconnectTimeouts.get(connectionKey);
        if (timeoutId) {
            clearTimeout(timeoutId);
            this.reconnectTimeouts.delete(connectionKey);
        }
        
        // Update state
        const state = this.connectionStates.get(connectionKey);
        if (state) {
            state.connected = false;
        }
        
        this.log(`Disconnected from server ${serverId}`);
        this.emitEvent('websocket:disconnected', { serverId });
    }
    
    /**
     * Disconnect all connections
     */
    disconnectAll() {
        const serverIds = Array.from(this.connections.keys()).map(key => key.replace('server_', ''));
        
        serverIds.forEach(serverId => {
            this.disconnect(serverId);
        });
        
        this.log('Disconnected all WebSocket connections');
    }
    
    /**
     * Pause connections (hide page)
     */
    pauseConnections() {
        this.connections.forEach((connection, key) => {
            if (connection.readyState === WebSocket.OPEN) {
                // Don't close, just reduce activity
                this.log(`Pausing connection for ${key}`);
            }
        });
    }
    
    /**
     * Resume connections (show page)
     */
    resumeConnections() {
        this.connections.forEach((connection, key) => {
            if (connection.readyState === WebSocket.CLOSED) {
                // Reconnect closed connections
                const serverId = key.replace('server_', '');
                const state = this.connectionStates.get(key);
                if (state) {
                    this.connect(serverId, state.region);
                }
            }
        });
    }
    
    /**
     * Get connection status
     */
    getConnectionStatus(serverId = null) {
        if (serverId) {
            const connectionKey = this.getConnectionKey(serverId);
            return this.connectionStates.get(connectionKey) || null;
        }
        
        // Return all connection statuses
        const statuses = {};
        this.connectionStates.forEach((state, key) => {
            const serverId = key.replace('server_', '');
            statuses[serverId] = { ...state };
        });
        
        return statuses;
    }
    
    /**
     * Check if server is connected
     */
    isConnected(serverId) {
        const connectionKey = this.getConnectionKey(serverId);
        const connection = this.connections.get(connectionKey);
        return connection && connection.readyState === WebSocket.OPEN;
    }
    
    /**
     * Get authentication token
     */
    async getAuthToken() {
        try {
            if (this.api && this.api.auth && this.api.auth.getToken) {
                return await this.api.auth.getToken();
            }
            
            // Fallback: check token status endpoint
            const response = await fetch('/api/token/status');
            const data = await response.json();
            
            if (data.token_valid) {
                return data.access_token || 'demo_token';
            }
            
            return null;
        } catch (error) {
            this.log('Error getting auth token:', error, 'error');
            return null;
        }
    }
    
    /**
     * Handle server added event
     */
    async handleServerAdded(data) {
        if (data.server && data.server.isActive) {
            // Auto-connect to new server if auto-connect is enabled
            if (this.options.autoConnect) {
                try {
                    await this.connect(data.server.serverId, data.server.serverRegion);
                } catch (error) {
                    this.log(`Auto-connect failed for new server ${data.server.serverId}:`, error.message, 'error');
                }
            }
        }
    }
    
    /**
     * Handle server deleted event
     */
    handleServerDeleted(data) {
        if (data.serverId) {
            this.disconnect(data.serverId);
        }
    }
    
    /**
     * Get connection key for server
     */
    getConnectionKey(serverId) {
        return `server_${serverId}`;
    }
    
    /**
     * Emit event through event bus
     */
    emitEvent(event, data) {
        if (this.eventBus) {
            this.eventBus.emit(event, data);
        }
    }
    
    /**
     * Log message with optional level
     */
    log(message, data = null, level = 'info') {
        if (!this.options.debug && level === 'debug') return;
        
        const prefix = '[WebSocketService]';
        
        switch (level) {
            case 'error':
                console.error(prefix, message, data);
                break;
            case 'warn':
                console.warn(prefix, message, data);
                break;
            case 'debug':
                console.debug(prefix, message, data);
                break;
            default:
                console.log(prefix, message, data);
        }
    }
    
    /**
     * Get service statistics
     */
    getStats() {
        const totalConnections = this.connections.size;
        const activeConnections = Array.from(this.connections.values())
            .filter(conn => conn.readyState === WebSocket.OPEN).length;
            
        let totalMessages = 0;
        this.messageHandlers.forEach((buffer, key) => {
            if (key.startsWith('messages_')) {
                totalMessages += buffer.length;
            }
        });
        
        return {
            totalConnections,
            activeConnections,
            totalMessages,
            maxReconnectAttempts: this.options.maxReconnectAttempts,
            reconnectDelay: this.options.reconnectDelay,
            autoReconnect: this.options.autoReconnect
        };
    }
    
    /**
     * Destroy service and cleanup
     */
    destroy() {
        this.disconnectAll();
        
        // Clear all timeouts
        this.reconnectTimeouts.forEach(timeoutId => clearTimeout(timeoutId));
        this.reconnectTimeouts.clear();
        
        // Clear handlers
        this.messageHandlers.clear();
        
        // Clear states
        this.connectionStates.clear();
        
        this.log('WebSocket service destroyed');
    }
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = WebSocketService;
} else {
    window.WebSocketService = WebSocketService;
}