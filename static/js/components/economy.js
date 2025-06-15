/**
 * GUST Bot Enhanced - Economy System Component
 * ============================================
 * Modular component for economy management, coin transfers, and balance operations
 */

class EconomyComponent extends BaseComponent {
    constructor(containerId, options = {}) {
        super(containerId, options);
        this.api = options.api || window.App.api;
        this.eventBus = options.eventBus || window.App.eventBus;
        this.stateManager = options.stateManager || window.App.stateManager;
    }
    
    get defaultOptions() {
        return {
            ...super.defaultOptions,
            enableTransfers: true,
            enableAdminControls: true,
            refreshInterval: 30000,
            maxTransferAmount: 100000
        };
    }
    
    getInitialState() {
        return {
            ...super.getInitialState(),
            userBalance: null,
            lookupUserId: '',
            transferFrom: '',
            transferTo: '',
            transferAmount: 0,
            leaderboard: [],
            transactions: [],
            stats: {}
        };
    }
    
    render() {
        this.container.innerHTML = `
            <div class="economy-system">
                <div class="economy-header">
                    <h2 class="text-3xl font-bold mb-6">💰 Economy Management</h2>
                    <div class="economy-stats" id="economyStats">
                        <!-- Stats will be populated here -->
                    </div>
                </div>
                
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <!-- Balance Lookup Section -->
                    <div class="bg-gray-800 p-6 rounded-lg">
                        <h3 class="text-xl font-semibold mb-4">💰 Check Balance</h3>
                        <div class="space-y-4">
                            <div class="form-group">
                                <label class="block text-sm font-medium mb-2">User ID</label>
                                <input type="text" 
                                       id="lookupUserId" 
                                       placeholder="Enter User ID" 
                                       class="w-full bg-gray-700 p-3 rounded border border-gray-600 focus:border-purple-500"
                                       value="${this.state.lookupUserId}">
                            </div>
                            <button id="lookupBalanceBtn" 
                                    class="w-full bg-blue-600 hover:bg-blue-700 p-3 rounded font-medium">
                                Check Balance
                            </button>
                            <div id="balanceResult" class="text-center text-lg font-semibold">
                                ${this.state.userBalance !== null ? `Balance: ${this.state.userBalance} coins` : ''}
                            </div>
                        </div>
                    </div>
                    
                    <!-- Transfer Coins Section -->
                    <div class="bg-gray-800 p-6 rounded-lg">
                        <h3 class="text-xl font-semibold mb-4">💸 Transfer Coins</h3>
                        <div class="space-y-4">
                            <div class="form-group">
                                <label class="block text-sm font-medium mb-2">From User ID</label>
                                <input type="text" 
                                       id="fromUserId" 
                                       placeholder="From User ID" 
                                       class="w-full bg-gray-700 p-3 rounded border border-gray-600 focus:border-purple-500"
                                       value="${this.state.transferFrom}">
                            </div>
                            <div class="form-group">
                                <label class="block text-sm font-medium mb-2">To User ID</label>
                                <input type="text" 
                                       id="toUserId" 
                                       placeholder="To User ID" 
                                       class="w-full bg-gray-700 p-3 rounded border border-gray-600 focus:border-purple-500"
                                       value="${this.state.transferTo}">
                            </div>
                            <div class="form-group">
                                <label class="block text-sm font-medium mb-2">Amount</label>
                                <input type="number" 
                                       id="transferAmount" 
                                       placeholder="Amount to transfer" 
                                       min="1"
                                       max="${this.options.maxTransferAmount}"
                                       class="w-full bg-gray-700 p-3 rounded border border-gray-600 focus:border-purple-500"
                                       value="${this.state.transferAmount}">
                            </div>
                            <button id="transferCoinsBtn" 
                                    class="w-full bg-green-600 hover:bg-green-700 p-3 rounded font-medium">
                                Transfer Coins
                            </button>
                        </div>
                    </div>
                    
                    <!-- Admin Controls Section -->
                    ${this.options.enableAdminControls ? this.renderAdminControls() : ''}
                    
                    <!-- Leaderboard Section -->
                    <div class="bg-gray-800 p-6 rounded-lg">
                        <h3 class="text-xl font-semibold mb-4">🏆 Economy Leaderboard</h3>
                        <div id="economyLeaderboard" class="space-y-2">
                            <!-- Leaderboard will be populated here -->
                        </div>
                        <button id="refreshLeaderboardBtn" 
                                class="mt-4 w-full bg-blue-600 hover:bg-blue-700 p-2 rounded text-sm">
                            Refresh Leaderboard
                        </button>
                    </div>
                </div>
                
                <!-- Transaction History -->
                <div class="mt-6 bg-gray-800 p-6 rounded-lg">
                    <h3 class="text-xl font-semibold mb-4">📊 Recent Transactions</h3>
                    <div id="transactionHistory" class="overflow-x-auto">
                        <!-- Transaction history will be populated here -->
                    </div>
                </div>
            </div>
        `;
    }
    
