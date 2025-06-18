/**
 * GUST Bot Enhanced - Complete API Client (REFACTORED)
 * ====================================================
 * Server-specific API client with user database integration
 */

class GustBotAPI {
    constructor(baseURL = '') {
        this.baseURL = baseURL;
        this.currentServer = null;
        this.currentUser = null;
    }

    async request(method, endpoint, data = null, params = null) {
        const url = new URL(this.baseURL + endpoint, window.location.origin);
        
        if (params) {
            Object.keys(params).forEach(key => 
                url.searchParams.append(key, params[key])
            );
        }

        const options = {
            method,
            headers: {
                'Content-Type': 'application/json',
            },
        };

        if (data) {
            options.body = JSON.stringify(data);
        }

        const response = await fetch(url, options);
        return response.json();
    }

    // Generic methods
    async get(endpoint, params = null) {
        return this.request('GET', endpoint, null, params);
    }

    async post(endpoint, data) {
        return this.request('POST', endpoint, data);
    }

    async put(endpoint, data) {
        return this.request('PUT', endpoint, data);
    }

    async delete(endpoint) {
        return this.request('DELETE', endpoint);
    }

    // Server context management
    setCurrentServer(serverId) {
        this.currentServer = serverId;
        localStorage.setItem('gust_current_server', serverId);
    }

    getCurrentServer() {
        return this.currentServer || localStorage.getItem('gust_current_server');
    }

    setCurrentUser(userId) {
        this.currentUser = userId;
        localStorage.setItem('gust_current_user', userId);
    }

    getCurrentUser() {
        return this.currentUser || localStorage.getItem('gust_current_user');
    }

    // User Database API
    async registerUser(userId, nickname) {
        return this.post('/api/users/register', { userId, nickname });
    }

    async getUserProfile(userId) {
        return this.get(/api/users/profile/);
    }

    async updateUserProfile(userId, profileData) {
        return this.put(/api/users/profile/, profileData);
    }

    async getUserServers(userId) {
        return this.get(/api/users/servers/);
    }

    async joinServer(userId, serverId) {
        return this.post(/api/users/join-server//);
    }

    // Economy API (Server-Specific)
    async getBalance(userId, serverId = null) {
        const server = serverId || this.getCurrentServer();
        return this.get(/api/economy/balance//);
    }

    async addCoins(userId, amount, serverId = null) {
        const server = serverId || this.getCurrentServer();
        return this.post(/api/economy/add-coins//, { amount });
    }

    async transferCoins(fromUserId, toUserId, amount, serverId = null) {
        const server = serverId || this.getCurrentServer();
        return this.post(/api/economy/transfer///, { amount });
    }

    async getLeaderboard(serverId = null, limit = 10) {
        const server = serverId || this.getCurrentServer();
        return this.get(/api/economy/leaderboard/, { limit });
    }

    async getServerEconomyStats(serverId = null) {
        const server = serverId || this.getCurrentServer();
        return this.get(/api/economy/server-stats/);
    }

    async getTransactionHistory(userId, serverId = null, limit = 20) {
        const server = serverId || this.getCurrentServer();
        return this.get(/api/economy/transactions//, { limit });
    }

    // Gambling API (Server-Specific)
    async playSlots(userId, amount, serverId = null) {
        const server = serverId || this.getCurrentServer();
        return this.post(/api/gambling/slots//, { amount });
    }

    async playCoinflip(userId, amount, choice, serverId = null) {
        const server = serverId || this.getCurrentServer();
        return this.post(/api/gambling/coinflip//, { amount, choice });
    }

    async playDice(userId, amount, prediction, serverId = null) {
        const server = serverId || this.getCurrentServer();
        return this.post(/api/gambling/dice//, { amount, prediction });
    }

    async getGamblingHistory(userId, serverId = null, limit = 20) {
        const server = serverId || this.getCurrentServer();
        return this.get(/api/gambling/history//, { limit });
    }

    async getGamblingStats(userId, serverId = null) {
        const server = serverId || this.getCurrentServer();
        return this.get(/api/gambling/stats//);
    }

    async getGamblingLeaderboard(serverId = null, limit = 10) {
        const server = serverId || this.getCurrentServer();
        return this.get(/api/gambling/leaderboard/, { limit });
    }

    // Clan API (Server-Specific)
    async getServerClans(serverId = null) {
        const server = serverId || this.getCurrentServer();
        return this.get(/api/clans/);
    }

    async createClan(userId, serverId, name, tag, description = '') {
        return this.post('/api/clans/create', { userId, serverId, name, tag, description });
    }

    async joinClan(userId, serverId, clanTag) {
        return this.post('/api/clans/join', { userId, serverId, clanTag });
    }

    async leaveClan(userId, serverId) {
        return this.post('/api/clans/leave', { userId, serverId });
    }

    async getClanStats(serverId = null) {
        const server = serverId || this.getCurrentServer();
        return this.get(/api/clans/stats/);
    }

    async getUserClanInfo(userId, serverId = null) {
        const server = serverId || this.getCurrentServer();
        return this.get(/api/clans/user//);
    }

    // Helper methods
    formatCurrency(amount) {
        return new Intl.NumberFormat('en-US').format(amount);
    }

    validateServerId(serverId) {
        return serverId && serverId.toString().length > 0;
    }

    validateUserId(userId) {
        return userId && userId.trim().length > 0;
    }
}

// Global API instance
const gustAPI = new GustBotAPI();

// Make available globally
window.GustBotAPI = GustBotAPI;
window.gustAPI = gustAPI;

export { GustBotAPI, gustAPI };
