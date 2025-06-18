// Server-Specific Gambling API Client
// ==================================
// Updated gambling API for server-specific operations

class ServerAwareGamblingClient {
    constructor(apiClient, defaultServerId = 'default_server') {
        this.api = apiClient;
        this.currentServerId = defaultServerId;
    }

    setCurrentServer(serverId) {
        this.currentServerId = serverId;
    }

    async playSlots(userId, betAmount, serverId = null) {
        const server = serverId || this.currentServerId;
        return this.api.post(/api/gambling/slots//, {
            bet: betAmount
        });
    }

    async playCoinflip(userId, betAmount, choice, serverId = null) {
        const server = serverId || this.currentServerId;
        return this.api.post(/api/gambling/coinflip//, {
            amount: betAmount,
            choice: choice.toLowerCase()
        });
    }

    async playDice(userId, betAmount, prediction, serverId = null) {
        const server = serverId || this.currentServerId;
        return this.api.post(/api/gambling/dice//, {
            amount: betAmount,
            prediction: prediction
        });
    }

    async getGamblingHistory(userId, limit = 20, gameType = 'all', serverId = null) {
        const server = serverId || this.currentServerId;
        return this.api.get(/api/gambling/history//?limit=&type=);
    }

    async getGamblingStats(userId, serverId = null) {
        const server = serverId || this.currentServerId;
        return this.api.get(/api/gambling/stats//);
    }

    async getGamblingLeaderboard(limit = 10, period = 'all', serverId = null) {
        const server = serverId || this.currentServerId;
        return this.api.get(/api/gambling/leaderboard/?limit=&period=);
    }
}

// Example usage in frontend components
const gamblingExamples = {
    initializeGambling: () => {
        // Initialize with server context
        const gamblingClient = new ServerAwareGamblingClient(apiClient, 'server_001');
        
        // Switch servers
        gamblingClient.setCurrentServer('server_002');
        
        // All gambling operations now use current server context
        return gamblingClient;
    },

    playSlotMachine: async (userId, betAmount) => {
        const response = await gamblingClient.playSlots(userId, betAmount);
        if (response.success) {
            return {
                symbols: response.result,
                winnings: response.winnings,
                newBalance: response.new_balance,
                netChange: response.net_change
            };
        }
    },

    flipCoin: async (userId, betAmount, choice) => {
        const response = await gamblingClient.playCoinflip(userId, betAmount, choice);
        if (response.success) {
            return {
                result: response.result,
                won: response.won,
                winnings: response.winnings,
                newBalance: response.new_balance
            };
        }
    },

    showGamblingStats: async (userId) => {
        const response = await gamblingClient.getGamblingStats(userId);
        if (response.success) {
            const stats = response.stats;
            return Gambling Stats:  games, % win rate, biggest win: ;
        }
    },

    showLeaderboard: async () => {
        const response = await gamblingClient.getGamblingLeaderboard(10);
        if (response.success) {
            return response.leaderboard.map(user => 
                #  -  coins won ( games)
            );
        }
    }
};

// Export for use in main application
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ServerAwareGamblingClient };
}
