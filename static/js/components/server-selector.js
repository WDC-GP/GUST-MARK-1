/**
 * Server Selector Component
 * =========================
 * Reusable server selection dropdown with server management
 */

class ServerSelector {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.options = {
            showAddServer: true,
            allowEmpty: false,
            placeholder: 'Select a server...',
            onServerChange: null,
            ...options
        };
        this.currentServer = null;
        this.servers = [];
        this.api = window.gustAPI;
        
        this.init();
    }

    async init() {
        this.render();
        await this.loadServers();
        this.attachEventListeners();
        
        // Restore previous selection
        const saved = localStorage.getItem('gust_current_server');
        if (saved && this.servers.some(s => s.id === saved)) {
            this.selectServer(saved);
        }
    }

    render() {
        this.container.innerHTML = 
            <div class="server-selector">
                <div class="relative">
                    <select id="serverSelect" class="w-full bg-gray-700 text-white p-3 rounded border border-gray-600 focus:border-purple-500 focus:outline-none">
                        <option value=""></option>
                    </select>
                    
                </div>
                
                <!-- Add Server Modal -->
                <div id="addServerModal" class="hidden fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center">
                    <div class="bg-gray-800 p-6 rounded-lg max-w-md w-full mx-4">
                        <h3 class="text-xl font-bold mb-4">Add New Server</h3>
                        <div class="space-y-4">
                            <div>
                                <label class="block text-sm font-medium mb-2">Server ID *</label>
                                <input type="text" id="newServerId" placeholder="e.g., 1234567" 
                                       class="w-full bg-gray-700 p-3 rounded border border-gray-600 focus:border-purple-500 focus:outline-none">
                            </div>
                            <div>
                                <label class="block text-sm font-medium mb-2">Server Name</label>
                                <input type="text" id="newServerName" placeholder="My Rust Server" 
                                       class="w-full bg-gray-700 p-3 rounded border border-gray-600 focus:border-purple-500 focus:outline-none">
                            </div>
                        </div>
                        <div class="flex space-x-3 mt-6">
                            <button id="saveServerBtn" class="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded flex-1">
                                Add Server
                            </button>
                            <button id="cancelServerBtn" class="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded flex-1">
                                Cancel
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        ;
    }

    async loadServers() {
        try {
            // Load from localStorage for now - in production this would come from API
            const stored = localStorage.getItem('gust_servers');
            this.servers = stored ? JSON.parse(stored) : [
                { id: 'server_001', name: 'Main Server', playerCount: 150 },
                { id: 'server_002', name: 'PvP Server', playerCount: 89 },
                { id: 'test_server', name: 'Test Server', playerCount: 5 }
            ];
            
            this.updateServerOptions();
        } catch (error) {
            console.error('Error loading servers:', error);
            this.servers = [];
        }
    }

    updateServerOptions() {
        const select = this.container.querySelector('#serverSelect');
        
        // Clear existing options except placeholder
        const placeholder = select.querySelector('option[value=""]');
        select.innerHTML = '';
        select.appendChild(placeholder);
        
        // Add server options
        this.servers.forEach(server => {
            const option = document.createElement('option');
            option.value = server.id;
            option.textContent = ${server.name} ( players);
            select.appendChild(option);
        });
    }

    attachEventListeners() {
        const select = this.container.querySelector('#serverSelect');
        const addBtn = this.container.querySelector('#addServerBtn');
        const modal = this.container.querySelector('#addServerModal');
        const saveBtn = this.container.querySelector('#saveServerBtn');
        const cancelBtn = this.container.querySelector('#cancelServerBtn');

        // Server selection change
        select?.addEventListener('change', (e) => {
            const serverId = e.target.value;
            this.selectServer(serverId);
        });

        // Add server button
        addBtn?.addEventListener('click', () => {
            this.showAddModal();
        });

        // Save new server
        saveBtn?.addEventListener('click', () => {
            this.saveNewServer();
        });

        // Cancel add server
        cancelBtn?.addEventListener('click', () => {
            this.hideAddModal();
        });

        // Close modal on backdrop click
        modal?.addEventListener('click', (e) => {
            if (e.target === modal) {
                this.hideAddModal();
            }
        });
    }

    selectServer(serverId) {
        if (!serverId && !this.options.allowEmpty) return;
        
        this.currentServer = serverId;
        this.api.setCurrentServer(serverId);
        
        // Update select value
        const select = this.container.querySelector('#serverSelect');
        if (select) select.value = serverId;
        
        // Trigger callback
        if (this.options.onServerChange) {
            const server = this.servers.find(s => s.id === serverId);
            this.options.onServerChange(serverId, server);
        }
        
        // Emit global event
        document.dispatchEvent(new CustomEvent('serverChanged', { 
            detail: { serverId, server: this.servers.find(s => s.id === serverId) }
        }));
    }

    showAddModal() {
        const modal = this.container.querySelector('#addServerModal');
        modal?.classList.remove('hidden');
        
        // Clear inputs
        this.container.querySelector('#newServerId').value = '';
        this.container.querySelector('#newServerName').value = '';
        
        // Focus first input
        this.container.querySelector('#newServerId')?.focus();
    }

    hideAddModal() {
        const modal = this.container.querySelector('#addServerModal');
        modal?.classList.add('hidden');
    }

    async saveNewServer() {
        const serverId = this.container.querySelector('#newServerId').value.trim();
        const serverName = this.container.querySelector('#newServerName').value.trim();

        if (!serverId) {
            alert('Please enter a server ID');
            return;
        }

        // Check for duplicates
        if (this.servers.some(s => s.id === serverId)) {
            alert('Server ID already exists');
            return;
        }

        // Add new server
        const newServer = {
            id: serverId,
            name: serverName || Server ,
            playerCount: 0,
            addedAt: new Date().toISOString()
        };

        this.servers.push(newServer);
        
        // Save to localStorage
        localStorage.setItem('gust_servers', JSON.stringify(this.servers));
        
        // Update UI
        this.updateServerOptions();
        this.selectServer(serverId);
        this.hideAddModal();
        
        console.log(Added server:  ());
    }

    getCurrentServer() {
        return this.currentServer;
    }

    getServers() {
        return this.servers;
    }
}

// Make available globally
window.ServerSelector = ServerSelector;

export { ServerSelector };
