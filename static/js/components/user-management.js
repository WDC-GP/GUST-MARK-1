/**
 * User Management Component
 * Handles user administration operations including bans, item giving, and moderation
 */
class UserManagementComponent extends BaseComponent {
    constructor(containerId, options = {}) {
        super(containerId, options);
        this.api = options.api || window.App.api;
        this.eventBus = options.eventBus || window.App.eventBus;
        this.modal = null;
        this.dataTable = null;
    }
    
    get defaultOptions() {
        return {
            ...super.defaultOptions,
            enableSearch: true,
            enableBulkActions: true,
            pageSize: 20
        };
    }
    
    getInitialState() {
        return {
            ...super.getInitialState(),
            bans: [],
            users: [],
            selectedUsers: new Set(),
            searchQuery: '',
            sortBy: 'bannedAt',
            sortDirection: 'desc',
            currentPage: 1,
            totalPages: 1,
            servers: [],
            showBanModal: false,
            showGiveItemModal: false
        };
    }
    
    render() {
        this.container.innerHTML = `
            <div class="user-management">
                <!-- Header Section -->
                <div class="user-management__header">
                    <h2 class="text-3xl font-bold mb-6">User Management</h2>
                    <div class="flex flex-wrap gap-4 mb-6">
                        <button id="temp-ban-btn" class="btn btn-warning">
                            <i class="icon-ban"></i> Temporary Ban
                        </button>
                        <button id="perm-ban-btn" class="btn btn-danger">
                            <i class="icon-ban-permanent"></i> Permanent Ban
                        </button>
                        <button id="give-item-btn" class="btn btn-success">
                            <i class="icon-gift"></i> Give Item
                        </button>
                        <button id="kick-user-btn" class="btn btn-secondary">
                            <i class="icon-kick"></i> Kick User
                        </button>
                        <button id="teleport-btn" class="btn btn-info">
                            <i class="icon-teleport"></i> Teleport
                        </button>
                    </div>
                </div>
                
                <!-- Quick Actions Panel -->
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
                    <!-- Temporary Ban Panel -->
                    <div class="bg-gray-800 p-6 rounded-lg">
                        <h3 class="text-xl font-semibold mb-4 text-yellow-400">
                            <i class="icon-clock"></i> Temporary Ban User
                        </h3>
                        <form id="temp-ban-form" class="space-y-4">
                            <div>
                                <label class="block text-sm font-medium mb-2">User ID *</label>
                                <input type="text" id="ban-user-id" 
                                       placeholder="Enter Steam ID or username"
                                       class="form-input w-full" required>
                            </div>
                            <div>
                                <label class="block text-sm font-medium mb-2">Server *</label>
                                <select id="ban-server-select" class="form-select w-full" required>
                                    <option value="">Choose a server...</option>
                                </select>
                            </div>
                            <div class="grid grid-cols-2 gap-4">
                                <div>
                                    <label class="block text-sm font-medium mb-2">Duration (minutes) *</label>
                                    <input type="number" id="ban-duration" 
                                           placeholder="e.g., 60" min="1" max="10080"
                                           class="form-input w-full" required>
                                </div>
                                <div>
                                    <label class="block text-sm font-medium mb-2">Quick Duration</label>
                                    <select id="quick-duration" class="form-select w-full">
                                        <option value="">Custom</option>
                                        <option value="30">30 minutes</option>
                                        <option value="60">1 hour</option>
                                        <option value="180">3 hours</option>
                                        <option value="360">6 hours</option>
                                        <option value="720">12 hours</option>
                                        <option value="1440">24 hours</option>
                                        <option value="4320">3 days</option>
                                        <option value="10080">1 week</option>
                                    </select>
                                </div>
                            </div>
                            <div>
                                <label class="block text-sm font-medium mb-2">Reason *</label>
                                <textarea id="ban-reason" 
                                         placeholder="Enter ban reason..."
                                         class="form-textarea w-full h-20" required></textarea>
                            </div>
                            <button type="submit" class="btn btn-warning w-full">
                                Apply Temporary Ban
                            </button>
                        </form>
                    </div>
                    
                    <!-- Give Items Panel -->
                    <div class="bg-gray-800 p-6 rounded-lg">
                        <h3 class="text-xl font-semibold mb-4 text-green-400">
                            <i class="icon-gift"></i> Give Items to Player
                        </h3>
                        <form id="give-item-form" class="space-y-4">
                            <div>
                                <label class="block text-sm font-medium mb-2">Player ID *</label>
                                <input type="text" id="give-player-id" 
                                       placeholder="Enter Steam ID or username"
                                       class="form-input w-full" required>
                            </div>
                            <div>
                                <label class="block text-sm font-medium mb-2">Server *</label>
                                <select id="give-server-select" class="form-select w-full" required>
                                    <option value="">Choose a server...</option>
                                </select>
                            </div>
                            <div class="grid grid-cols-2 gap-4">
                                <div>
                                    <label class="block text-sm font-medium mb-2">Item *</label>
                                    <select id="give-item-select" class="form-select w-full" required>
                                        <option value="">Choose item...</option>
                                        <optgroup label="Resources">
                                            <option value="scrap">Scrap</option>
                                            <option value="metal.fragments">Metal Fragments</option>
                                            <option value="metal.refined">High Quality Metal</option>
                                            <option value="wood">Wood</option>
                                            <option value="stones">Stone</option>
                                            <option value="cloth">Cloth</option>
                                            <option value="leather">Leather</option>
                                        </optgroup>
                                        <optgroup label="Weapons">
                                            <option value="rifle.ak">AK-47</option>
                                            <option value="rifle.lr300">LR-300</option>
                                            <option value="rifle.bolt">Bolt Action Rifle</option>
                                            <option value="smg.mp5">MP5</option>
                                            <option value="pistol.m92">M92 Pistol</option>
                                        </optgroup>
                                        <optgroup label="Medical">
                                            <option value="medical.syringe">Medical Syringe</option>
                                            <option value="medical.bandage">Bandage</option>
                                            <option value="medical.largemedkit">Large Medkit</option>
                                        </optgroup>
                                        <optgroup label="Tools">
                                            <option value="tool.hatchet">Hatchet</option>
                                            <option value="tool.pickaxe">Pickaxe</option>
                                            <option value="tool.hammer">Hammer</option>
                                        </optgroup>
                                    </select>
                                </div>
                                <div>
                                    <label class="block text-sm font-medium mb-2">Amount *</label>
                                    <input type="number" id="give-amount" 
                                           placeholder="e.g., 1000" min="1" max="10000"
                                           class="form-input w-full" required>
                                </div>
                            </div>
                            <div>
                                <label class="block text-sm font-medium mb-2">Custom Item Name</label>
                                <input type="text" id="give-custom-item" 
                                       placeholder="Enter custom item shortname..."
                                       class="form-input w-full">
                                <div class="text-xs text-gray-400 mt-1">
                                    Leave blank to use selected item above
                                </div>
                            </div>
                            <button type="submit" class="btn btn-success w-full">
                                Give Item to Player
                            </button>
                        </form>
                    </div>
                </div>
                
                <!-- Active Bans Section -->
                <div class="bg-gray-800 p-6 rounded-lg mb-8">
                    <div class="flex items-center justify-between mb-6">
                        <h3 class="text-xl font-semibold">Active Bans</h3>
                        <div class="flex items-center space-x-4">
                            <div class="relative">
                                <input type="text" id="ban-search" 
                                       placeholder="Search bans..."
                                       class="form-input pl-10">
                                <i class="icon-search absolute left-3 top-3 text-gray-400"></i>
                            </div>
                            <button id="refresh-bans-btn" class="btn btn-secondary">
                                <i class="icon-refresh"></i> Refresh
                            </button>
                        </div>
                    </div>
                    
                    <div id="bans-table-container">
                        <!-- Data table will be rendered here -->
                    </div>
                </div>
                
                <!-- User History Section -->
                <div class="bg-gray-800 p-6 rounded-lg">
                    <h3 class="text-xl font-semibold mb-4">User Action History</h3>
                    <div class="flex items-center space-x-4 mb-4">
                        <input type="text" id="history-user-search" 
                               placeholder="Enter user ID to view history..."
                               class="form-input flex-1">
                        <button id="load-history-btn" class="btn btn-primary">
                            Load History
                        </button>
                    </div>
                    
                    <div id="user-history-container" class="hidden">
                        <!-- User history will be displayed here -->
                    </div>
                </div>
                
                <!-- Bulk Actions Modal -->
                <div id="bulk-actions-modal" class="modal">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h4 class="modal-title">Bulk Actions</h4>
                            <button class="modal-close">&times;</button>
                        </div>
                        <div class="modal-body">
                            <p>Select an action to perform on <span id="selected-count">0</span> selected users:</p>
                            <div class="flex flex-wrap gap-4 mt-4">
                                <button id="bulk-unban-btn" class="btn btn-success">
                                    Unban Selected
                                </button>
                                <button id="bulk-extend-ban-btn" class="btn btn-warning">
                                    Extend Bans
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    bindEvents() {
        // Form submissions
        const tempBanForm = this.container.querySelector('#temp-ban-form');
        const giveItemForm = this.container.querySelector('#give-item-form');
        
        this.addEventListener(tempBanForm, 'submit', (e) => this.handleTempBan(e));
        this.addEventListener(giveItemForm, 'submit', (e) => this.handleGiveItem(e));
        
        // Quick duration selector
        const quickDuration = this.container.querySelector('#quick-duration');
        this.addEventListener(quickDuration, 'change', (e) => {
            if (e.target.value) {
                document.getElementById('ban-duration').value = e.target.value;
            }
        });
        
        // Custom item toggle
        const customItemInput = this.container.querySelector('#give-custom-item');
        const itemSelect = this.container.querySelector('#give-item-select');
        
        this.addEventListener(customItemInput, 'input', (e) => {
            if (e.target.value.trim()) {
                itemSelect.disabled = true;
                itemSelect.required = false;
            } else {
                itemSelect.disabled = false;
                itemSelect.required = true;
            }
        });
        
        // Search functionality
        const banSearch = this.container.querySelector('#ban-search');
        this.addEventListener(banSearch, 'input', 
            this.debounce((e) => this.filterBans(e.target.value), 300)
        );
        
        // Action buttons
        const refreshBansBtn = this.container.querySelector('#refresh-bans-btn');
        const loadHistoryBtn = this.container.querySelector('#load-history-btn');
        
        this.addEventListener(refreshBansBtn, 'click', () => this.loadBans());
        this.addEventListener(loadHistoryBtn, 'click', () => this.loadUserHistory());
        
        // Global events
        this.eventBus.on('servers:updated', (data) => this.updateServerDropdowns(data.servers));
        this.eventBus.on('user:banned', () => this.loadBans());
        this.eventBus.on('user:unbanned', () => this.loadBans());
    }
    
    async loadData() {
        try {
            this.setState({ loading: true, error: null });
            
            // Load servers and bans in parallel
            const [servers, bans] = await Promise.all([
                this.api.servers.list(),
                this.api.users.getBans()
            ]);
            
            this.setState({ 
                servers, 
                bans, 
                loading: false 
            });
            
            this.updateServerDropdowns(servers);
            this.renderBansTable();
            
        } catch (error) {
            this.handleError(error);
        }
    }
    
    updateServerDropdowns(servers) {
        const selectors = [
            '#ban-server-select',
            '#give-server-select'
        ];
        
        selectors.forEach(selector => {
            const dropdown = this.container.querySelector(selector);
            if (!dropdown) return;
            
            const currentValue = dropdown.value;
            
            // Clear and rebuild options
            dropdown.innerHTML = '<option value="">Choose a server...</option>';
            
            servers.filter(server => server.isActive).forEach(server => {
                const option = document.createElement('option');
                option.value = server.serverId;
                option.textContent = `${server.serverName} (${server.serverId})`;
                dropdown.appendChild(option);
            });
            
            // Restore selection
            if (currentValue) {
                dropdown.value = currentValue;
            }
        });
    }
    
    async handleTempBan(event) {
        event.preventDefault();
        
        const formData = new FormData(event.target);
        const banData = {
            userId: formData.get('user-id') || document.getElementById('ban-user-id').value,
            serverId: document.getElementById('ban-server-select').value,
            duration: parseInt(document.getElementById('ban-duration').value),
            reason: document.getElementById('ban-reason').value
        };
        
        if (!this.validateBanData(banData)) {
            return;
        }
        
        try {
            this.showLoader();
            const result = await this.api.users.tempBan(banData);
            
            if (result.success) {
                this.showNotification('User banned successfully', 'success');
                this.clearForm('#temp-ban-form');
                this.eventBus.emit('user:banned', { banData, result });
                await this.loadBans();
            } else {
                this.showNotification(result.error || 'Ban failed', 'error');
            }
        } catch (error) {
            this.handleError(error);
        } finally {
            this.hideLoader();
        }
    }
    
    async handleGiveItem(event) {
        event.preventDefault();
        
        const customItem = document.getElementById('give-custom-item').value.trim();
        const selectedItem = document.getElementById('give-item-select').value;
        
        const itemData = {
            playerId: document.getElementById('give-player-id').value,
            serverId: document.getElementById('give-server-select').value,
            item: customItem || selectedItem,
            amount: parseInt(document.getElementById('give-amount').value)
        };
        
        if (!this.validateItemData(itemData)) {
            return;
        }
        
        try {
            this.showLoader();
            const result = await this.api.users.giveItem(itemData);
            
            if (result.success) {
                this.showNotification('Item given successfully', 'success');
                this.clearForm('#give-item-form');
                this.eventBus.emit('user:item-given', { itemData, result });
            } else {
                this.showNotification(result.error || 'Give item failed', 'error');
            }
        } catch (error) {
            this.handleError(error);
        } finally {
            this.hideLoader();
        }
    }
    
    validateBanData(data) {
        if (!data.userId) {
            this.showNotification('User ID is required', 'error');
            return false;
        }
        
        if (!data.serverId) {
            this.showNotification('Please select a server', 'error');
            return false;
        }
        
        if (!data.duration || data.duration < 1 || data.duration > 10080) {
            this.showNotification('Duration must be between 1 and 10080 minutes', 'error');
            return false;
        }
        
        if (!data.reason || data.reason.length < 3) {
            this.showNotification('Ban reason must be at least 3 characters', 'error');
            return false;
        }
        
        return true;
    }
    
    validateItemData(data) {
        if (!data.playerId) {
            this.showNotification('Player ID is required', 'error');
            return false;
        }
        
        if (!data.serverId) {
            this.showNotification('Please select a server', 'error');
            return false;
        }
        
        if (!data.item) {
            this.showNotification('Please select or enter an item', 'error');
            return false;
        }
        
        if (!data.amount || data.amount < 1 || data.amount > 10000) {
            this.showNotification('Amount must be between 1 and 10000', 'error');
            return false;
        }
        
        return true;
    }
    
    async loadBans() {
        try {
            const bans = await this.api.users.getBans();
            this.setState({ bans });
            this.renderBansTable();
        } catch (error) {
            this.handleError(error);
        }
    }
    
    renderBansTable() {
        const container = this.container.querySelector('#bans-table-container');
        
        if (!this.dataTable) {
            this.dataTable = new DataTable(container, {
                columns: [
                    { key: 'userId', label: 'User ID', sortable: true },
                    { key: 'serverId', label: 'Server', sortable: true },
                    { key: 'reason', label: 'Reason', sortable: false },
                    { 
                        key: 'duration', 
                        label: 'Duration', 
                        sortable: true,
                        formatter: (value, row) => {
                            if (row.type === 'permanent') return 'Permanent';
                            return `${value} minutes`;
                        }
                    },
                    { 
                        key: 'bannedAt', 
                        label: 'Banned At', 
                        sortable: true,
                        formatter: (value) => new Date(value).toLocaleString()
                    },
                    {
                        key: 'actions',
                        label: 'Actions',
                        sortable: false,
                        formatter: (value, row) => `
                            <button class="btn btn-sm btn-success" 
                                    onclick="window.userManagement.unbanUser('${row.banId}')">
                                Unban
                            </button>
                        `
                    }
                ],
                data: this.state.bans,
                selectable: this.options.enableBulkActions,
                onSelectionChange: (selected) => this.handleBanSelection(selected)
            });
        } else {
            this.dataTable.updateData(this.state.bans);
        }
        
        // Make unbanUser globally accessible for button clicks
        window.userManagement = this;
    }
    
    async unbanUser(banId) {
        if (!confirm('Are you sure you want to unban this user?')) {
            return;
        }
        
        try {
            const ban = this.state.bans.find(b => b.banId === banId);
            if (!ban) return;
            
            const result = await this.api.users.unban({
                userId: ban.userId,
                serverId: ban.serverId
            });
            
            if (result.success) {
                this.showNotification('User unbanned successfully', 'success');
                this.eventBus.emit('user:unbanned', { banId, ban });
                await this.loadBans();
            } else {
                this.showNotification(result.error || 'Unban failed', 'error');
            }
        } catch (error) {
            this.handleError(error);
        }
    }
    
    async loadUserHistory() {
        const userId = document.getElementById('history-user-search').value.trim();
        
        if (!userId) {
            this.showNotification('Please enter a user ID', 'error');
            return;
        }
        
        try {
            this.showLoader();
            const history = await this.api.users.getHistory(userId);
            this.renderUserHistory(history, userId);
            
            const container = this.container.querySelector('#user-history-container');
            container.classList.remove('hidden');
        } catch (error) {
            this.handleError(error);
        } finally {
            this.hideLoader();
        }
    }
    
    renderUserHistory(history, userId) {
        const container = this.container.querySelector('#user-history-container');
        
        if (history.length === 0) {
            container.innerHTML = `
                <div class="text-center py-8 text-gray-400">
                    <i class="icon-user text-4xl mb-4"></i>
                    <p>No history found for user: ${userId}</p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = `
            <h4 class="text-lg font-semibold mb-4">History for User: ${userId}</h4>
            <div class="space-y-3">
                ${history.map(action => `
                    <div class="bg-gray-700 p-4 rounded border-l-4 ${this.getActionBorderColor(action.action_type)}">
                        <div class="flex items-center justify-between">
                            <div class="flex items-center space-x-3">
                                <i class="${this.getActionIcon(action.action_type)} text-lg"></i>
                                <div>
                                    <div class="font-medium">${this.getActionTitle(action)}</div>
                                    <div class="text-sm text-gray-400">
                                        ${new Date(action.timestamp || action.bannedAt || action.givenAt).toLocaleString()}
                                    </div>
                                </div>
                            </div>
                            <div class="text-sm text-gray-300">
                                ${action.reason || action.item || 'No details'}
                            </div>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }
    
