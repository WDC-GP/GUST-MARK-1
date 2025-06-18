/**
 * GUST Bot Enhanced - Configuration and Constants
 * ==============================================
 * Application configuration, API endpoints, and constants
 */

export const Config = {
    // Application Information
    APP: {
        NAME: 'GUST Bot Enhanced',
        VERSION: '2.0.0',
        DESCRIPTION: 'Complete GUST bot with working KOTH events AND live console monitoring'
    },

    // API Endpoints
    API: {
        BASE_URL: '',
        ENDPOINTS: {
            // Authentication
            LOGIN: '/login',
            LOGOUT: '/logout',
            TOKEN_STATUS: '/api/token/status',
            TOKEN_REFRESH: '/api/token/refresh',

            // Server Management
            SERVERS: '/api/servers',
            SERVERS_ADD: '/api/servers/add',
            SERVERS_UPDATE: (id) => `/api/servers/update/${id}`,
            SERVERS_DELETE: (id) => `/api/servers/delete/${id}`,
            SERVERS_PING: (id) => `/api/servers/ping/${id}`,
            SERVERS_BULK: '/api/servers/bulk-action',
            SERVERS_STATS: '/api/servers/stats',

            // Console
            CONSOLE_SEND: '/api/console/send',
            CONSOLE_OUTPUT: '/api/console/output',
            CONSOLE_LIVE_CONNECT: '/api/console/live/connect',
            CONSOLE_LIVE_DISCONNECT: '/api/console/live/disconnect',
            CONSOLE_LIVE_STATUS: '/api/console/live/status',
            CONSOLE_LIVE_MESSAGES: '/api/console/live/messages',
            CONSOLE_LIVE_TEST: '/api/console/live/test',

            // Events
            EVENTS: '/api/events',
            EVENTS_KOTH_START: '/api/events/koth/start',
            EVENTS_KOTH_STOP: '/api/events/koth/stop',
            EVENTS_SERVER: (id) => `/api/events/server/${id}`,
            EVENTS_STATS: '/api/events/stats',
            EVENTS_ARENA_LOCATIONS: '/api/events/arena-locations',
            EVENTS_TEMPLATES: '/api/events/templates',

            // Economy
            ECONOMY_BALANCE: (userId) => `/api/economy/balance/${userId}`,
            ECONOMY_TRANSFER: '/api/economy/transfer',
            ECONOMY_ADD_COINS: '/api/economy/add-coins',
            ECONOMY_REMOVE_COINS: '/api/economy/remove-coins',
            ECONOMY_TRANSACTIONS: (userId) => `/api/economy/transactions/${userId}`,
            ECONOMY_LEADERBOARD: '/api/economy/leaderboard',
            ECONOMY_STATS: '/api/economy/stats',

            // Gambling
            GAMBLING_SLOTS: '/api/gambling/slots',
            GAMBLING_COINFLIP: '/api/gambling/coinflip',
            GAMBLING_DICE: '/api/gambling/dice',
            GAMBLING_HISTORY: (userId) => `/api/gambling/history/${userId}`,
            GAMBLING_STATS: (userId) => `/api/gambling/stats/${userId}`,
            GAMBLING_LEADERBOARD: '/api/gambling/leaderboard',

            // Clans
            CLANS: '/api/clans',
            CLANS_CREATE: '/api/clans/create',
            CLANS_GET: (id) => `/api/clans/${id}`,
            CLANS_JOIN: (id) => `/api/clans/${id}/join`,
            CLANS_LEAVE: (id) => `/api/clans/${id}/leave`,
            CLANS_KICK: (id) => `/api/clans/${id}/kick`,
            CLANS_UPDATE: (id) => `/api/clans/${id}/update`,
            CLANS_DELETE: (id) => `/api/clans/${id}/delete`,
            CLANS_USER: (userId) => `/api/clans/user/${userId}`,
            CLANS_SERVER: (serverId) => `/api/clans/server/${serverId}`,
            CLANS_STATS: '/api/clans/stats',

            // User Management
            BANS_TEMP: '/api/bans/temp',
            BANS_PERMANENT: '/api/bans/permanent',
            BANS_UNBAN: '/api/bans/unban',
            BANS_LIST: '/api/bans',
            ITEMS_GIVE: '/api/items/give',
            USERS_KICK: '/api/users/kick',
            USERS_TELEPORT: '/api/users/teleport',
            USERS_HISTORY: (userId) => `/api/users/${userId}/history`,
            USERS_SEARCH: '/api/users/search',
            USERS_STATS: '/api/users/stats',

            // Health
            HEALTH: '/health'
        }
    },

    // Server Dropdown IDs
    SERVER_DROPDOWNS: [
        'consoleServerSelect',
        'eventServerSelect',
        'clanServerSelect',
        'banServerSelect',
        'giveItemServerSelect',
        'monitorServerFilter'
    ],

    // Polling Intervals (in milliseconds)
    POLLING: {
        CONSOLE_REFRESH: 3000,      // Console messages refresh
        CONNECTION_STATUS: 3000,    // Live connection status
        RECONNECT_CHECK: 30000,     // Auto-reconnect check
        SYSTEM_STATUS: 30000,       // System status updates
        SERVER_LIST: 120000         // Server list refresh
    },

    // Delays (in milliseconds)
    DELAYS: {
        LIVE_CONSOLE_INIT: 2000,    // Live console initialization delay
        SERVER_CONNECTION: 500,     // Delay between server connections
        COMMAND_REFRESH: 1000,      // Delay before refreshing after command
        AUTO_REFRESH: 1000          // General auto-refresh delay
    },

    // Limits and Constraints
    LIMITS: {
        CONSOLE_MESSAGES: 50,       // Max console messages to display
        MESSAGE_BUFFER: 1000,       // Console message buffer size
        BAN_DURATION_MAX: 10080,    // Max ban duration in minutes (1 week)
        ITEM_AMOUNT_MAX: 10000,     // Max item amount to give
        SEARCH_RESULTS: 10,         // Max search results
        LEADERBOARD_SIZE: 10        // Default leaderboard size
    },

    // Route Configuration
    ROUTES: {
        DEFAULT: 'dashboard',
        TABS: [
            'dashboard',
            'server-manager',
            'console',
            'events',
            'economy',
            'gambling',
            'clans',
            'bans'
        ]
    },

    // Console Configuration
    CONSOLE: {
        AUTO_SCROLL: true,
        MESSAGE_TYPES: [
            'all', 'chat', 'auth', 'save', 'kill', 'error', 
            'warning', 'command', 'player', 'system', 'event', 'ban'
        ],
        TYPE_ICONS: {
            'chat': '💬',
            'auth': '🔐',
            'save': '💾',
            'kill': '⚔️',
            'error': '❌',
            'warning': '⚠️',
            'command': '🔧',
            'player': '👥',
            'system': '🖥️',
            'event': '🎯',
            'ban': '🚫'
        },
        QUICK_COMMANDS: [
            { label: '📊 Server Info', command: 'serverinfo' },
            { label: '👑 Auth Levels', command: 'global.getauthlevels' },
            { label: '💾 Save Server', command: 'server.save' },
            { label: '📢 Say Message', command: 'global.say "Server Message"' }
        ]
    },

    // KOTH Event Configuration
    KOTH: {
        DEFAULT_DURATION: 30,       // Default duration in minutes
        PREPARATION_TIME: 300,      // Preparation time in seconds (5 minutes)
        ARENA_LOCATIONS: [
            'Launch Site', 'Military Base', 'Airfield', 'Power Plant',
            'Water Treatment Plant', 'Train Yard', 'Satellite Dish', 'Dome',
            'Nuclear Missile Silo', 'Supermarket', 'Gas Station', 'Lighthouse',
            'Mining Outpost', 'Compound', 'Junkyard', 'Quarry', 'Desert Base',
            'Arctic Base', 'Forest Base', 'Island Base', 'Mountain Peak',
            'Valley Floor', 'Beach Landing', 'Crater Site', 'Abandoned Town',
            'Research Facility', 'Oil Rig', 'Wind Farm'
        ],
        DEFAULT_REWARDS: {
            ITEM: 'scrap',
            AMOUNT: 1000
        },
        SUPPLY_COMMANDS: [
            'giveall medical.bandage 5',
            'giveall ammo.pistol 60',
            'giveall weapon.pistol.revolver 1'
        ]
    },

    // Server Regions
    REGIONS: [
        { code: 'US', name: '🇺🇸 United States', flag: '🇺🇸' },
        { code: 'EU', name: '🇪🇺 Europe', flag: '🇪🇺' },
        { code: 'AS', name: '🌏 Asia', flag: '🌏' }
    ],

    // Server Types
    SERVER_TYPES: [
        'Standard', 'Modded', 'PvP', 'PvE', 'RP', 'Vanilla+'
    ],

    // Gambling Configuration
    GAMBLING: {
        SLOTS: {
            SYMBOLS: ['🍒', '🍋', '🔔', '⭐', '💎'],
            PAYOUTS: {
                '💎': 10,    // Diamond jackpot
                '⭐': 5,     // Star
                'three': 3,  // Any three of a kind
                'two': 2     // Any two of a kind
            }
        },
        DICE: {
            SIDES: 6,
            EXACT_MULTIPLIER: 5
        }
    },

    // Status Classes
    STATUS_CLASSES: {
        'online': 'bg-green-800 text-green-200',
        'offline': 'bg-red-800 text-red-200',
        'unknown': 'bg-gray-700 text-gray-300'
    },

    // Status Text
    STATUS_TEXT: {
        'online': '🟢 Online',
        'offline': '🔴 Offline',
        'unknown': '⚪ Unknown'
    },

    // Validation Rules
    VALIDATION: {
        SERVER_ID: {
            MIN: 1,
            MAX: 99999999
        },
        BAN_DURATION: {
            MIN: 1,
            MAX: 10080  // 1 week in minutes
        },
        TRANSFER_AMOUNT: {
            MIN: 1,
            MAX: 1000000
        },
        BET_AMOUNT: {
            MIN: 1,
            MAX: 100000
        }
    },

    // Error Messages
    ERRORS: {
        REQUIRED_FIELDS: 'Please fill in all required fields',
        INVALID_SERVER_ID: 'Invalid server ID format',
        INVALID_REGION: 'Invalid server region',
        SERVER_EXISTS: 'A server with this ID already exists',
        SERVER_NOT_FOUND: 'Server not found',
        INSUFFICIENT_BALANCE: 'Insufficient balance',
        NETWORK_ERROR: 'Network error. Please try again.',
        AUTHENTICATION_REQUIRED: 'Authentication required',
        DEMO_MODE_LIMIT: 'This feature requires G-Portal authentication',
        WEBSOCKET_UNAVAILABLE: 'WebSocket support not available. Install with: pip install websockets'
    },

    // Success Messages
    SUCCESS: {
        SERVER_ADDED: '✅ Server added successfully!',
        SERVER_UPDATED: '✅ Server updated successfully!',
        SERVER_DELETED: '✅ Server deleted successfully!',
        COMMAND_SENT: '✅ Command sent successfully!',
        EVENT_STARTED: '✅ Event started successfully!',
        TRANSFER_COMPLETE: '✅ Transfer completed successfully!',
        TOKEN_REFRESHED: '✅ Token refreshed successfully!',
        CLAN_CREATED: '✅ Clan created successfully!',
        BAN_SUCCESSFUL: '✅ User banned successfully!',
        ITEM_GIVEN: '✅ Item given successfully!'
    },

    // Local Storage Keys
    STORAGE: {
        PREFERENCES: 'gust_preferences',
        CONSOLE_FILTERS: 'gust_console_filters',
        SERVER_FAVORITES: 'gust_server_favorites',
        UI_STATE: 'gust_ui_state'
    },

    // Feature Flags
    FEATURES: {
        WEBSOCKETS: true,           // WebSocket support
        MONGODB: true,              // MongoDB support
        LIVE_CONSOLE: true,         // Live console monitoring
        AUTO_RECONNECT: true,       // Auto-reconnection
        BACKGROUND_TASKS: true,     // Background task scheduling
        DEMO_MODE: true,            // Demo mode support
        BULK_OPERATIONS: true,      // Bulk server operations
        GAMBLING_GAMES: true,       // Gambling system
        CLAN_MANAGEMENT: true,      // Clan system
        USER_ADMINISTRATION: true   // User management
    },

    // Debug Configuration
    DEBUG: {
        ENABLED: false,
        LOG_LEVEL: 'info',          // 'debug', 'info', 'warn', 'error'
        LOG_API_CALLS: false,
        LOG_STATE_CHANGES: false,
        LOG_EVENTS: false
    },

    // Performance Configuration
    PERFORMANCE: {
        DEBOUNCE_DELAY: 300,        // Input debounce delay in ms
        THROTTLE_DELAY: 100,        // Event throttling delay in ms
        BATCH_SIZE: 50,             // Batch size for bulk operations
        MAX_RETRIES: 3,             // Max retry attempts for failed requests
        RETRY_DELAY: 1000           // Delay between retries in ms
    },

    // UI Configuration
    UI: {
        ANIMATION_DURATION: 300,    // Default animation duration in ms
        TOAST_DURATION: 5000,       // Toast notification duration in ms
        LOADING_DELAY: 500,         // Delay before showing loading indicator
        SCROLL_BEHAVIOR: 'smooth',  // Scroll behavior
        THEME: 'dark'               // Default theme
    }
};

// Environment-specific overrides
if (typeof window !== 'undefined') {
    // Browser environment
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        Config.DEBUG.ENABLED = true;
        Config.DEBUG.LOG_LEVEL = 'debug';
    }
}

// Freeze configuration to prevent modification
Object.freeze(Config);

export default Config;