    renderAdminControls() {
        return `
            <div class="bg-gray-800 p-6 rounded-lg border-2 border-yellow-600">
                <h3 class="text-xl font-semibold mb-4 text-yellow-400">⚡ Admin Controls</h3>
                <div class="space-y-4">
                    <div class="form-group">
                        <label class="block text-sm font-medium mb-2">User ID</label>
                        <input type="text" 
                               id="adminUserId" 
                               placeholder="User ID" 
                               class="w-full bg-gray-700 p-3 rounded border border-gray-600 focus:border-purple-500">
                    </div>
                    <div class="form-group">
                        <label class="block text-sm font-medium mb-2">Amount</label>
                        <input type="number" 
                               id="adminAmount" 
                               placeholder="Amount" 
                               class="w-full bg-gray-700 p-3 rounded border border-gray-600 focus:border-purple-500">
                    </div>
                    <div class="grid grid-cols-2 gap-2">
                        <button id="addCoinsBtn" 
                                class="bg-green-600 hover:bg-green-700 p-2 rounded text-sm">
                            Add Coins
                        </button>
                        <button id="removeCoinsBtn" 
                                class="bg-red-600 hover:bg-red-700 p-2 rounded text-sm">
                            Remove Coins
                        </button>
                    </div>
                </div>
            </div>
        `;
    }
    
    bindEvents() {
        // Balance lookup
        const lookupBtn = this.container.querySelector('#lookupBalanceBtn');
        const lookupInput = this.container.querySelector('#lookupUserId');
        
        this.addEventListener(lookupBtn, 'click', () => this.lookupBalance());
        this.addEventListener(lookupInput, 'keypress', (e) => {
            if (e.key === 'Enter') this.lookupBalance();
        });
        this.addEventListener(lookupInput, 'input', (e) => {
            this.setState({ lookupUserId: e.target.value });
        });
        
        // Transfer coins
        const transferBtn = this.container.querySelector('#transferCoinsBtn');
        const fromInput = this.container.querySelector('#fromUserId');
        const toInput = this.container.querySelector('#toUserId');
        const amountInput = this.container.querySelector('#transferAmount');
        
        this.addEventListener(transferBtn, 'click', () => this.transferCoins());
        this.addEventListener(fromInput, 'input', (e) => {
            this.setState({ transferFrom: e.target.value });
        });
        this.addEventListener(toInput, 'input', (e) => {
            this.setState({ transferTo: e.target.value });
        });
        this.addEventListener(amountInput, 'input', (e) => {
            this.setState({ transferAmount: parseInt(e.target.value) || 0 });
        });
        
        // Admin controls
        if (this.options.enableAdminControls) {
            const addCoinsBtn = this.container.querySelector('#addCoinsBtn');
            const removeCoinsBtn = this.container.querySelector('#removeCoinsBtn');
            
            if (addCoinsBtn) {
                this.addEventListener(addCoinsBtn, 'click', () => this.addCoins());
            }
            if (removeCoinsBtn) {
                this.addEventListener(removeCoinsBtn, 'click', () => this.removeCoins());
            }
        }
        
        // Leaderboard
        const refreshLeaderboardBtn = this.container.querySelector('#refreshLeaderboardBtn');
        this.addEventListener(refreshLeaderboardBtn, 'click', () => this.loadLeaderboard());
        
        // Global events
        this.eventBus.on('economy:balance-updated', (data) => this.onBalanceUpdated(data));
        this.eventBus.on('economy:transaction-completed', (data) => this.onTransactionCompleted(data));
    }
    