    getActionBorderColor(actionType) {
        switch (actionType) {
            case 'ban': return 'border-red-500';
            case 'item_give': return 'border-green-500';
            case 'kick': return 'border-yellow-500';
            case 'teleport': return 'border-blue-500';
            default: return 'border-gray-500';
        }
    }
    
    getActionIcon(actionType) {
        switch (actionType) {
            case 'ban': return 'icon-ban';
            case 'item_give': return 'icon-gift';
            case 'kick': return 'icon-kick';
            case 'teleport': return 'icon-teleport';
            default: return 'icon-info';
        }
    }
    
    getActionTitle(action) {
        switch (action.action_type) {
            case 'ban': 
                return `${action.type === 'permanent' ? 'Permanent' : 'Temporary'} Ban${action.duration ? ` (${action.duration}m)` : ''}`;
            case 'item_give': 
                return `Gave ${action.amount}x ${action.item}`;
            case 'kick': 
                return 'Kicked from server';
            case 'teleport': 
                return 'Teleported user';
            default: 
                return 'Unknown action';
        }
    }
    
    filterBans(searchText) {
        if (!this.dataTable) return;
        
        const filteredBans = this.state.bans.filter(ban => 
            ban.userId.toLowerCase().includes(searchText.toLowerCase()) ||
            ban.reason.toLowerCase().includes(searchText.toLowerCase()) ||
            ban.serverId.includes(searchText)
        );
        
        this.dataTable.updateData(filteredBans);
    }
    
