/**
 * GUST Bot Enhanced - API Communication Layer
 * ==========================================
 * Centralized API calls and HTTP request management
 */

import { Config } from './config.js';

export class API {
    constructor() {
        this.baseURL = Config.API.BASE_URL;
        this.defaultHeaders = {
            'Content-Type': 'application/json'
        };
        this.requestCount = 0;
        this.retryAttempts = Config.PERFORMANCE.MAX_RETRIES;
        this.retryDelay = Config.PERFORMANCE.RETRY_DELAY;
    }

    /**
     * Generic request method with error handling and retry logic
     */
    async request(endpoint, options = {}) {
        const url = this.baseURL + endpoint;
        const config = {
            ...options,
            headers: {
                ...this.defaultHeaders,
                ...options.headers
            }
        };

        if (Config.DEBUG.LOG_API_CALLS) {
            console.log(`🌐 API Request: ${config.method || 'GET'} ${url}`, config);
        }

        this.requestCount++;

        for (let attempt = 1; attempt <= this.retryAttempts; attempt++) {
            try {
                const response = await fetch(url, config);
                
                if (!response.ok) {
                    if (response.status === 401) {
                        throw new Error('Authentication required');
                    }
                    if (response.status === 403) {
                        throw new Error('Forbidden - insufficient permissions');
                    }
                    if (response.status >= 500 && attempt < this.retryAttempts) {
                        throw new Error('Server error - retrying');
                    }
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }

                const data = await response.json();
                
                if (Config.DEBUG.LOG_API_CALLS) {
                    console.log(`✅ API Response: ${url}`, data);
                }

                return data;

            } catch (error) {
                console.error(`❌ API Error (attempt ${attempt}/${this.retryAttempts}):`, error);
                
                if (attempt === this.retryAttempts) {
                    throw error;
                }
                
                // Wait before retry
                await this.delay(this.retryDelay * attempt);
            }
        }
    }

    /**
     * GET request
     */
    async get(endpoint, params = {}) {
        const url = new URL(this.baseURL + endpoint, window.location.origin);
        Object.keys(params).forEach(key => {
            if (params[key] !== undefined && params[key] !== null) {
                url.searchParams.append(key, params[key]);
            }
        });

        return this.request(url.pathname + url.search, {
            method: 'GET'
        });
    }