    async loadData() {
        try {
            this.setState({ loading: true, error: null });
            
            // Load initial data
            await Promise.all([
                this.loadStats(),
                this.loadLeaderboard()
            ]);
            
            this.setState({ loading: false });
        } catch (error) {
            this.handleError(error);
        }
    }
    
    async lookupBalance() {
        const userId = this.state.lookupUserId.trim();
        
        if (!userId) {
            this.showNotification('Please enter a user ID', 'warning');
            return;
        }
        
        try {
            this.showLoader();
            const result = await this.api.economy.getBalance(userId);
            
            this.setState({ userBalance: result.balance });
            this.updateBalanceDisplay(result.balance);
            
            this.eventBus.emit('economy:balance-looked-up', { userId, balance: result.balance });
            this.hideLoader();
            
        } catch (error) {
            this.handleError(error);
            this.updateBalanceDisplay('Error loading balance');
        }
    }
    
    updateBalanceDisplay(balance) {
        const balanceResult = this.container.querySelector('#balanceResult');
        if (balanceResult) {
            if (typeof balance === 'number') {
                balanceResult.innerHTML = `
                    <div class="text-green-400 text-xl">
                        💰 Balance: ${balance.toLocaleString()} coins
                    </div>
                `;
            } else {
                balanceResult.innerHTML = `
                    <div class="text-red-400">${balance}</div>
                `;
            }
        }
    }
    
    async transferCoins() {
        const { transferFrom, transferTo, transferAmount } = this.state;
        
        if (!transferFrom || !transferTo || !transferAmount) {
            this.showNotification('Please fill all transfer fields', 'warning');
            return;
        }
        
        if (transferFrom === transferTo) {
            this.showNotification('Cannot transfer to the same user', 'error');
            return;
        }
        
        if (transferAmount <= 0) {
            this.showNotification('Transfer amount must be greater than 0', 'error');
            return;
        }
        
        if (transferAmount > this.options.maxTransferAmount) {
            this.showNotification(`Transfer amount cannot exceed ${this.options.maxTransferAmount}`, 'error');
            return;
        }
        
        try {
            this.showLoader();
            const result = await this.api.economy.transfer({
                fromUserId: transferFrom,
                toUserId: transferTo,
                amount: transferAmount
            });
            
            if (result.success) {
                this.showNotification('Transfer completed successfully!', 'success');
                this.clearTransferForm();
                this.eventBus.emit('economy:transfer-completed', {
                    from: transferFrom,
                    to: transferTo,
                    amount: transferAmount
                });
                await this.loadStats();
            } else {
                this.showNotification(result.error || 'Transfer failed', 'error');
            }
            
            this.hideLoader();
            
        } catch (error) {
            this.handleError(error);
            this.showNotification('Transfer failed due to an error', 'error');
        }
    }
    
    async addCoins() {
        const userId = this.container.querySelector('#adminUserId').value.trim();
        const amount = parseInt(this.container.querySelector('#adminAmount').value) || 0;
        
        if (!userId || amount <= 0) {
            this.showNotification('Please enter valid user ID and amount', 'warning');
            return;
        }
        
        try {
            const result = await this.api.economy.addCoins({ userId, amount });
            
            if (result.success) {
                this.showNotification(`Added ${amount} coins to ${userId}`, 'success');
                this.eventBus.emit('economy:coins-added', { userId, amount, newBalance: result.newBalance });
                await this.loadStats();
            } else {
                this.showNotification('Failed to add coins', 'error');
            }
            
        } catch (error) {
            this.handleError(error);
        }
    }
    
    async removeCoins() {
        const userId = this.container.querySelector('#adminUserId').value.trim();
        const amount = parseInt(this.container.querySelector('#adminAmount').value) || 0;
        
        if (!userId || amount <= 0) {
            this.showNotification('Please enter valid user ID and amount', 'warning');
            return;
        }
        
        if (!confirm(`Remove ${amount} coins from ${userId}?`)) {
            return;
        }
        
        try {
            const result = await this.api.economy.removeCoins({ userId, amount });
            
            if (result.success) {
                this.showNotification(`Removed ${amount} coins from ${userId}`, 'success');
                this.eventBus.emit('economy:coins-removed', { userId, amount, newBalance: result.newBalance });
                await this.loadStats();
            } else {
                this.showNotification(result.error || 'Failed to remove coins', 'error');
            }
            
        } catch (error) {
            this.handleError(error);
        }
    }
    