    handleBanSelection(selectedBans) {
        this.setState({ selectedBans: new Set(selectedBans) });
        
        const modal = this.container.querySelector('#bulk-actions-modal');
        const countSpan = modal.querySelector('#selected-count');
        countSpan.textContent = selectedBans.length;
        
        if (selectedBans.length > 0) {
            this.showModal('#bulk-actions-modal');
        }
    }
    
    clearForm(selector) {
        const form = this.container.querySelector(selector);
        if (form) {
            form.reset();
            
            // Reset custom states
            const customItemInput = form.querySelector('#give-custom-item');
            const itemSelect = form.querySelector('#give-item-select');
            
            if (customItemInput && itemSelect) {
                itemSelect.disabled = false;
                itemSelect.required = true;
            }
        }
    }
    
    showModal(selector) {
        const modal = this.container.querySelector(selector);
        if (modal) {
            modal.classList.add('active');
        }
    }
    
    hideModal(selector) {
        const modal = this.container.querySelector(selector);
        if (modal) {
            modal.classList.remove('active');
        }
    }
    
    showNotification(message, type = 'info') {
        this.eventBus.emit('notification:show', { message, type });
    }
    
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
    
    onDestroy() {
        // Clean up data table
        if (this.dataTable) {
            this.dataTable.destroy();
        }
        
        // Clean up global reference
        if (window.userManagement === this) {
            delete window.userManagement;
        }
        
        // Unsubscribe from events
        this.eventBus.off('servers:updated');
        this.eventBus.off('user:banned');
        this.eventBus.off('user:unbanned');
    }
}