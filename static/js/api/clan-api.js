/**
 * GUST Bot Enhanced - Clan API Client (ENHANCED)
 * ===============================================
 * Server-specific clan management with user database integration
 */

class ClanAPI {
    constructor(baseURL = '') {
        this.baseURL = baseURL;
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

    // Clan Management (Server-Specific)
    async getServerClans(serverId) {
        return this.get(/api/clans/);
    }

    async createClan(userId, serverId, name, tag, description = '') {
        return this.post('/api/clans/create', {
            userId,
            serverId,
            name,
            tag,
            description
        });
    }

    async joinClan(userId, serverId, clanTag) {
        return this.post('/api/clans/join', {
            userId,
            serverId,
            clanTag
        });
    }

    async leaveClan(userId, serverId) {
        return this.post('/api/clans/leave', {
            userId,
            serverId
        });
    }

    async getClanStats(serverId) {
        return this.get(/api/clans/stats/);
    }

    async getUserClanInfo(userId, serverId) {
        return this.get(/api/clans/user//);
    }

    // Clan Management Helpers
    async isUserInClan(userId, serverId) {
        try {
            const result = await this.getUserClanInfo(userId, serverId);
            return result.inClan;
        } catch (error) {
            console.error('Error checking clan membership:', error);
            return false;
        }
    }

    async getClanMemberInfo(serverId, clanTag) {
        try {
            const clans = await this.getServerClans(serverId);
            const clan = clans.find(c => c.tag === clanTag);
            return clan ? clan.enhancedMembers : [];
        } catch (error) {
            console.error('Error getting clan member info:', error);
            return [];
        }
    }

    async getClanLeaderboard(serverId, sortBy = 'totalWealth') {
        try {
            const clans = await this.getServerClans(serverId);
            return clans.sort((a, b) => {
                const aValue = a.stats?.[sortBy] || 0;
                const bValue = b.stats?.[sortBy] || 0;
                return bValue - aValue; // Descending order
            });
        } catch (error) {
            console.error('Error getting clan leaderboard:', error);
            return [];
        }
    }

    // Clan Statistics
    async getClanWealthRanking(serverId) {
        return this.getClanLeaderboard(serverId, 'totalWealth');
    }

    async getClanSizeRanking(serverId) {
        return this.getClanLeaderboard(serverId, 'totalMembers');
    }

    async getActiveClansRanking(serverId) {
        return this.getClanLeaderboard(serverId, 'activeMembers');
    }

    // Enhanced clan display helpers
    formatClanDisplay(clan) {
        return {
            name: clan.name,
            tag: [],
            memberCount: clan.memberCount,
            wealth: this.formatCurrency(clan.stats?.totalWealth || 0),
            averageWealth: this.formatCurrency(clan.stats?.averageBalance || 0),
            leader: clan.enhancedMembers?.find(m => m.isLeader)?.displayName || 'Unknown'
        };
    }

    formatCurrency(amount) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }).format(amount).replace('$', '');
    }

    // Clan validation helpers
    validateClanName(name) {
        if (!name || name.length < 3 || name.length > 30) {
            return 'Clan name must be 3-30 characters long';
        }
        if (!/^[a-zA-Z0-9\s]+$/.test(name)) {
            return 'Clan name can only contain letters, numbers, and spaces';
        }
        return null;
    }

    validateClanTag(tag) {
        if (!tag || tag.length < 2 || tag.length > 6) {
            return 'Clan tag must be 2-6 characters long';
        }
        if (!/^[A-Z0-9]+$/.test(tag)) {
            return 'Clan tag can only contain uppercase letters and numbers';
        }
        return null;
    }

    validateClanDescription(description) {
        if (description && description.length > 200) {
            return 'Clan description cannot exceed 200 characters';
        }
        return null;
    }
}

// Global clan API instance
const clanAPI = new ClanAPI();

// Make available globally
if (typeof window !== 'undefined') {
    window.ClanAPI = ClanAPI;
    window.clanAPI = clanAPI;
}

export { ClanAPI, clanAPI };
