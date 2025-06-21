/**
 * GUST Bot Enhanced - WebSocket Service (EXTENDED FOR SENSOR DATA)
 * ================================================================
 * Manages WebSocket connections for live console monitoring + real-time sensor data
 * ✅ EXTENDED: Real-time sensor data (CPU, memory, uptime) subscriptions
 * ✅ EXTENDED: Server configuration data monitoring
 * ✅ EXTENDED: Sensor data storage and retrieval
 * ✅ EXTENDED: Health monitoring integration
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
        
        // ✅ NEW: Sensor data storage
        this.sensorData = new Map();
        this.configData = new Map();
        this.sensorCallbacks = new Map();
        
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
            debug: false,
            // ✅ NEW: Sensor options
            sensorDataBufferSize: 100,
            sensorDataMaxAge: 60000, // 60 seconds
            enableSensorData: true
        };
    }
    
    init() {
        this.bindEvents();
        this.log('WebSocket service initialized with sensor data support');
    }
    
    bindEvents() {
        if (this.eventBus) {
            this.eventBus.on('server:added', (data) => this.handleServerAdded(data));
            this.eventBus.on('server:deleted', (data) => this.handleServerDeleted(data));
            this.eventBus.on('console:connect', (data) => this.connect(data.serverId, data.region));
            this.eventBus.on('console:disconnect', (data) => this.disconnect(data.serverId));
            
            // ✅ NEW: Sensor-specific events
            this.eventBus.on('sensor:subscribe', (data) => this.subscribeSensorData(data.serverId, data.region));
            this.eventBus.on('sensor:unsubscribe', (data) => this.unsubscribeSensorData(data.serverId));
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
     * ✅ EXTENDED: Connect to live console + sensor data for a server
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
            this.log(`Connecting to server ${serverId} (${region}) with sensor data support`);
            
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
                messageCount: 0,
                // ✅ NEW: Sensor data status
                sensorDataEnabled: this.options.enableSensorData,
                sensorDataCount: 0,
                lastSensorData: null
            });
            
            // ✅ NEW: Subscribe to sensor data if enabled
            if (this.options.enableSensorData) {
                try {
                    await this.subscribeSensorData(serverId, region);
                    await this.subscribeServerConfig(serverId, region);
                } catch (sensorError) {
                    this.log(`Sensor subscription failed for server ${serverId}: ${sensorError.message}`, 'warn');
                }
            }
            
            // Emit connected event
            this.emitEvent('websocket:connected', { serverId, region, sensorEnabled: this.options.enableSensorData });
            
            this.log(`Connected to server ${serverId} with ${this.options.enableSensorData ? 'sensor data' : 'console only'}`);
            return connection;
            
        } catch (error) {
            this.log(`Failed to connect to server ${serverId}: ${error.message}`, 'error');
            this.emitEvent('websocket:error', { serverId, error: error.message });
            throw error;
        }
    }
    
    /**
     * ✅ EXTENDED: Create WebSocket connection to G-Portal with sensor support
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
                            // ✅ EXTENDED: Handle both console and sensor data
                            this.handleWebSocketMessage(serverId, data);
                            
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
     * ✅ NEW: Handle all WebSocket messages (console + sensor data)
     */
    handleWebSocketMessage(serverId, data) {
        const streamId = data.id || '';
        const payload = data.payload?.data;
        
        if (streamId.includes('console_stream_')) {
            // Existing console message handling
            this.handleConsoleMessage(serverId, data);
        } 
        else if (streamId.includes('sensors_stream_')) {
            // ✅ NEW: Sensor data handling
            this.handleSensorMessage(serverId, payload);
        }
        else if (streamId.includes('config_stream_')) {
            // ✅ NEW: Config data handling
            this.handleConfigMessage(serverId, payload);
        }
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
     * ✅ NEW: Subscribe to sensor data for a server
     */
    async subscribeSensorData(serverId, region = 'US') {
        try {
            const connection = this.connections.get(this.getConnectionKey(serverId));
            if (!connection) {
                throw new Error('No WebSocket connection available');
            }
            
            // Clean server ID (remove test suffixes)
            const cleanServerId = serverId.toString().split('_')[0];
            
            // Subscribe to sensor data
            const sensorSubscription = {
                id: `sensors_stream_${serverId}`,
                type: 'start',
                payload: {
                    query: `subscription ServiceSensors($sid: Int!, $region: String!) {
                        serviceSensors(rsid: {id: $sid, region: $region}) {
                            cpu
                            cpuTotal
                            memory {
                                percent
                                used
                                total
                            }
                            uptime
                            timestamp
                            __typename
                        }
                    }`,
                    variables: {
                        sid: parseInt(cleanServerId),
                        region: region.toUpperCase()
                    }
                }
            };
            
            connection.send(JSON.stringify(sensorSubscription));
            this.log(`Subscribed to sensor data for server ${serverId}`);
            
        } catch (error) {
            this.log(`Failed to subscribe to sensor data for ${serverId}: ${error.message}`, 'error');
            throw error;
        }
    }
    
    /**
     * ✅ NEW: Subscribe to server configuration data
     */
    async subscribeServerConfig(serverId, region = 'US') {
        try {
            const connection = this.connections.get(this.getConnectionKey(serverId));
            if (!connection) {
                throw new Error('No WebSocket connection available');
            }
            
            const cleanServerId = serverId.toString().split('_')[0];
            
            const configSubscription = {
                id: `config_stream_${serverId}`,
                type: 'start',
                payload: {
                    query: `subscription ServerConfig($sid: Int!, $region: String!) {
                        cfgContext(rsid: {id: $sid, region: $region}) {
                            ns {
                                service {
                                    currentState {
                                        state
                                        fsmState
                                        fsmIsTransitioning
                                    }
                                    config {
                                        state
                                        ipAddress
                                    }
                                }
                            }
                        }
                    }`,
                    variables: {
                        sid: parseInt(cleanServerId),
                        region: region.toUpperCase()
                    }
                }
            };
            
            connection.send(JSON.stringify(configSubscription));
            this.log(`Subscribed to config data for server ${serverId}`);
            
        } catch (error) {
            this.log(`Failed to subscribe to config data for ${serverId}: ${error.message}`, 'error');
            throw error;
        }
    }
    
    /**
     * ✅ NEW: Handle sensor data messages
     */
    handleSensorMessage(serverId, data) {
        try {
            if (data && data.serviceSensors) {
                const sensorData = {
                    serverId: serverId,
                    cpu: data.serviceSensors.cpu || 0,
                    cpuTotal: data.serviceSensors.cpuTotal || 0,
                    memoryPercent: data.serviceSensors.memory?.percent || 0,
                    memoryUsed: data.serviceSensors.memory?.used || 0,
                    memoryTotal: data.serviceSensors.memory?.total || 0,
                    uptime: data.serviceSensors.uptime || 0,
                    timestamp: data.serviceSensors.timestamp || new Date().toISOString(),
                    receivedAt: Date.now(),
                    dataSource: 'websocket_live'
                };
                
                // Store sensor data
                this.storeSensorData(serverId, sensorData);
                
                // Update connection state
                const connectionKey = this.getConnectionKey(serverId);
                const state = this.connectionStates.get(connectionKey);
                if (state) {
                    state.sensorDataCount++;
                    state.lastSensorData = Date.now();
                }
                
                // Emit sensor data event
                this.emitEvent('websocket:sensor_data', sensorData);
                this.emitEvent(`websocket:sensor_data:${serverId}`, sensorData);
                
                // Call sensor callbacks
                this.callSensorCallbacks(serverId, sensorData);
                
                this.log(`Sensor data updated for server ${serverId}: CPU ${sensorData.cpuTotal}%, Memory ${sensorData.memoryPercent}%`);
            }
        } catch (error) {
            this.log(`Error handling sensor message for server ${serverId}: ${error.message}`, 'error');
        }
    }
    
    /**
     * ✅ NEW: Handle config data messages
     */
    handleConfigMessage(serverId, data) {
        try {
            if (data && data.cfgContext && data.cfgContext.ns && data.cfgContext.ns.service) {
                const service = data.cfgContext.ns.service;
                const currentState = service.currentState || {};
                const config = service.config || {};
                
                const configData = {
                    serverId: serverId,
                    serverState: currentState.state || 'UNKNOWN',
                    fsmState: currentState.fsmState || 'Unknown',
                    isTransitioning: currentState.fsmIsTransitioning || false,
                    ipAddress: config.ipAddress || '',
                    timestamp: new Date().toISOString(),
                    receivedAt: Date.now(),
                    dataSource: 'websocket_live'
                };
                
                // Store config data
                this.storeConfigData(serverId, configData);
                
                // Emit config data event
                this.emitEvent('websocket:config_data', configData);
                this.emitEvent(`websocket:config_data:${serverId}`, configData);
                
                this.log(`Config data updated for server ${serverId}: State ${configData.serverState}`);
            }
        } catch (error) {
            this.log(`Error handling config message for server ${serverId}: ${error.message}`, 'error');
        }
    }
    
    /**
     * ✅ NEW: Store sensor data with history
     */
    storeSensorData(serverId, sensorData) {
        const sensorKey = `sensor_${serverId}`;
        const historyKey = `sensor_history_${serverId}`;
        
        // Store latest data
        this.sensorData.set(sensorKey, sensorData);
        
        // Store in history
        if (!this.sensorData.has(historyKey)) {
            this.sensorData.set(historyKey, []);
        }
        
        const history = this.sensorData.get(historyKey);
        history.push(sensorData);
        
        // Limit history size
        if (history.length > this.options.sensorDataBufferSize) {
            history.shift();
        }
    }
    
    /**
     * ✅ NEW: Store config data
     */
    storeConfigData(serverId, configData) {
        const configKey = `config_${serverId}`;
        this.configData.set(configKey, configData);
    }
    
    /**
     * ✅ NEW: Get latest sensor data for a server
     */
    getLatestSensorData(serverId) {
        const sensorKey = `sensor_${serverId}`;
        const data = this.sensorData.get(sensorKey);
        
        if (!data) return null;
        
        // Check if data is fresh
        const age = Date.now() - data.receivedAt;
        if (age > this.options.sensorDataMaxAge) {
            this.log(`Sensor data for server ${serverId} is stale (${Math.round(age/1000)}s old)`, 'warn');
            return null;
        }
        
        return data;
    }
    
    /**
     * ✅ NEW: Get sensor data history
     */
    getSensorDataHistory(serverId, limit = 50) {
        const historyKey = `sensor_history_${serverId}`;
        const history = this.sensorData.get(historyKey) || [];
        
        return limit ? history.slice(-limit) : history;
    }
    
    /**
     * ✅ NEW: Get latest config data
     */
    getLatestConfigData(serverId) {
        const configKey = `config_${serverId}`;
        return this.configData.get(configKey) || null;
    }
    
    /**
     * ✅ NEW: Check if sensor data is fresh
     */
    isSensorDataFresh(serverId, maxAge = null) {
        const data = this.sensorData.get(`sensor_${serverId}`);
        if (!data) return false;
        
        const age = Date.now() - data.receivedAt;
        const threshold = maxAge || this.options.sensorDataMaxAge;
        
        return age <= threshold;
    }
    
    /**
     * ✅ NEW: Register sensor data callback
     */
    onSensorData(serverId, callback) {
        const callbackKey = `sensor_callback_${serverId}`;
        
        if (!this.sensorCallbacks.has(callbackKey)) {
            this.sensorCallbacks.set(callbackKey, []);
        }
        
        this.sensorCallbacks.get(callbackKey).push(callback);
        
        // Return unregister function
        return () => {
            const callbacks = this.sensorCallbacks.get(callbackKey);
            if (callbacks) {
                const index = callbacks.indexOf(callback);
                if (index !== -1) {
                    callbacks.splice(index, 1);
                }
            }
        };
    }
    
    /**
     * ✅ NEW: Call sensor data callbacks
     */
    callSensorCallbacks(serverId, sensorData) {
        const callbackKey = `sensor_callback_${serverId}`;
        const callbacks = this.sensorCallbacks.get(callbackKey) || [];
        
        callbacks.forEach(callback => {
            try {
                callback(sensorData);
            } catch (error) {
                this.log(`Error in sensor callback for server ${serverId}:`, error, 'error');
            }
        });
    }
    
    /**
     * ✅ NEW: Test sensor data subscription
     */
    async testSensorSubscription(serverId) {
        try {
            this.log(`Testing sensor subscription for server ${serverId}`);
            
            // Check if connected
            if (!this.isConnected(serverId)) {
                throw new Error('Server not connected');
            }
            
            // Subscribe to sensor data
            const connectionKey = this.getConnectionKey(serverId);
            const state = this.connectionStates.get(connectionKey);
            if (state) {
                await this.subscribeSensorData(serverId, state.region);
            }
            
            // Wait for sensor data (up to 10 seconds)
            return new Promise((resolve, reject) => {
                const timeout = setTimeout(() => {
                    reject(new Error('Sensor data test timeout'));
                }, 10000);
                
                const checkData = () => {
                    const sensorData = this.getLatestSensorData(serverId);
                    if (sensorData) {
                        clearTimeout(timeout);
                        resolve(sensorData);
                    } else {
                        setTimeout(checkData, 1000);
                    }
                };
                
                checkData();
            });
            
        } catch (error) {
            this.log(`Sensor subscription test failed for server ${serverId}: ${error.message}`, 'error');
            throw error;
        }
    }
    
    /**
     * ✅ NEW: Unsubscribe from sensor data
     */
    unsubscribeSensorData(serverId) {
        const connection = this.connections.get(this.getConnectionKey(serverId));
        if (connection) {
            try {
                // Stop sensor subscription
                const stopSensorMessage = {
                    id: `sensors_stream_${serverId}`,
                    type: 'stop'
                };
                connection.send(JSON.stringify(stopSensorMessage));
                
                // Stop config subscription
                const stopConfigMessage = {
                    id: `config_stream_${serverId}`,
                    type: 'stop'
                };
                connection.send(JSON.stringify(stopConfigMessage));
                
                this.log(`Unsubscribed from sensor data for server ${serverId}`);
            } catch (error) {
                this.log(`Error unsubscribing sensor data for server ${serverId}:`, error, 'error');
            }
        }
    }
    
    /**
     * ✅ NEW: Get sensor statistics
     */
    getSensorStats() {
        const totalServers = this.connections.size;
        let serversWithSensorData = 0;
        let serversWithFreshData = 0;
        let totalSensorMessages = 0;
        
        this.connectionStates.forEach((state, key) => {
            if (state.sensorDataCount > 0) {
                serversWithSensorData++;
                totalSensorMessages += state.sensorDataCount;
            }
            
            const serverId = key.replace('server_', '');
            if (this.isSensorDataFresh(serverId)) {
                serversWithFreshData++;
            }
        });
        
        return {
            totalServers,
            serversWithSensorData,
            serversWithFreshData,
            totalSensorMessages,
            sensorDataCoverage: totalServers > 0 ? `${serversWithSensorData}/${totalServers}` : '0/0',
            freshDataCoverage: totalServers > 0 ? `${serversWithFreshData}/${totalServers}` : '0/0'
        };
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
     * ✅ EXTENDED: Disconnect from server with sensor data cleanup
     */
    disconnect(serverId) {
        const connectionKey = this.getConnectionKey(serverId);
        const connection = this.connections.get(connectionKey);
        
        if (connection) {
            // Send stop subscriptions
            try {
                const stopConsoleMessage = {
                    id: `console_stream_${serverId}`,
                    type: 'stop'
                };
                connection.send(JSON.stringify(stopConsoleMessage));
                
                // ✅ NEW: Stop sensor subscriptions
                if (this.options.enableSensorData) {
                    this.unsubscribeSensorData(serverId);
                }
            } catch (error) {
                this.log(`Error sending stop messages for server ${serverId}:`, error, 'error');
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
        
        // ✅ NEW: Clean up sensor data
        this.sensorData.delete(`sensor_${serverId}`);
        this.sensorData.delete(`sensor_history_${serverId}`);
        this.configData.delete(`config_${serverId}`);
        this.sensorCallbacks.delete(`sensor_callback_${serverId}`);
        
        // Update state
        const state = this.connectionStates.get(connectionKey);
        if (state) {
            state.connected = false;
        }
        
        this.log(`Disconnected from server ${serverId} (including sensor data)`);
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
     * ✅ EXTENDED: Get connection status including sensor data
     */
    getConnectionStatus(serverId = null) {
        if (serverId) {
            const connectionKey = this.getConnectionKey(serverId);
            const state = this.connectionStates.get(connectionKey);
            if (state) {
                return {
                    ...state,
                    // ✅ NEW: Sensor data status
                    hasSensorData: this.getLatestSensorData(serverId) !== null,
                    sensorDataFresh: this.isSensorDataFresh(serverId),
                    hasConfigData: this.getLatestConfigData(serverId) !== null
                };
            }
            return null;
        }
        
        // Return all connection statuses
        const statuses = {};
        this.connectionStates.forEach((state, key) => {
            const serverId = key.replace('server_', '');
            statuses[serverId] = {
                ...state,
                // ✅ NEW: Sensor data status
                hasSensorData: this.getLatestSensorData(serverId) !== null,
                sensorDataFresh: this.isSensorDataFresh(serverId),
                hasConfigData: this.getLatestConfigData(serverId) !== null
            };
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
                // console.log removed for production deployment
        }
    }
    
    /**
     * ✅ EXTENDED: Get service statistics including sensor data
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
        
        // ✅ NEW: Sensor statistics
        const sensorStats = this.getSensorStats();
        
        return {
            totalConnections,
            activeConnections,
            totalMessages,
            maxReconnectAttempts: this.options.maxReconnectAttempts,
            reconnectDelay: this.options.reconnectDelay,
            autoReconnect: this.options.autoReconnect,
            // ✅ NEW: Sensor data statistics
            sensorDataEnabled: this.options.enableSensorData,
            ...sensorStats
        };
    }
    
    /**
     * ✅ EXTENDED: Destroy service and cleanup including sensor data
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
        
        // ✅ NEW: Clear sensor data
        this.sensorData.clear();
        this.configData.clear();
        this.sensorCallbacks.clear();
        
        this.log('WebSocket service destroyed (including sensor data)');
    }
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = WebSocketService;
} else {
    window.WebSocketService = WebSocketService;
}