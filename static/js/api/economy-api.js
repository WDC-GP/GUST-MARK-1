// Updated Economy API Configuration
// ================================
// New server-specific economy endpoints

const EconomyAPI = {
    // Server-specific balance operations
    getBalance: (userId, serverId) => /api/economy/balance//,
    setBalance: (userId, serverId) => /api/economy/set-balance//,
    adjustBalance: (userId, serverId) => /api/economy/adjust-balance//,
    
    // Server-specific transfers and transactions
    transfer: (serverId) => /api/economy/transfer/,
    getTransactions: (userId, serverId) => /api/economy/transactions//,
    
    // Server-specific leaderboards and stats
    getLeaderboard: (serverId) => /api/economy/leaderboard/,
    getServerStats: (serverId) => /api/economy/server-stats/,
    
    // User database endpoints
    registerUser: () => '/api/users/register',
    getUserProfile: (userId) => /api/users/profile/,
    updateUserProfile: (userId) => /api/users/profile/,
    getUserServers: (userId) => /api/users/servers/,
    joinServer: (userId, serverId) => /api/users/join-server//
};

// Economy API Client with Server Context
class ServerAwareEconomyClient {
    constructor(apiClient, defaultServerId = 'default_server') {
        this.api = apiClient;
        this.currentServerId = defaultServerId;
    }
    
    setCurrentServer(serverId) {
        this.currentServerId = serverId;
    }
    
    async getBalance(userId, serverId = null) {
        const server = serverId || this.currentServerId;
        return this.api.get(EconomyAPI.getBalance(userId, server));
    }
    
    async adjustBalance(userId, amount, reason = 'Manual adjustment', serverId = null) {
        const server = serverId || this.currentServerId;
        return this.api.post(EconomyAPI.adjustBalance(userId, server), {
            amount,
            reason
        });
    }
    
    async transferCoins(fromUserId, toUserId, amount, serverId = null) {
        const server = serverId || this.currentServerId;
        return this.api.post(EconomyAPI.transfer(server), {
            fromUserId,
            toUserId,
            amount
        });
    }
    
    async getLeaderboard(limit = 10, serverId = null) {
        const server = serverId || this.currentServerId;
        return this.api.get(${EconomyAPI.getLeaderboard(server)}?limit=);
    }
    
    async getTransactions(userId, limit = 20, serverId = null) {
        const server = serverId || this.currentServerId;
        return this.api.get(${EconomyAPI.getTransactions(userId, server)}?limit=);
    }
    
    async getServerStats(serverId = null) {
        const server = serverId || this.currentServerId;
        return this.api.get(EconomyAPI.getServerStats(server));
    }
}

// Example usage in frontend components
const exampleUsage = {
    initializeEconomy: () => {
        // Initialize with server context
        const economyClient = new ServerAwareEconomyClient(apiClient, 'server_001');
        
        // Switch servers
        economyClient.setCurrentServer('server_002');
        
        // All operations now use the current server context
        return economyClient;
    },
    
    displayBalance: async (userId) => {
        const response = await economyClient.getBalance(userId);
        if (response.success) {
            return ${response.displayName}:  coins on ;
        }
    },
    
    showLeaderboard: async () => {
        const response = await economyClient.getLeaderboard(10);
        if (response.success) {
            return response.leaderboard.map(user => 
                #  -  coins
            );
        }
    }
};

// Export for use in main application
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { EconomyAPI, ServerAwareEconomyClient };
}