    async loadStats() {
        try {
            const stats = await this.api.economy.getStats();
            this.setState({ stats });
            this.renderStats(stats);
        } catch (error) {
            console.error('Failed to load economy stats:', error);
        }
    }
    
    async loadLeaderboard() {
        try {
            const leaderboard = await this.api.economy.getLeaderboard();
            this.setState({ leaderboard });
            this.renderLeaderboard(leaderboard);
        } catch (error) {
            console.error('Failed to load leaderboard:', error);
        }
    }
    
    renderStats(stats) {
        const statsContainer = this.container.querySelector('#economyStats');
        if (statsContainer) {
            statsContainer.innerHTML = `
                <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                    <div class="bg-gray-700 p-4 rounded">
                        <div class="text-sm text-gray-400">Total Users</div>
                        <div class="text-xl font-bold">${stats.total_users || 0}</div>
                    </div>
                    <div class="bg-gray-700 p-4 rounded">
                        <div class="text-sm text-gray-400">Total Coins</div>
                        <div class="text-xl font-bold">${(stats.total_coins || 0).toLocaleString()}</div>
                    </div>
                    <div class="bg-gray-700 p-4 rounded">
                        <div class="text-sm text-gray-400">Average Balance</div>
                        <div class="text-xl font-bold">${stats.average_balance || 0}</div>
                    </div>
                    <div class="bg-gray-700 p-4 rounded">
                        <div class="text-sm text-gray-400">Richest User</div>
                        <div class="text-sm font-bold">${stats.richest_user?.userId || 'N/A'}</div>
                        <div class="text-xs text-gray-400">${(stats.richest_user?.balance || 0).toLocaleString()} coins</div>
                    </div>
                </div>
            `;
        }
    }
    
    renderLeaderboard(leaderboard) {
        const leaderboardContainer = this.container.querySelector('#economyLeaderboard');
        if (leaderboardContainer) {
            if (leaderboard.length === 0) {
                leaderboardContainer.innerHTML = '<div class="text-gray-400 text-center py-4">No users found</div>';
                return;
            }
            
            leaderboardContainer.innerHTML = leaderboard.map((user, index) => `
                <div class="flex items-center justify-between p-3 bg-gray-700 rounded">
                    <div class="flex items-center space-x-3">
                        <span class="text-lg font-bold ${index === 0 ? 'text-yellow-400' : index === 1 ? 'text-gray-300' : index === 2 ? 'text-yellow-600' : 'text-gray-400'}">
                            ${index + 1}
                        </span>
                        <span class="font-medium">${user.userId}</span>
                    </div>
                    <span class="text-green-400 font-bold">${user.balance.toLocaleString()} coins</span>
                </div>
            `).join('');
        }
    }
    
    clearTransferForm() {
        this.setState({ transferFrom: '', transferTo: '', transferAmount: 0 });
        this.container.querySelector('#fromUserId').value = '';
        this.container.querySelector('#toUserId').value = '';
        this.container.querySelector('#transferAmount').value = '';
    }
    
    onBalanceUpdated(data) {
        // Handle balance updates from other components
        if (data.userId === this.state.lookupUserId) {
            this.setState({ userBalance: data.balance });
            this.updateBalanceDisplay(data.balance);
        }
    }
    
    onTransactionCompleted(data) {
        // Handle transaction completion notifications
        this.loadStats();
        this.loadLeaderboard();
    }
    
    showNotification(message, type = 'info') {
        this.eventBus.emit('notification:show', { message, type });
    }
    
    onStateChange(oldState, newState) {
        // React to state changes if needed
        if (oldState.userBalance !== newState.userBalance && newState.userBalance !== null) {
            this.updateBalanceDisplay(newState.userBalance);
        }
    }
    
    onDestroy() {
        // Clean up event listeners
        this.eventBus.off('economy:balance-updated');
        this.eventBus.off('economy:transaction-completed');
    }
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = EconomyComponent;
} else {
    window.EconomyComponent = EconomyComponent;
}