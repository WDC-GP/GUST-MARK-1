/**
 * Console Component - Console and Live Monitoring
 * Handles console commands, live message monitoring, and WebSocket connections
 */
class ConsoleComponent extends BaseComponent {
    constructor(containerId, options = {}) {
        super(containerId, options);
        this.api = options.api || window.App.api;
        this.eventBus = options.eventBus || window.App.eventBus;
        this.websocketService = options.websocketService || window.App.websocketService;
        this.autoScrollEnabled = true;
        this.refreshInterval = null;
    }
    
    get defaultOptions() {
        return {
            ...super.defaultOptions,
            messageBufferSize: 1000,
            autoRefreshInterval: 3000,
            enableWebSockets: true,
            autoConnectServers: true
        };
    }
    
    getInitialState() {
        return {
            ...super.getInitialState(),
            servers: [],
            selectedServerId: '',
            messageTypeFilter: 'all',
            serverFilter: '',
            messages: [],
            connectionStatus: {},
            websocketsAvailable: false,
            liveConnections: {}
        };
    }
    
    render() {
        this.container.innerHTML = `
            <div class="console">
                <h2 class="text-3xl font-bold mb-6">🔧 Console & Live Monitor (Enhanced)</h2>
                
                <!-- Enhanced Console Info -->
                <div class="bg-green-800 border border-green-600 p-4 rounded-lg mb-6">
                    <h3 class="text-lg font-semibold text-green-300">📺 Auto Live Console Active!</h3>
                    <p class="text-green-200">All servers from Server Manager are automatically connected for live monitoring!</p>
                    <div class="text-sm text-green-200 mt-2">
                        <span class="font-medium">Auto Features:</span>
                        Auto-connect | Auto-reconnect | Real-time display | Combined output
                    </div>
                </div>
                
                <div class="flex gap-6">
                    <!-- Main Console Area -->
                    <div class="flex-1">
                        <div class="bg-gray-800 p-6 rounded-lg">
                            <!-- Command Controls -->
                            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                                <div>
                                    <label class="block text-sm font-medium mb-2">Command Target Server</label>
                                    <select id="consoleServerSelect" class="w-full bg-gray-700 p-3 rounded border border-gray-600 focus:border-purple-500">
                                        <option value="">Choose a server...</option>
                                    </select>
                                </div>
                                <div class="flex items-end">
                                    <button id="refreshConsoleBtn" class="w-full bg-blue-600 hover:bg-blue-700 p-3 rounded">
                                        Refresh Output
                                    </button>
                                </div>
                            </div>
                            
                            <!-- Command Input -->
                            <div class="flex mb-4">
                                <input type="text" id="consoleInput" 
                                       class="flex-1 bg-gray-700 p-3 rounded-l border border-gray-600 focus:border-purple-500" 
                                       placeholder="Enter console command...">
                                <button id="sendCommandBtn" class="bg-purple-600 hover:bg-purple-700 px-6 py-3 rounded-r">
                                    Send
                                </button>
                            </div>
                            
                            <!-- Quick Commands -->
                            <div class="mb-6">
                                <h4 class="text-sm font-medium mb-3">Quick Commands</h4>
                                <div class="grid grid-cols-2 md:grid-cols-4 gap-2">
                                    <button class="quick-command p-2 bg-gray-700 hover:bg-gray-600 rounded text-sm" 
                                            data-command="serverinfo">📊 Server Info</button>
                                    <button class="quick-command p-2 bg-gray-700 hover:bg-gray-600 rounded text-sm" 
                                            data-command="global.getauthlevels">👑 Auth Levels</button>
                                    <button class="quick-command p-2 bg-gray-700 hover:bg-gray-600 rounded text-sm" 
                                            data-command="server.save">💾 Save Server</button>
                                    <button class="quick-command p-2 bg-gray-700 hover:bg-gray-600 rounded text-sm" 
                                            data-command='global.say "Server Message"'>📢 Say Message</button>
                                </div>
                            </div>
                            
                            <!-- Live Monitor Controls -->
                            <div class="border-t border-gray-700 pt-4 mb-4">
                                <h4 class="text-sm font-medium mb-3">Live Monitor Controls</h4>
                                <div class="flex items-center space-x-4 mb-4">
                                    <select id="monitorServerFilter" class="p-2 bg-gray-700 rounded border border-gray-600 focus:border-purple-500">
                                        <option value="">🌐 All Connected Servers</option>
                                    </select>
                                    <select id="consoleMessageTypeFilter" class="p-2 bg-gray-700 rounded border border-gray-600 focus:border-purple-500">
                                        <option value="all">📋 All Messages</option>
                                        <option value="chat">💬 Chat Messages</option>
                                        <option value="auth">🔐 Auth/VIP Updates</option>
                                        <option value="save">💾 Server Saves</option>
                                        <option value="kill">⚔️ Kill Feed</option>
                                        <option value="error">❌ Errors</option>
                                        <option value="warning">⚠️ Warnings</option>
                                        <option value="command">🔧 Commands</option>
                                        <option value="player">👥 Player Events</option>
                                        <option value="system">🖥️ System Messages</option>
                                        <option value="event">🎯 Events</option>
                                        <option value="ban">🚫 Bans</option>
                                    </select>
                                    <button id="clearConsoleBtn" class="bg-red-600 hover:bg-red-700 px-3 py-2 rounded text-sm">
                                        Clear
                                    </button>
                                    <label class="flex items-center">
                                        <input type="checkbox" id="consoleAutoScroll" checked class="mr-2">
                                        <span class="text-sm">Auto-scroll</span>
                                    </label>
                                </div>
                            </div>
                            
                            <!-- Server Status Info -->
                            <div class="mb-4">
                                <div class="text-sm text-gray-400">
                                    No servers? <button id="gotoServerManagerBtn" class="text-purple-400 hover:text-purple-300 underline">Add servers in Server Manager</button>
                                </div>
                            </div>
                            
                            <!-- Console Output -->
                            <div id="consoleOutput" class="bg-black p-4 rounded h-96 overflow-y-auto font-mono text-sm">
                                <div class="text-green-400">GUST Bot Console - Ready (Commands + Live Messages)</div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Live Connection Sidebar -->
                    <div class="w-80 bg-gray-800 rounded-lg p-4">
                        <h3 class="text-lg font-semibold mb-4">🔗 Live Connections</h3>
                        
                        <!-- Auto-Connection Status -->
                        <div class="mb-6 p-4 bg-gray-700 rounded">
                            <div class="text-center">
                                <div class="text-sm font-medium text-green-300 mb-2">🔄 Auto-Connect Mode</div>
                                <div class="text-xs text-gray-300">
                                    All servers from Server Manager are automatically connected for live monitoring.
                                </div>
                                <div class="text-xs text-blue-300 mt-2">
                                    Add servers in <button id="gotoServerManager2Btn" class="text-purple-400 hover:text-purple-300 underline">Server Manager</button> to see them here.
                                </div>
                            </div>
                        </div>
                        
                        <!-- WebSocket Status -->
                        <div class="mb-6 p-3 bg-gray-700 rounded">
                            <h4 class="text-sm font-semibold mb-2">WebSocket Status</h4>
                            <div id="websocketStatusInfo" class="text-xs text-gray-300">
                                <div>Status: <span id="wsStatus">Checking...</span></div>
                                <div>Available: <span id="wsAvailable">Checking...</span></div>
                            </div>
                        </div>
                        
                        <!-- Active Connections -->
                        <div class="mb-6">
                            <h4 class="text-md font-semibold mb-3">Active Live Connections</h4>
                            <div id="liveActiveConnections" class="space-y-2">
                                <div class="text-gray-400 text-sm text-center py-4">
                                    No active connections
                                </div>
                            </div>
                        </div>
                        
                        <!-- Connection Stats -->
                        <div class="p-3 bg-gray-700 rounded">
                            <h4 class="text-sm font-semibold mb-2">Connection Status</h4>
                            <div id="connectionStats" class="text-xs text-gray-300">
                                <div>Active: <span id="activeConnectionCount">0</span></div>
                                <div>Total Messages: <span id="totalMessageCount">0</span></div>
                                <div>Last Update: <span id="lastUpdateTime">Never</span></div>
                            </div>
                        </div>
                        
                        <!-- Test Button -->
                        <div class="mt-4">
                            <button id="testLiveConsoleBtn" class="w-full bg-blue-600 hover:bg-blue-700 p-2 rounded text-sm">
                                🔍 Test Live Console
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    bindEvents() {
        // Command controls
        const sendBtn = this.container.querySelector('#sendCommandBtn');
        const refreshBtn = this.container.querySelector('#refreshConsoleBtn');
        const consoleInput = this.container.querySelector('#consoleInput');
        const clearBtn = this.container.querySelector('#clearConsoleBtn');
        
        this.addEventListener(sendBtn, 'click', () => this.sendConsoleCommand());
        this.addEventListener(refreshBtn, 'click', () => this.refreshConsole());
        this.addEventListener(clearBtn, 'click', () => this.clearConsole());
        
        // Console input enter key
        this.addEventListener(consoleInput, 'keypress', (e) => {
            if (e.key === 'Enter') this.sendConsoleCommand();
        });
        
        // Quick commands
        const quickCommandBtns = this.container.querySelectorAll('.quick-command');
        quickCommandBtns.forEach(btn => {
            this.addEventListener(btn, 'click', (e) => {
                const command = e.target.dataset.command;
                this.setCommand(command);
            });
        });
        
        // Filters
        const serverFilter = this.container.querySelector('#monitorServerFilter');
        const messageTypeFilter = this.container.querySelector('#consoleMessageTypeFilter');
        const autoScrollCheck = this.container.querySelector('#consoleAutoScroll');
        
        this.addEventListener(serverFilter, 'change', (e) => {
            this.setState({ serverFilter: e.target.value });
            this.refreshConsoleWithLiveMessages();
        });
        
        this.addEventListener(messageTypeFilter, 'change', (e) => {
            this.setState({ messageTypeFilter: e.target.value });
            this.refreshConsoleWithLiveMessages();
        });
        
        this.addEventListener(autoScrollCheck, 'change', (e) => {
            this.autoScrollEnabled = e.target.checked;
        });
        
        // Navigation buttons
        const gotoServerMgr = this.container.querySelector('#gotoServerManagerBtn');
        const gotoServerMgr2 = this.container.querySelector('#gotoServerManager2Btn');
        const testBtn = this.container.querySelector('#testLiveConsoleBtn');
        
        this.addEventListener(gotoServerMgr, 'click', () => {
            this.eventBus.emit('navigation:goto', { route: 'server-manager' });
        });
        
        this.addEventListener(gotoServerMgr2, 'click', () => {
            this.eventBus.emit('navigation:goto', { route: 'server-manager' });
        });
        
        this.addEventListener(testBtn, 'click', () => this.testLiveConsole());
        
        // Listen for events from other components
        this.eventBus.on('servers:updated', (data) => this.updateServerDropdowns(data.servers));
        this.eventBus.on('server:auto-connect', (data) => this.autoConnectToServer(data));
        this.eventBus.on('websocket:message', (data) => this.handleLiveMessage(data));
        this.eventBus.on('websocket:status-changed', (data) => this.updateConnectionStatus(data));
    }
    
    async loadData() {
        try {
            this.setState({ loading: true, error: null });
            
            // Load servers and console output
            await Promise.all([
                this.loadServers(),
                this.loadConsoleOutput(),
                this.loadConnectionStatus()
            ]);
            
            this.setState({ loading: false });
            this.refreshConsoleWithLiveMessages();
            
        } catch (error) {
            this.handleError(error);
        }
    }
    
    async loadServers() {
        try {
            const servers = await this.api.servers.list();
            this.setState({ servers });
            this.updateServerDropdowns(servers);
            
            // Auto-connect to active servers if enabled
            if (this.options.autoConnectServers) {
                this.autoConnectToAllServers(servers);
            }
        } catch (error) {
            console.warn('Failed to load servers:', error);
        }
    }
    
    async loadConsoleOutput() {
        try {
            const output = await this.api.console.output();
            this.setState({ messages: output });
        } catch (error) {
            console.warn('Failed to load console output:', error);
        }
    }
    
    async loadConnectionStatus() {
        try {
            const status = await this.api.console.liveStatus();
            this.setState({ 
                connectionStatus: status.connections || {},
                websocketsAvailable: status.websockets_available || false
            });
            this.updateConnectionStatusDisplay();
        } catch (error) {
            console.warn('Failed to load connection status:', error);
        }
    }
    
    updateServerDropdowns(servers) {
        const consoleSelect = this.container.querySelector('#consoleServerSelect');
        const monitorSelect = this.container.querySelector('#monitorServerFilter');
        
        // Update console server select
        if (consoleSelect) {
            const currentValue = consoleSelect.value;
            consoleSelect.innerHTML = '<option value="">Choose a server...</option>';
            
            servers.filter(s => s.isActive).forEach(server => {
                const option = document.createElement('option');
                option.value = server.serverId;
                option.textContent = `${server.serverName} (${server.serverId}) - ${server.serverRegion}`;
                consoleSelect.appendChild(option);
            });
            
            if (currentValue) consoleSelect.value = currentValue;
        }
        
        // Update monitor filter
        if (monitorSelect) {
            const currentValue = monitorSelect.value;
            monitorSelect.innerHTML = '<option value="">🌐 All Connected Servers</option>';
            
            Object.keys(this.state.connectionStatus).forEach(serverId => {
                const server = servers.find(s => s.serverId === serverId);
                const serverName = server ? server.serverName : `Server ${serverId}`;
                const option = document.createElement('option');
                option.value = serverId;
                option.textContent = `${serverName} (${serverId})`;
                monitorSelect.appendChild(option);
            });
            
            if (currentValue) monitorSelect.value = currentValue;
        }
    }
    
    async autoConnectToAllServers(servers) {
        if (!this.state.websocketsAvailable) {
            // WebSockets not available - skipping auto-connect
            return;
        }
        
        for (const server of servers.filter(s => s.isActive)) {
            await this.autoConnectToServer(server);
            // Small delay between connections
            await new Promise(resolve => setTimeout(resolve, 500));
        }
    }
    
    async autoConnectToServer(server) {
        try {
            // Auto-connecting to server - console.log removed for production
            
            const result = await this.api.console.liveConnect({
                serverId: server.serverId,
                region: server.serverRegion || 'US'
            });
            
            if (result.success) {
                // Auto-connected to server - console.log removed for production
                this.addConsoleMessage({
                    timestamp: new Date().toISOString(),
                    message: `🔄 Auto-connected to ${server.serverName || server.serverId} for live monitoring`,
                    type: 'system',
                    source: 'auto_connection'
                });
            } else {
                if (!result.error?.includes('Demo mode') && !result.error?.includes('demo')) {
                    this.addConsoleMessage({
                        timestamp: new Date().toISOString(),
                        message: `⚠️ Auto-connect failed for ${server.serverName || server.serverId}: ${result.error}`,
                        type: 'warning',
                        source: 'auto_connection'
                    });
                }
            }
        } catch (error) {
            console.error(`Error auto-connecting to ${server.serverName || server.serverId}:`, error);
        }
    }
    
    setCommand(command) {
        const input = this.container.querySelector('#consoleInput');
        if (input) {
            input.value = command;
            input.focus();
        }
    }
    
    async sendConsoleCommand() {
        const command = this.container.querySelector('#consoleInput').value.trim();
        const serverSelect = this.container.querySelector('#consoleServerSelect');
        const serverId = serverSelect.value;
        
        if (!command) {
            this.showNotification('Please enter a command', 'error');
            return;
        }
        
        if (!serverId) {
            this.showNotification('Please select a server from the dropdown', 'error');
            return;
        }
        
        const server = this.state.servers.find(s => s.serverId === serverId);
        const region = server ? server.serverRegion : 'US';
        
        // Add command to output
        this.addConsoleMessage({
            timestamp: new Date().toISOString(),
            message: `> ${command} (Server: ${serverId})`,
            type: 'command',
            source: 'user_input'
        });
        
        try {
            const result = await this.api.console.send({
                command: command,
                serverId: serverId,
                region: region
            });
            
            if (result.success) {
                this.addConsoleMessage({
                    timestamp: new Date().toISOString(),
                    message: `✅ Command sent successfully to ${server?.serverName || serverId}`,
                    type: 'system',
                    source: 'command_response'
                });
                
                this.container.querySelector('#consoleInput').value = '';
                
                // Auto-refresh to show new messages
                setTimeout(() => {
                    this.refreshConsoleWithLiveMessages();
                }, 1000);
                
            } else {
                this.addConsoleMessage({
                    timestamp: new Date().toISOString(),
                    message: `❌ Command failed: ${result.error || 'Unknown error'}`,
                    type: 'error',
                    source: 'command_response'
                });
            }
        } catch (error) {
            this.addConsoleMessage({
                timestamp: new Date().toISOString(),
                message: `❌ Send error: ${error.message}`,
                type: 'error',
                source: 'command_response'
            });
        }
    }
    
    async refreshConsole() {
        await this.loadConsoleOutput();
        this.refreshConsoleWithLiveMessages();
    }
    
    async refreshConsoleWithLiveMessages() {
        try {
            // Get regular console output
            const consoleOutput = this.state.messages;
            
            // Get live messages
            const params = new URLSearchParams();
            if (this.state.serverFilter) params.append('serverId', this.state.serverFilter);
            if (this.state.messageTypeFilter !== 'all') params.append('type', this.state.messageTypeFilter);
            params.append('limit', '30');
            
            let liveMessages = [];
            try {
                const liveResponse = await this.api.console.liveMessages(Object.fromEntries(params));
                liveMessages = liveResponse.messages || [];
            } catch (error) {
                console.warn('Failed to load live messages:', error);
            }
            
            // Combine and display messages
            this.displayCombinedConsoleOutput(consoleOutput, liveMessages);
            
        } catch (error) {
            console.error('Error refreshing console with live messages:', error);
            this.displayCombinedConsoleOutput(this.state.messages, []);
        }
    }
    
    displayCombinedConsoleOutput(consoleOutput, liveMessages) {
        const outputDiv = this.container.querySelector('#consoleOutput');
        if (!outputDiv) return;
        
        const wasScrolledToBottom = this.isScrolledToBottom(outputDiv);
        
        // Clear and add header
        outputDiv.innerHTML = '<div class="text-green-400">GUST Bot Console - Ready (Commands + Live Messages)</div>';
        
        // Add console command output
        consoleOutput.forEach(entry => {
            const div = this.createConsoleMessageElement(entry);
            outputDiv.appendChild(div);
        });
        
        // Add live messages if any
        if (liveMessages.length > 0) {
            // Add separator
            const separator = document.createElement('div');
            separator.className = 'text-yellow-400 text-sm border-t border-gray-600 pt-2 mt-2';
            separator.textContent = '📺 Live Console Messages:';
            outputDiv.appendChild(separator);
            
            // Add live messages
            liveMessages.forEach(message => {
                const div = this.createLiveMessageElement(message);
                outputDiv.appendChild(div);
            });
        }
        
        // Auto-scroll if needed
        if (this.autoScrollEnabled && wasScrolledToBottom) {
            outputDiv.scrollTop = outputDiv.scrollHeight;
        }
    }
    
    createConsoleMessageElement(entry) {
        const div = document.createElement('div');
        div.className = 'mb-1 text-sm';
        
        if (entry.command) {
            div.className += ' text-blue-400 font-mono';
            div.textContent = `> ${entry.command}`;
        } else {
            div.className += entry.status === 'server_response' ? ' text-white' : ' text-gray-400';
            div.textContent = entry.message;
        }
        
        return div;
    }
    
    createLiveMessageElement(message) {
        const div = document.createElement('div');
        div.className = 'console-live-message text-sm mb-1 pl-2 border-l-2 border-blue-500';
        
        const time = new Date(message.timestamp).toLocaleTimeString();
        const type = message.type || 'system';
        const serverId = message.server_id || message.serverId || '';
        
        // Format the message with timestamp and type
        const typeIcon = this.getTypeIcon(type);
        const serverInfo = serverId ? ` [${serverId}]` : '';
        
        div.innerHTML = `
            <span class="text-gray-500 text-xs">[${time}]</span>
            <span class="text-xs bg-gray-700 px-1 rounded">${typeIcon} ${type}</span>
            ${serverInfo ? `<span class="text-xs text-gray-400">${serverInfo}</span>` : ''}
            <div class="text-gray-200 font-mono mt-1">${this.escapeHtml(message.message)}</div>
        `;
        
        return div;
    }
    
    addConsoleMessage(message) {
        const outputDiv = this.container.querySelector('#consoleOutput');
        if (!outputDiv) return;
        
        const wasScrolledToBottom = this.isScrolledToBottom(outputDiv);
        
        const messageDiv = document.createElement('div');
        messageDiv.className = 'text-blue-300 text-sm mb-1';
        
        const time = new Date(message.timestamp).toLocaleTimeString();
        messageDiv.textContent = `[${time}] ${message.message}`;
        
        outputDiv.appendChild(messageDiv);
        
        if (this.autoScrollEnabled && wasScrolledToBottom) {
            outputDiv.scrollTop = outputDiv.scrollHeight;
        }
    }
    
    clearConsole() {
        const outputDiv = this.container.querySelector('#consoleOutput');
        if (outputDiv) {
            outputDiv.innerHTML = '<div class="text-green-400">GUST Bot Console - Cleared</div>';
        }
    }
    
    isScrolledToBottom(element) {
        return element.scrollTop + element.clientHeight >= element.scrollHeight - 10;
    }
    
    async updateConnectionStatus(data) {
        this.setState({ connectionStatus: data.connections || {} });
        await this.loadConnectionStatus();
        this.updateConnectionStatusDisplay();
    }
    
    updateConnectionStatusDisplay() {
        const { connectionStatus, websocketsAvailable } = this.state;
        
        // Update WebSocket status
        const wsStatus = this.container.querySelector('#wsStatus');
        const wsAvailable = this.container.querySelector('#wsAvailable');
        
        if (wsStatus) {
            wsStatus.textContent = websocketsAvailable ? 'Connected' : 'Unavailable';
            wsStatus.className = websocketsAvailable ? 'text-green-400' : 'text-red-400';
        }
        
        if (wsAvailable) {
            wsAvailable.textContent = websocketsAvailable ? 'Yes ✅' : 'No ❌';
            wsAvailable.className = websocketsAvailable ? 'text-green-400' : 'text-red-400';
        }
        
        // Update connection stats
        const activeCount = Object.values(connectionStatus).filter(c => c.connected).length;
        const totalMessages = Object.values(connectionStatus).reduce((sum, c) => sum + (c.message_count || 0), 0);
        
        this.updateElement('#activeConnectionCount', activeCount);
        this.updateElement('#totalMessageCount', totalMessages);
        this.updateElement('#lastUpdateTime', new Date().toLocaleTimeString());
        
        // Update active connections display
        this.updateActiveConnectionsDisplay();
        
        // Emit status update for other components
        this.eventBus.emit('websocket:status-changed', { activeConnections: activeCount });
    }
    
    updateActiveConnectionsDisplay() {
        const connectionsDiv = this.container.querySelector('#liveActiveConnections');
        const { connectionStatus, servers } = this.state;
        
        if (!connectionsDiv) return;
        
        const totalConnections = Object.keys(connectionStatus).length;
        
        if (totalConnections === 0) {
            connectionsDiv.innerHTML = '<div class="text-gray-400 text-sm text-center py-4">No active connections</div>';
            return;
        }
        
        connectionsDiv.innerHTML = Object.entries(connectionStatus).map(([serverId, status]) => {
            const server = servers.find(s => s.serverId === serverId);
            const serverName = server ? server.serverName : `Server ${serverId}`;
            const serverRegion = server ? server.serverRegion : 'Unknown';
            
            return `
                <div class="flex items-center justify-between p-2 bg-gray-600 rounded mb-2">
                    <div class="flex-1">
                        <div class="text-sm font-medium">${this.escapeHtml(serverName)}</div>
                        <div class="text-xs text-gray-300">${serverId} - ${serverRegion}</div>
                        <div class="text-xs ${status.connected ? 'text-green-400' : 'text-red-400'}">
                            ${status.connected ? '● Live Connected' : '○ Disconnected'}
                        </div>
                    </div>
                    <button class="disconnect-server text-red-400 hover:text-red-300 text-xs p-1" 
                            data-server-id="${serverId}" title="Disconnect">✕</button>
                </div>
            `;
        }).join('');
        
        // Bind disconnect events
        const disconnectBtns = connectionsDiv.querySelectorAll('.disconnect-server');
        disconnectBtns.forEach(btn => {
            this.addEventListener(btn, 'click', (e) => {
                const serverId = e.target.dataset.serverId;
                this.disconnectServer(serverId);
            });
        });
    }
    
    async disconnectServer(serverId) {
        try {
            const result = await this.api.console.liveDisconnect({ serverId });
            
            if (result.success) {
                this.addConsoleMessage({
                    timestamp: new Date().toISOString(),
                    message: `🔌 Disconnected from server ${serverId}`,
                    type: 'system',
                    source: 'connection'
                });
                await this.loadConnectionStatus();
            } else {
                this.showNotification(`Failed to disconnect from server ${serverId}`, 'error');
            }
        } catch (error) {
            this.showNotification(`Disconnect error: ${error.message}`, 'error');
        }
    }
    
    async testLiveConsole() {
        try {
            const response = await this.api.console.liveTest();
            
            const alertMsg = `Live Console Test Results:
            
✅ Success: ${response.success}
🔌 WebSockets Available: ${response.websockets_available}
📡 Active Connections: ${response.total_connections || 0}
📨 Recent Messages: ${response.message_count || 0}

${response.recent_messages && response.recent_messages.length > 0 ? 
  'Latest Message: ' + (response.recent_messages[response.recent_messages.length-1].message || 'N/A').substring(0, 100) : 
  'No recent messages'}

${response.error ? 'Error: ' + response.error : 'Working!'}`;
            
            alert(alertMsg);
            // Live Console Test Data - console.log removed for production
            
            // Refresh console after test
            this.refreshConsoleWithLiveMessages();
            
        } catch (error) {
            alert(`Test Error: ${error.message}`);
            console.error('Test error:', error);
        }
    }
    
    handleLiveMessage(message) {
        // Handle incoming live messages
        this.addConsoleMessage({
            timestamp: message.timestamp,
            message: `📺 Live: ${message.message}`,
            type: 'live',
            source: 'websocket_live'
        });
    }
    
    getTypeIcon(type) {
        const icons = {
            'chat': '💬',
            'auth': '🔐',
            'save': '💾',
            'kill': '⚔️',
            'error': '❌',
            'warning': '⚠️',
            'command': '🔧',
            'player': '👥',
            'system': '🖥️',
            'event': '🎯',
            'ban': '🚫'
        };
        return icons[type] || '📋';
    }
    
    updateElement(selector, value) {
        const element = this.container.querySelector(selector);
        if (element) {
            element.textContent = value;
        }
    }
    
    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    showNotification(message, type = 'info') {
        this.eventBus.emit('notification:show', { message, type });
    }
    
    onReady() {
        super.onReady();
        
        // Start auto-refresh
        this.refreshInterval = setInterval(() => {
            this.refreshConsoleWithLiveMessages();
            this.loadConnectionStatus();
        }, this.options.autoRefreshInterval);
    }
    
    onDestroy() {
        // Clean up interval
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
        
        // Unsubscribe from events
        this.eventBus.off('servers:updated');
        this.eventBus.off('server:auto-connect');
        this.eventBus.off('websocket:message');
        this.eventBus.off('websocket:status-changed');
    }
}