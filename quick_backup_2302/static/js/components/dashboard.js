/**
 * Server Manager Component - Centralized Server Management
 * Handles adding, editing, deleting, and monitoring servers
 */
class ServerManagerComponent extends BaseComponent {
    constructor(containerId, options = {}) {
        super(containerId, options);
        this.api = options.api || window.App.api;
        this.eventBus = options.eventBus || window.App.eventBus;
        this.refreshInterval = null;
    }
    
    get defaultOptions() {
        return {
            ...super.defaultOptions,
            enableBulkOperations: true,
            autoRefresh: true,
            refreshInterval: 60000,
            pageSize: 10
        };
    }
    
    getInitialState() {
        return {
            ...super.getInitialState(),
            servers: [],
            selectedServers: new Set(),
            sortBy: 'serverName',
            sortDirection: 'asc',
            filterText: '',
            currentPage: 1,
            showAddModal: false,
            editingServer: null
        };
    }
    
    render() {
        this.container.innerHTML = `
            <div class="server-manager">
                <h2 class="text-3xl font-bold mb-6">🖥️ Server Manager</h2>
                <p class="text-gray-300 mb-6">Centralized server management - add servers here and they'll be available across all tabs.</p>
                
                <!-- Add Server Section -->
                <div class="bg-gray-800 p-6 rounded-lg mb-6">
                    <h3 class="text-xl font-semibold mb-4">Add New Server</h3>
                    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        <div>
                            <label class="block text-sm font-medium mb-2">Server ID *</label>
                            <input type="text" id="newServerId" placeholder="e.g., 1234567" 
                                   class="w-full bg-gray-700 p-3 rounded border border-gray-600 focus:border-purple-500">
                        </div>
                        <div>
                            <label class="block text-sm font-medium mb-2">Server Name *</label>
                            <input type="text" id="newServerName" placeholder="e.g., My Rust Server" 
                                   class="w-full bg-gray-700 p-3 rounded border border-gray-600 focus:border-purple-500">
                        </div>
                        <div>
                            <label class="block text-sm font-medium mb-2">Region *</label>
                            <select id="newServerRegion" class="w-full bg-gray-700 p-3 rounded border border-gray-600 focus:border-purple-500">
                                <option value="US">🇺🇸 United States</option>
                                <option value="EU">🇪🇺 Europe</option>
                                <option value="AS">🌏 Asia</option>
                            </select>
                        </div>
                        <div>
                            <label class="block text-sm font-medium mb-2">Server Type</label>
                            <select id="newServerType" class="w-full bg-gray-700 p-3 rounded border border-gray-600 focus:border-purple-500">
                                <option value="Standard">Standard</option>
                                <option value="Modded">Modded</option>
                                <option value="PvP">PvP Focused</option>
                                <option value="PvE">PvE Focused</option>
                                <option value="RP">Roleplay</option>
                                <option value="Vanilla+">Vanilla+</option>
                            </select>
                        </div>
                        <div class="md:col-span-2">
                            <label class="block text-sm font-medium mb-2">Description</label>
                            <input type="text" id="newServerDescription" placeholder="Optional description" 
                                   class="w-full bg-gray-700 p-3 rounded border border-gray-600 focus:border-purple-500">
                        </div>
                    </div>
                    <div class="flex items-center space-x-4 mt-4">
                        <button id="addServerBtn" class="bg-purple-600 hover:bg-purple-700 px-6 py-3 rounded font-medium">
                            Add Server
                        </button>
                        <button id="clearFormBtn" class="bg-gray-600 hover:bg-gray-700 px-4 py-3 rounded">
                            Clear
                        </button>
                    </div>
                </div>
                
                <!-- Server Management Section -->
                <div class="bg-gray-800 p-6 rounded-lg">
                    <div class="flex items-center justify-between mb-6">
                        <h3 class="text-xl font-semibold">Managed Servers</h3>
                        <div class="flex items-center space-x-4">
                            <input type="text" id="serverFilter" placeholder="Filter servers..." 
                                   class="bg-gray-700 p-2 rounded border border-gray-600 focus:border-purple-500">
                            <button id="refreshServersBtn" class="bg-blue-600 hover:bg-blue-700 px-3 py-2 rounded text-sm">
                                Refresh
                            </button>
                            <button id="bulkActionsBtn" class="bg-orange-600 hover:bg-orange-700 px-3 py-2 rounded text-sm hidden">
                                Bulk Actions
                            </button>
                        </div>
                    </div>
                    
                    <!-- Server List -->
                    <div id="serversList" class="space-y-3">
                        <div class="text-gray-400 text-center py-8">
                            <div class="text-4xl mb-4">🖥️</div>
                            <div>No servers added yet</div>
                            <div class="text-sm mt-2">Add your first server above to get started</div>
                        </div>
                    </div>
                    
                    <!-- Pagination -->
                    <div id="pagination" class="flex justify-center mt-6 hidden">
                        <div class="flex space-x-2">
                            <button id="prevPageBtn" class="px-3 py-1 bg-gray-700 rounded text-sm">Previous</button>
                            <span id="pageInfo" class="px-3 py-1 text-sm">Page 1 of 1</span>
                            <button id="nextPageBtn" class="px-3 py-1 bg-gray-700 rounded text-sm">Next</button>
                        </div>
                    </div>
                </div>
                
                <!-- Bulk Actions Modal -->
                <div id="bulkActionsModal" class="fixed inset-0 bg-black bg-opacity-50 hidden z-50">
                    <div class="flex items-center justify-center h-full">
                        <div class="bg-gray-800 p-6 rounded-lg w-96">
                            <h3 class="text-lg font-semibold mb-4">Bulk Actions</h3>
                            <div class="space-y-3">
                                <button class="w-full bg-blue-600 hover:bg-blue-700 p-2 rounded" data-action="activate">
                                    Activate Selected
                                </button>
                                <button class="w-full bg-yellow-600 hover:bg-yellow-700 p-2 rounded" data-action="deactivate">
                                    Deactivate Selected
                                </button>
                                <button class="w-full bg-green-600 hover:bg-green-700 p-2 rounded" data-action="ping">
                                    Ping Selected
                                </button>
                                <button class="w-full bg-red-600 hover:bg-red-700 p-2 rounded" data-action="delete">
                                    Delete Selected
                                </button>
                            </div>
                            <div class="flex justify-end mt-4">
                                <button id="closeBulkModal" class="bg-gray-600 hover:bg-gray-700 px-4 py-2 rounded">
                                    Cancel
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    bindEvents() {
        // Form events
        const addBtn = this.container.querySelector('#addServerBtn');
        const clearBtn = this.container.querySelector('#clearFormBtn');
        const refreshBtn = this.container.querySelector('#refreshServersBtn');
        const filterInput = this.container.querySelector('#serverFilter');
        
        this.addEventListener(addBtn, 'click', () => this.addNewServer());
        this.addEventListener(clearBtn, 'click', () => this.clearServerForm());
        this.addEventListener(refreshBtn, 'click', () => this.loadData());
        this.addEventListener(filterInput, 'input', (e) => this.filterServers(e.target.value));
        
        // Bulk actions
        const bulkBtn = this.container.querySelector('#bulkActionsBtn');
        const bulkModal = this.container.querySelector('#bulkActionsModal');
        const closeBulkBtn = this.container.querySelector('#closeBulkModal');
        
        this.addEventListener(bulkBtn, 'click', () => this.showBulkActionsModal());
        this.addEventListener(closeBulkBtn, 'click', () => this.hideBulkActionsModal());
        
        // Bulk action buttons
        const bulkActionBtns = this.container.querySelectorAll('[data-action]');
        bulkActionBtns.forEach(btn => {
            this.addEventListener(btn, 'click', (e) => {
                const action = e.target.dataset.action;
                this.performBulkAction(action);
            });
        });
        
        // Pagination
        const prevBtn = this.container.querySelector('#prevPageBtn');
        const nextBtn = this.container.querySelector('#nextPageBtn');
        
        this.addEventListener(prevBtn, 'click', () => this.previousPage());
        this.addEventListener(nextBtn, 'click', () => this.nextPage());
        
        // Form enter key support
        const formInputs = ['newServerId', 'newServerName', 'newServerDescription'];
        formInputs.forEach(inputId => {
            const input = this.container.querySelector(`#${inputId}`);
            if (input) {
                this.addEventListener(input, 'keypress', (e) => {
                    if (e.key === 'Enter') this.addNewServer();
                });
            }
        });
        
        // Listen for server events from other components
        this.eventBus.on('server:connect-console', (data) => this.handleConsoleConnect(data));
        this.eventBus.on('websocket:status-changed', () => this.renderServerList());
    }
    
    async loadData() {
        try {
            this.setState({ loading: true, error: null });
            const servers = await this.api.servers.list();
            this.setState({ servers, loading: false });
            this.renderServerList();
            
            // Emit event for other components
            this.eventBus.emit('servers:updated', { servers });
            
        } catch (error) {
            this.handleError(error);
        }
    }
    
    async addNewServer() {
        const serverId = this.container.querySelector('#newServerId').value.trim();
        const serverName = this.container.querySelector('#newServerName').value.trim();
        const serverRegion = this.container.querySelector('#newServerRegion').value;
        const serverType = this.container.querySelector('#newServerType').value;
        const description = this.container.querySelector('#newServerDescription').value.trim();
        
        if (!serverId || !serverName) {
            this.showNotification('Please fill in Server ID and Server Name (required fields)', 'error');
            return;
        }
        
        // Validate server ID format
        if (!/^\d+$/.test(serverId)) {
            this.showNotification('Server ID must be numeric', 'error');
            return;
        }
        
        // Check if server already exists
        if (this.state.servers.find(s => s.serverId === serverId)) {
            this.showNotification('A server with this ID already exists!', 'error');
            return;
        }
        
        try {
            const result = await this.api.servers.add({
                serverId,
                serverName,
                serverRegion,
                serverType,
                description
            });
            
            if (result.success) {
                this.showNotification('✅ Server added successfully!', 'success');
                this.clearServerForm();
                await this.loadData();
                
                // Emit event for other components
                this.eventBus.emit('server:added', { 
                    server: { serverId, serverName, serverRegion, serverType, description }
                });
                
                // Auto-connect to live console if available
                this.eventBus.emit('server:auto-connect', { serverId, serverRegion });
                
            } else {
                this.showNotification('❌ Failed to add server: ' + (result.error || 'Unknown error'), 'error');
            }
        } catch (error) {
            this.showNotification('❌ Error adding server: ' + error.message, 'error');
        }
    }
    
    clearServerForm() {
        this.container.querySelector('#newServerId').value = '';
        this.container.querySelector('#newServerName').value = '';
        this.container.querySelector('#newServerDescription').value = '';
        this.container.querySelector('#newServerRegion').value = 'US';
        this.container.querySelector('#newServerType').value = 'Standard';
    }
    
    renderServerList() {
        const container = this.container.querySelector('#serversList');
        const filteredServers = this.getFilteredServers();
        const paginatedServers = this.getPaginatedServers(filteredServers);
        
        if (filteredServers.length === 0) {
            container.innerHTML = `
                <div class="text-gray-400 text-center py-8">
                    <div class="text-4xl mb-4">🔍</div>
                    <div>No servers found</div>
                    <div class="text-sm mt-2">Add a new server above to get started</div>
                </div>
            `;
            this.container.querySelector('#pagination').classList.add('hidden');
            return;
        }
        
        container.innerHTML = paginatedServers.map(server => this.renderServerCard(server)).join('');
        this.updatePagination(filteredServers.length);
        this.bindServerCardEvents();
        this.updateBulkActionsVisibility();
    }
    
    renderServerCard(server) {
        const isSelected = this.state.selectedServers.has(server.serverId);
        
        return `
            <div class="bg-gray-700 p-4 rounded-lg border border-gray-600 ${isSelected ? 'ring-2 ring-purple-500' : ''}">
                <div class="flex items-center justify-between">
                    <div class="flex items-center space-x-4">
                        ${this.options.enableBulkOperations ? `
                            <input type="checkbox" class="server-checkbox" 
                                   data-server-id="${server.serverId}" 
                                   ${isSelected ? 'checked' : ''}>
                        ` : ''}
                        <div>
                            <div class="flex items-center space-x-2">
                                <h4 class="font-semibold text-lg">${this.escapeHtml(server.serverName)}</h4>
                                ${server.isFavorite ? '<span class="text-yellow-400">⭐</span>' : ''}
                                ${!server.isActive ? '<span class="text-red-400 text-xs bg-red-900 px-2 py-1 rounded">INACTIVE</span>' : ''}
                            </div>
                            <div class="text-sm text-gray-300">
                                ID: ${server.serverId} | Region: ${server.serverRegion} | Type: ${server.serverType || 'Standard'}
                            </div>
                            ${server.description ? `<div class="text-xs text-gray-400 mt-1">${this.escapeHtml(server.description)}</div>` : ''}
                        </div>
                    </div>
                    
                    <div class="flex items-center space-x-2">
                        <!-- Status Indicator -->
                        <div class="flex items-center space-x-2">
                            <span class="text-xs px-2 py-1 rounded ${this.getStatusClass(server.status)}">
                                ${this.getStatusText(server.status)}
                            </span>
                            ${server.lastPing ? `<span class="text-xs text-gray-400">Pinged: ${new Date(server.lastPing).toLocaleTimeString()}</span>` : ''}
                        </div>
                        
                        <!-- Quick Actions -->
                        <button class="bg-blue-600 hover:bg-blue-700 px-2 py-1 rounded text-xs" 
                                data-action="ping" data-server-id="${server.serverId}" title="Ping Server">
                            📡
                        </button>
                        <button class="bg-green-600 hover:bg-green-700 px-2 py-1 rounded text-xs" 
                                data-action="console" data-server-id="${server.serverId}" title="Open Console">
                            📺
                        </button>
                        <button class="bg-yellow-600 hover:bg-yellow-700 px-2 py-1 rounded text-xs" 
                                data-action="edit" data-server-id="${server.serverId}" title="Edit Server">
                            ✏️
                        </button>
                        <button class="bg-red-600 hover:bg-red-700 px-2 py-1 rounded text-xs" 
                                data-action="delete" data-server-id="${server.serverId}" title="Delete Server">
                            🗑️
                        </button>
                    </div>
                </div>
            </div>
        `;
    }
    
    bindServerCardEvents() {
        // Checkbox events
        const checkboxes = this.container.querySelectorAll('.server-checkbox');
        checkboxes.forEach(checkbox => {
            this.addEventListener(checkbox, 'change', (e) => {
                const serverId = e.target.dataset.serverId;
                if (e.target.checked) {
                    this.state.selectedServers.add(serverId);
                } else {
                    this.state.selectedServers.delete(serverId);
                }
                this.updateBulkActionsVisibility();
            });
        });
        
        // Action button events
        const actionButtons = this.container.querySelectorAll('[data-action][data-server-id]');
        actionButtons.forEach(button => {
            const action = button.dataset.action;
            const serverId = button.dataset.serverId;
            
            this.addEventListener(button, 'click', () => {
                this.handleServerAction(action, serverId);
            });
        });
    }
    
    async handleServerAction(action, serverId) {
        const server = this.state.servers.find(s => s.serverId === serverId);
        
        switch (action) {
            case 'ping':
                await this.pingServer(serverId);
                break;
            case 'console':
                this.eventBus.emit('navigation:goto', { route: 'console', serverId });
                break;
            case 'edit':
                this.editServer(server);
                break;
            case 'delete':
                if (confirm(`Are you sure you want to delete "${server.serverName}"?\n\nThis action cannot be undone.`)) {
                    await this.deleteServer(serverId);
                }
                break;
        }
    }
    
    async pingServer(serverId) {
        try {
            const result = await this.api.servers.ping(serverId);
            if (result.success) {
                // Update server status in state
                const servers = this.state.servers.map(server => 
                    server.serverId === serverId 
                        ? { ...server, status: result.status, lastPing: new Date().toISOString() }
                        : server
                );
                this.setState({ servers });
                this.renderServerList();
                this.showNotification(`Server ${serverId} pinged: ${result.status}`, 'info');
            }
        } catch (error) {
            this.showNotification('Failed to ping server: ' + error.message, 'error');
        }
    }
    
    editServer(server) {
        // Pre-fill form with server data
        this.container.querySelector('#newServerId').value = server.serverId;
        this.container.querySelector('#newServerName').value = server.serverName;
        this.container.querySelector('#newServerRegion').value = server.serverRegion;
        this.container.querySelector('#newServerType').value = server.serverType || 'Standard';
        this.container.querySelector('#newServerDescription').value = server.description || '';
        
        // Update button text and behavior
        const addBtn = this.container.querySelector('#addServerBtn');
        addBtn.textContent = 'Update Server';
        addBtn.dataset.editing = server.serverId;
        
        // Scroll to form
        this.container.querySelector('.server-manager').scrollIntoView({ behavior: 'smooth' });
    }
    
    async deleteServer(serverId) {
        try {
            const result = await this.api.servers.delete(serverId);
            if (result.success) {
                // Remove from state
                const servers = this.state.servers.filter(s => s.serverId !== serverId);
                this.setState({ servers });
                this.renderServerList();
                
                // Emit events
                this.eventBus.emit('server:deleted', { serverId });
                this.eventBus.emit('servers:updated', { servers });
                
                this.showNotification('✅ Server deleted successfully', 'success');
            }
        } catch (error) {
            this.showNotification('❌ Failed to delete server: ' + error.message, 'error');
        }
    }
    
    getFilteredServers() {
        const { servers, filterText, sortBy, sortDirection } = this.state;
        let filtered = servers;
        
        if (filterText) {
            filtered = filtered.filter(server => 
                server.serverName.toLowerCase().includes(filterText.toLowerCase()) ||
                server.serverId.includes(filterText) ||
                (server.description && server.description.toLowerCase().includes(filterText.toLowerCase()))
            );
        }
        
        filtered.sort((a, b) => {
            const aVal = a[sortBy] || '';
            const bVal = b[sortBy] || '';
            const result = aVal.toString().localeCompare(bVal.toString());
            return sortDirection === 'desc' ? -result : result;
        });
        
        return filtered;
    }
    
    getPaginatedServers(servers) {
        const { currentPage } = this.state;
        const { pageSize } = this.options;
        const startIndex = (currentPage - 1) * pageSize;
        const endIndex = startIndex + pageSize;
        return servers.slice(startIndex, endIndex);
    }
    
    updatePagination(totalServers) {
        const { currentPage } = this.state;
        const { pageSize } = this.options;
        const totalPages = Math.ceil(totalServers / pageSize);
        
        const pagination = this.container.querySelector('#pagination');
        const pageInfo = this.container.querySelector('#pageInfo');
        const prevBtn = this.container.querySelector('#prevPageBtn');
        const nextBtn = this.container.querySelector('#nextPageBtn');
        
        if (totalPages <= 1) {
            pagination.classList.add('hidden');
            return;
        }
        
        pagination.classList.remove('hidden');
        pageInfo.textContent = `Page ${currentPage} of ${totalPages}`;
        prevBtn.disabled = currentPage === 1;
        nextBtn.disabled = currentPage === totalPages;
    }
    
    previousPage() {
        if (this.state.currentPage > 1) {
            this.setState({ currentPage: this.state.currentPage - 1 });
            this.renderServerList();
        }
    }
    
    nextPage() {
        const totalPages = Math.ceil(this.getFilteredServers().length / this.options.pageSize);
        if (this.state.currentPage < totalPages) {
            this.setState({ currentPage: this.state.currentPage + 1 });
            this.renderServerList();
        }
    }
    
    filterServers(filterText) {
        this.setState({ filterText, currentPage: 1 });
        this.renderServerList();
    }
    
    updateBulkActionsVisibility() {
        const bulkBtn = this.container.querySelector('#bulkActionsBtn');
        const hasSelected = this.state.selectedServers.size > 0;
        
        if (hasSelected) {
            bulkBtn.classList.remove('hidden');
            bulkBtn.textContent = `Bulk Actions (${this.state.selectedServers.size})`;
        } else {
            bulkBtn.classList.add('hidden');
        }
    }
    
    showBulkActionsModal() {
        const modal = this.container.querySelector('#bulkActionsModal');
        modal.classList.remove('hidden');
    }
    
    hideBulkActionsModal() {
        const modal = this.container.querySelector('#bulkActionsModal');
        modal.classList.add('hidden');
    }
    
    async performBulkAction(action) {
        const selectedIds = Array.from(this.state.selectedServers);
        if (selectedIds.length === 0) return;
        
        if (action === 'delete' && !confirm(`Delete ${selectedIds.length} servers? This cannot be undone.`)) {
            return;
        }
        
        try {
            const result = await this.api.servers.bulkAction({
                action,
                serverIds: selectedIds
            });
            
            if (result.success) {
                this.showNotification(`✅ Bulk ${action} completed`, 'success');
                this.setState({ selectedServers: new Set() });
                await this.loadData();
            } else {
                this.showNotification(`❌ Bulk ${action} failed`, 'error');
            }
        } catch (error) {
            this.showNotification(`❌ Bulk ${action} error: ${error.message}`, 'error');
        }
        
        this.hideBulkActionsModal();
    }
    
    getStatusClass(status) {
        const classes = {
            online: 'bg-green-800 text-green-200',
            offline: 'bg-red-800 text-red-200',
            unknown: 'bg-gray-700 text-gray-300'
        };
        return classes[status] || classes.unknown;
    }
    
    getStatusText(status) {
        const texts = {
            online: '🟢 Online',
            offline: '🔴 Offline',
            unknown: '⚪ Unknown'
        };
        return texts[status] || texts.unknown;
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    showNotification(message, type = 'info') {
        this.eventBus.emit('notification:show', { message, type });
    }
    
    handleConsoleConnect(data) {
        this.showNotification(`Connecting to console for server ${data.serverId}`, 'info');
    }
    
    onReady() {
        super.onReady();
        
        // Start auto-refresh if enabled
        if (this.options.autoRefresh) {
            this.refreshInterval = setInterval(() => {
                this.loadData();
            }, this.options.refreshInterval);
        }
    }
    
    onDestroy() {
        // Clean up interval
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
        
        // Unsubscribe from events
        this.eventBus.off('server:connect-console');
        this.eventBus.off('websocket:status-changed');
    }
}