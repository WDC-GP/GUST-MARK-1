/**
 * Enhanced Dashboard Component
 * ============================
 * Main dashboard with server-specific data
 */

class EnhancedDashboard {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.options = {
            refreshInterval: 30000,
            autoRefresh: true,
            ...options
        };
        this.api = window.gustAPI;
        this.refreshTimer = null;
        this.currentServer = null;
        this.currentUser = null;
        
        this.init();
    }

    async init() {
        this.render();
        this.attachEventListeners();
        
        // Listen for server/user changes
        document.addEventListener('serverChanged', (e) => {
            this.currentServer = e.detail.serverId;
            this.refreshData();
        });
        
        document.addEventListener('userRegistered', (e) => {
            this.currentUser = e.detail.user;
            this.refreshData();
        });
        
        document.addEventListener('userLoggedOut', () => {
            this.currentUser = null;
            this.refreshData();
        });
        
        // Initial data load
        this.currentServer = this.api.getCurrentServer();
        this.currentUser = this.api.getCurrentUser();
        if (this.currentUser && this.currentServer) {
            this.refreshData();
        }
        
        // Setup auto-refresh
        if (this.options.autoRefresh) {
            this.startAutoRefresh();
        }
    }

    render() {
        this.container.innerHTML = 
            <div class="enhanced-dashboard space-y-6">
                <!-- Server Status Card -->
                <div class="bg-gray-800 p-6 rounded-lg border border-gray-700">
                    <h3 class="text-xl font-semibold mb-4 flex items-center">
                        🖥️ Server Status
                        <button id="refreshBtn" class="ml-auto bg-purple-600 hover:bg-purple-700 text-white px-3 py-1 rounded text-sm">
                            🔄 Refresh
                        </button>
                    </h3>
                    <div id="serverStatus" class="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div class="bg-gray-700 p-4 rounded">
                            <div class="text-2xl font-bold" id="serverPlayerCount">--</div>
                            <div class="text-gray-400">Players Online</div>
                        </div>
                        <div class="bg-gray-700 p-4 rounded">
                            <div class="text-2xl font-bold" id="serverEconomyHealth">--</div>
                            <div class="text-gray-400">Economy Health</div>
                        </div>
                        <div class="bg-gray-700 p-4 rounded">
                            <div class="text-2xl font-bold" id="serverUptime">--</div>
                            <div class="text-gray-400">Server Uptime</div>
                        </div>
                    </div>
                </div>

                <!-- Quick Stats Grid -->
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                    <!-- Balance Card -->
                    <div class="bg-gray-800 p-6 rounded-lg border border-gray-700">
                        <h4 class="font-semibold mb-2 text-green-400">💰 Your Balance</h4>
                        <div class="text-3xl font-bold" id="userBalance">--</div>
                        <div class="text-sm text-gray-400 mt-2" id="balanceRank">Rank: --</div>
                    </div>

                    <!-- Clan Card -->
                    <div class="bg-gray-800 p-6 rounded-lg border border-gray-700">
                        <h4 class="font-semibold mb-2 text-purple-400">⚔️ Your Clan</h4>
                        <div class="text-xl font-bold" id="userClan">None</div>
                        <div class="text-sm text-gray-400 mt-2" id="clanRole">Not in clan</div>
                    </div>

                    <!-- Gambling Card -->
                    <div class="bg-gray-800 p-6 rounded-lg border border-gray-700">
                        <h4 class="font-semibold mb-2 text-yellow-400">🎰 Gambling Stats</h4>
                        <div class="text-xl font-bold" id="gamblingWinRate">--%</div>
                        <div class="text-sm text-gray-400 mt-2" id="gamesPlayed">-- games played</div>
                    </div>

                    <!-- Activity Card -->
                    <div class="bg-gray-800 p-6 rounded-lg border border-gray-700">
                        <h4 class="font-semibold mb-2 text-blue-400">📊 Activity</h4>
                        <div class="text-xl font-bold" id="lastSeen">--</div>
                        <div class="text-sm text-gray-400 mt-2" id="totalServers">-- servers</div>
                    </div>
                </div>

                <!-- Recent Activity -->
                <div class="bg-gray-800 p-6 rounded-lg border border-gray-700">
                    <h3 class="text-xl font-semibold mb-4">📈 Recent Activity</h3>
                    <div id="recentActivity" class="space-y-3">
                        <div class="text-gray-400 text-center py-8">
                            Select a server to view recent activity
                        </div>
                    </div>
                </div>

                <!-- Leaderboards Preview -->
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <!-- Economy Leaderboard -->
                    <div class="bg-gray-800 p-6 rounded-lg border border-gray-700">
                        <h3 class="text-xl font-semibold mb-4 text-green-400">💰 Top Players</h3>
                        <div id="economyLeaderboard" class="space-y-2">
                            <div class="text-gray-400 text-center py-4">
                                Select a server to view leaderboard
                            </div>
                        </div>
                    </div>

                    <!-- Clan Leaderboard -->
                    <div class="bg-gray-800 p-6 rounded-lg border border-gray-700">
                        <h3 class="text-xl font-semibold mb-4 text-purple-400">⚔️ Top Clans</h3>
                        <div id="clanLeaderboard" class="space-y-2">
                            <div class="text-gray-400 text-center py-4">
                                Select a server to view clans
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        ;
    }

    attachEventListeners() {
        this.container.querySelector('#refreshBtn')?.addEventListener('click', () => {
            this.refreshData();
        });
    }

    async refreshData() {
        if (!this.currentUser || !this.currentServer) {
            this.showNoDataState();
            return;
        }

        try {
            // Load all data in parallel
            const [
                balanceData,
                clanData,
                gamblingData,
                economyStats,
                economyLeaderboard,
                clanLeaderboard,
                transactionHistory
            ] = await Promise.all([
                this.api.getBalance(this.currentUser, this.currentServer),
                this.api.getUserClanInfo(this.currentUser, this.currentServer),
                this.api.getGamblingStats(this.currentUser, this.currentServer),
                this.api.getServerEconomyStats(this.currentServer),
                this.api.getLeaderboard(this.currentServer, 5),
                this.api.getServerClans(this.currentServer),
                this.api.getTransactionHistory(this.currentUser, this.currentServer, 5)
            ]);

            this.updateBalance(balanceData);
            this.updateClanInfo(clanData);
            this.updateGamblingStats(gamblingData);
            this.updateServerStats(economyStats);
            this.updateEconomyLeaderboard(economyLeaderboard);
            this.updateClanLeaderboard(clanLeaderboard);
            this.updateRecentActivity(transactionHistory);

        } catch (error) {
            console.error('Error refreshing dashboard data:', error);
        }
    }

    updateBalance(data) {
        const balanceEl = this.container.querySelector('#userBalance');
        const rankEl = this.container.querySelector('#balanceRank');
        
        if (data?.success) {
            balanceEl.textContent = this.api.formatCurrency(data.balance);
            rankEl.textContent = Rank: ;
        } else {
            balanceEl.textContent = '--';
            rankEl.textContent = 'Rank: --';
        }
    }

    updateClanInfo(data) {
        const clanEl = this.container.querySelector('#userClan');
        const roleEl = this.container.querySelector('#clanRole');
        
        if (data?.success && data.inClan) {
            clanEl.textContent = data.clan.name;
            roleEl.textContent = data.isLeader ? 'Leader' : 'Member';
        } else {
            clanEl.textContent = 'None';
            roleEl.textContent = 'Not in clan';
        }
    }

    updateGamblingStats(data) {
        const winRateEl = this.container.querySelector('#gamblingWinRate');
        const gamesEl = this.container.querySelector('#gamesPlayed');
        
        if (data?.success) {
            const winRate = data.stats.gamesPlayed > 0 
                ? ((data.stats.totalWon / data.stats.totalWagered) * 100).toFixed(1)
                : 0;
            winRateEl.textContent = ${winRate}%;
            gamesEl.textContent = ${data.stats.gamesPlayed} games played;
        } else {
            winRateEl.textContent = '--%';
            gamesEl.textContent = '-- games played';
        }
    }

    updateServerStats(data) {
        const playerCountEl = this.container.querySelector('#serverPlayerCount');
        const economyHealthEl = this.container.querySelector('#serverEconomyHealth');
        const uptimeEl = this.container.querySelector('#serverUptime');
        
        if (data?.success) {
            playerCountEl.textContent = data.stats.activeUsers || '--';
            economyHealthEl.textContent = ${(data.stats.healthScore * 100).toFixed(0)}%;
            uptimeEl.textContent = '99.9%'; // Mock data
        } else {
            playerCountEl.textContent = '--';
            economyHealthEl.textContent = '--';
            uptimeEl.textContent = '--';
        }
    }

    updateEconomyLeaderboard(data) {
        const container = this.container.querySelector('#economyLeaderboard');
        
        if (data?.success && data.leaderboard?.length > 0) {
            container.innerHTML = data.leaderboard.map((user, index) => 
                <div class="flex justify-between items-center p-2 bg-gray-700 rounded">
                    <div class="flex items-center space-x-2">
                        <span class="text-gray-400">#</span>
                        <span class="font-medium"></span>
                    </div>
                    <span class="text-green-400"></span>
                </div>
            ).join('');
        } else {
            container.innerHTML = '<div class="text-gray-400 text-center py-4">No data available</div>';
        }
    }

    updateClanLeaderboard(data) {
        const container = this.container.querySelector('#clanLeaderboard');
        
        if (data?.length > 0) {
            // Sort by total wealth and take top 5
            const sortedClans = data
                .sort((a, b) => (b.stats?.totalWealth || 0) - (a.stats?.totalWealth || 0))
                .slice(0, 5);
                
            container.innerHTML = sortedClans.map((clan, index) => 
                <div class="flex justify-between items-center p-2 bg-gray-700 rounded">
                    <div class="flex items-center space-x-2">
                        <span class="text-gray-400">#</span>
                        <span class="font-medium"></span>
                        <span class="text-purple-400 text-sm">[]</span>
                    </div>
                    <span class="text-purple-400"> members</span>
                </div>
            ).join('');
        } else {
            container.innerHTML = '<div class="text-gray-400 text-center py-4">No clans available</div>';
        }
    }

    updateRecentActivity(data) {
        const container = this.container.querySelector('#recentActivity');
        
        if (data?.success && data.transactions?.length > 0) {
            container.innerHTML = data.transactions.map(tx => 
                <div class="flex justify-between items-center p-3 bg-gray-700 rounded">
                    <div>
                        <div class="font-medium"></div>
                        <div class="text-sm text-gray-400"></div>
                    </div>
                    <div class="text-right">
                        <div class="font-medium ">
                            
                        </div>
                        <div class="text-xs text-gray-400"></div>
                    </div>
                </div>
            ).join('');
        } else {
            container.innerHTML = '<div class="text-gray-400 text-center py-8">No recent activity</div>';
        }
    }

    showNoDataState() {
        // Show empty states when no user/server selected
        const elements = {
            '#userBalance': '--',
            '#balanceRank': 'Rank: --',
            '#userClan': 'None',
            '#clanRole': 'Not in clan',
            '#gamblingWinRate': '--%',
            '#gamesPlayed': '-- games played',
            '#lastSeen': '--',
            '#totalServers': '-- servers',
            '#serverPlayerCount': '--',
            '#serverEconomyHealth': '--',
            '#serverUptime': '--'
        };

        Object.entries(elements).forEach(([selector, value]) => {
            const el = this.container.querySelector(selector);
            if (el) el.textContent = value;
        });

        // Clear complex sections
        this.container.querySelector('#recentActivity').innerHTML = 
            '<div class="text-gray-400 text-center py-8">Select a server and login to view activity</div>';
        this.container.querySelector('#economyLeaderboard').innerHTML = 
            '<div class="text-gray-400 text-center py-4">Select a server to view leaderboard</div>';
        this.container.querySelector('#clanLeaderboard').innerHTML = 
            '<div class="text-gray-400 text-center py-4">Select a server to view clans</div>';
    }

    startAutoRefresh() {
        this.refreshTimer = setInterval(() => {
            if (this.currentUser && this.currentServer) {
                this.refreshData();
            }
        }, this.options.refreshInterval);
    }

    stopAutoRefresh() {
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
            this.refreshTimer = null;
        }
    }

    destroy() {
        this.stopAutoRefresh();
    }
}

// Make available globally
window.EnhancedDashboard = EnhancedDashboard;

export { EnhancedDashboard };