    /**
     * POST request
     */
    async post(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    /**
     * PUT request
     */
    async put(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    /**
     * DELETE request
     */
    async delete(endpoint) {
        return this.request(endpoint, {
            method: 'DELETE'
        });
    }

    /**
     * Utility delay function
     */
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    // ===========================================
    // AUTHENTICATION API METHODS
    // ===========================================

    async getTokenStatus() {
        return this.get(Config.API.ENDPOINTS.TOKEN_STATUS);
    }

    async refreshToken() {
        return this.post(Config.API.ENDPOINTS.TOKEN_REFRESH);
    }

    // ===========================================
    // SERVER MANAGEMENT API METHODS
    // ===========================================

    async getServers() {
        return this.get(Config.API.ENDPOINTS.SERVERS);
    }

    async addServer(serverData) {
        return this.post(Config.API.ENDPOINTS.SERVERS_ADD, serverData);
    }

    async updateServer(serverId, updateData) {
        return this.post(Config.API.ENDPOINTS.SERVERS_UPDATE(serverId), updateData);
    }

    async deleteServer(serverId) {
        return this.delete(Config.API.ENDPOINTS.SERVERS_DELETE(serverId));
    }

    async pingServer(serverId) {
        return this.post(Config.API.ENDPOINTS.SERVERS_PING(serverId));
    }

    async bulkServerAction(action, serverIds) {
        return this.post(Config.API.ENDPOINTS.SERVERS_BULK, {
            action,
            serverIds
        });
    }

    async getServerStats() {
        return this.get(Config.API.ENDPOINTS.SERVERS_STATS);
    }

    // ===========================================
    // CONSOLE API METHODS
    // ===========================================

    async sendConsoleCommand(command, serverId, region) {
        return this.post(Config.API.ENDPOINTS.CONSOLE_SEND, {
            command,
            serverId,
            region
        });
    }

    async getConsoleOutput() {
        return this.get(Config.API.ENDPOINTS.CONSOLE_OUTPUT);
    }

    async connectLiveConsole(serverId, region) {
        return this.post(Config.API.ENDPOINTS.CONSOLE_LIVE_CONNECT, {
            serverId,
            region
        });
    }

    async disconnectLiveConsole(serverId) {
        return this.post(Config.API.ENDPOINTS.CONSOLE_LIVE_DISCONNECT, {
            serverId
        });
    }

    async getLiveConsoleStatus() {
        return this.get(Config.API.ENDPOINTS.CONSOLE_LIVE_STATUS);
    }

    async getLiveConsoleMessages(params = {}) {
        return this.get(Config.API.ENDPOINTS.CONSOLE_LIVE_MESSAGES, params);
    }

    async testLiveConsole() {
        return this.get(Config.API.ENDPOINTS.CONSOLE_LIVE_TEST);
    }

    // ===========================================
    // EVENTS API METHODS
    // ===========================================

    async getEvents() {
        return this.get(Config.API.ENDPOINTS.EVENTS);
    }

    async startKothEvent(eventData) {
        return this.post(Config.API.ENDPOINTS.EVENTS_KOTH_START, eventData);
    }

    async stopKothEvent(eventId) {
        return this.post(Config.API.ENDPOINTS.EVENTS_KOTH_STOP, { eventId });
    }

    async getServerEvents(serverId) {
        return this.get(Config.API.ENDPOINTS.EVENTS_SERVER(serverId));
    }

    async getEventStats() {
        return this.get(Config.API.ENDPOINTS.EVENTS_STATS);
    }

    async getArenaLocations() {
        return this.get(Config.API.ENDPOINTS.EVENTS_ARENA_LOCATIONS);
    }

    async getEventTemplates() {
        return this.get(Config.API.ENDPOINTS.EVENTS_TEMPLATES);
    }

    // ===========================================
    // ECONOMY API METHODS
    // ===========================================

    async getUserBalance(userId) {
        return this.get(Config.API.ENDPOINTS.ECONOMY_BALANCE(userId));
    }

    async transferCoins(fromUserId, toUserId, amount) {
        return this.post(Config.API.ENDPOINTS.ECONOMY_TRANSFER, {
            fromUserId,
            toUserId,
            amount
        });
    }

    async addCoins(userId, amount, reason) {
        return this.post(Config.API.ENDPOINTS.ECONOMY_ADD_COINS, {
            userId,
            amount,
            reason
        });
    }

    async removeCoins(userId, amount, reason) {
        return this.post(Config.API.ENDPOINTS.ECONOMY_REMOVE_COINS, {
            userId,
            amount,
            reason
        });
    }

    async getUserTransactions(userId, limit = 50) {
        return this.get(Config.API.ENDPOINTS.ECONOMY_TRANSACTIONS(userId), { limit });
    }

    async getEconomyLeaderboard(limit = 10) {
        return this.get(Config.API.ENDPOINTS.ECONOMY_LEADERBOARD, { limit });
    }

    async getEconomyStats() {
        return this.get(Config.API.ENDPOINTS.ECONOMY_STATS);
    }

    // ===========================================
    // GAMBLING API METHODS
    // ===========================================

    async playSlots(userId, bet) {
        return this.post(Config.API.ENDPOINTS.GAMBLING_SLOTS, {
            userId,
            bet
        });
    }

    async playCoinflip(userId, amount, choice) {
        return this.post(Config.API.ENDPOINTS.GAMBLING_COINFLIP, {
            userId,
            amount,
            choice
        });
    }

    async playDice(userId, amount, prediction) {
        return this.post(Config.API.ENDPOINTS.GAMBLING_DICE, {
            userId,
            amount,
            prediction
        });
    }

    async getGamblingHistory(userId, limit = 20, type = 'all') {
        return this.get(Config.API.ENDPOINTS.GAMBLING_HISTORY(userId), {
            limit,
            type
        });
    }

    async getGamblingStats(userId) {
        return this.get(Config.API.ENDPOINTS.GAMBLING_STATS(userId));
    }

    async getGamblingLeaderboard(limit = 10, period = 'all') {
        return this.get(Config.API.ENDPOINTS.GAMBLING_LEADERBOARD, {
            limit,
            period
        });
    }

    // ===========================================
    // CLAN API METHODS
    // ===========================================

    async getClans() {
        return this.get(Config.API.ENDPOINTS.CLANS);
    }

    async createClan(clanData) {
        return this.post(Config.API.ENDPOINTS.CLANS_CREATE, clanData);
    }

    async getClan(clanId) {
        return this.get(Config.API.ENDPOINTS.CLANS_GET(clanId));
    }

    async joinClan(clanId, userId) {
        return this.post(Config.API.ENDPOINTS.CLANS_JOIN(clanId), { userId });
    }

    async leaveClan(clanId, userId) {
        return this.post(Config.API.ENDPOINTS.CLANS_LEAVE(clanId), { userId });
    }

    async kickFromClan(clanId, leaderId, targetId) {
        return this.post(Config.API.ENDPOINTS.CLANS_KICK(clanId), {
            leaderId,
            targetId
        });
    }

    async updateClan(clanId, leaderId, updateData) {
        return this.post(Config.API.ENDPOINTS.CLANS_UPDATE(clanId), {
            leaderId,
            ...updateData
        });
    }

    async deleteClan(clanId, leaderId) {
        return this.delete(Config.API.ENDPOINTS.CLANS_DELETE(clanId), {
            leaderId
        });
    }

    async getUserClan(userId) {
        return this.get(Config.API.ENDPOINTS.CLANS_USER(userId));
    }

    async getServerClans(serverId) {
        return this.get(Config.API.ENDPOINTS.CLANS_SERVER(serverId));
    }

    async getClanStats() {
        return this.get(Config.API.ENDPOINTS.CLANS_STATS);
    }

    // ===========================================
    // USER MANAGEMENT API METHODS
    // ===========================================

    async tempBanUser(userId, serverId, duration, reason) {
        return this.post(Config.API.ENDPOINTS.BANS_TEMP, {
            userId,
            serverId,
            duration,
            reason
        });
    }

    async permanentBanUser(userId, serverId, reason) {
        return this.post(Config.API.ENDPOINTS.BANS_PERMANENT, {
            userId,
            serverId,
            reason
        });
    }

    async unbanUser(userId, serverId) {
        return this.post(Config.API.ENDPOINTS.BANS_UNBAN, {
            userId,
            serverId
        });
    }

    async getBans(limit = 50, serverId = null) {
        return this.get(Config.API.ENDPOINTS.BANS_LIST, {
            limit,
            serverId
        });
    }

    async giveItem(playerId, serverId, item, amount) {
        return this.post(Config.API.ENDPOINTS.ITEMS_GIVE, {
            playerId,
            serverId,
            item,
            amount
        });
    }

    async kickUser(userId, serverId, reason) {
        return this.post(Config.API.ENDPOINTS.USERS_KICK, {
            userId,
            serverId,
            reason
        });
    }

    async teleportUser(userId, serverId, x, y, z) {
        return this.post(Config.API.ENDPOINTS.USERS_TELEPORT, {
            userId,
            serverId,
            x,
            y,
            z
        });
    }

    async getUserHistory(userId, limit = 20) {
        return this.get(Config.API.ENDPOINTS.USERS_HISTORY(userId), { limit });
    }

    async searchUsers(query, limit = 10) {
        return this.get(Config.API.ENDPOINTS.USERS_SEARCH, {
            q: query,
            limit
        });
    }

    async getUserStats() {
        return this.get(Config.API.ENDPOINTS.USERS_STATS);
    }

    // ===========================================
    // HEALTH AND STATUS API METHODS
    // ===========================================

    async getHealth() {
        return this.get(Config.API.ENDPOINTS.HEALTH);
    }

    // ===========================================
    // BATCH API METHODS
    // ===========================================

    /**
     * Execute multiple API calls in parallel
     */
    async batch(requests) {
        const promises = requests.map(request => {
            const { method = 'GET', endpoint, data } = request;
            
            switch (method.toUpperCase()) {
                case 'GET':
                    return this.get(endpoint, data);
                case 'POST':
                    return this.post(endpoint, data);
                case 'PUT':
                    return this.put(endpoint, data);
                case 'DELETE':
                    return this.delete(endpoint);
                default:
                    throw new Error(`Unsupported method: ${method}`);
            }
        });

        try {
            const results = await Promise.allSettled(promises);
            return results.map((result, index) => ({
                request: requests[index],
                success: result.status === 'fulfilled',
                data: result.status === 'fulfilled' ? result.value : null,
                error: result.status === 'rejected' ? result.reason : null
            }));
        } catch (error) {
            console.error('❌ Batch API error:', error);
            throw error;
        }
    }

    /**
     * Get request statistics
     */
    getStats() {
        return {
            requestCount: this.requestCount,
            retryAttempts: this.retryAttempts,
            retryDelay: this.retryDelay
        };
    }

    /**
     * Reset request statistics
     */
    resetStats() {
        this.requestCount = 0;
    }
}