/**
 * GUST Bot Enhanced - Main Application Controller
 * =============================================
 * Central application controller and initialization
 */

import { Config } from './config.js';
import { API } from './api.js';
import { Router } from './router.js';
import { StateManager } from './state-manager.js';
import { EventBus } from './event-bus.js';
import { Utils } from './utils.js';

class GustApp {
    constructor() {
        this.state = new StateManager();
        this.api = new API();
        this.router = new Router();
        this.eventBus = new EventBus();
        this.utils = new Utils();
        
        // Application state
        this.initialized = false;
        this.pollingIntervals = new Map();
    }

    /**
     * Initialize the application
     */
    async init() {
        if (this.initialized) return;

        try {
            console.log('🚀 Initializing GUST Bot Enhanced...');
            
            // Initialize components
            await this.initializeComponents();
            
            // Setup event listeners
            this.setupEventListeners();
            
            // Load initial data
            await this.loadInitialData();
            
            // Start background processes
            this.startBackgroundTasks();
            
            // Mark as initialized
            this.initialized = true;
            
            console.log('✅ GUST Bot Enhanced initialized successfully');
            
            // Emit initialization complete event
            this.eventBus.emit('app:initialized');
            
        } catch (error) {
            console.error('❌ Failed to initialize application:', error);
            this.eventBus.emit('app:error', { error, context: 'initialization' });
        }
    }

    /**
     * Initialize core components
     */
    async initializeComponents() {
        // Initialize router
        this.router.init();
        
        // Initialize state manager
        this.state.init();
        
        // Check system status
        await this.checkSystemStatus();
        
        // Initialize live console if available
        if (this.state.get('websocketsAvailable')) {
            console.log('📺 WebSocket support available - initializing live console...');
            setTimeout(() => {
                this.initializeLiveConsole();
            }, Config.DELAYS.LIVE_CONSOLE_INIT);
        }
    }

    /**
     * Setup global event listeners
     */
    setupEventListeners() {
        // DOM Content Loaded
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                this.setupDOMEventListeners();
            });
        } else {
            this.setupDOMEventListeners();
        }

        // Window events
        window.addEventListener('beforeunload', () => {
            this.cleanup();
        });

        // Application events
        this.eventBus.on('servers:updated', () => {
            this.onServersUpdated();
        });

        this.eventBus.on('route:changed', (data) => {
            this.onRouteChanged(data);
        });

        this.eventBus.on('connection:status', (data) => {
            this.onConnectionStatusChanged(data);
        });
    }

    /**
     * Setup DOM event listeners
     */
    setupDOMEventListeners() {
        // Form submissions
        this.setupFormEventListeners();
        
        // Button clicks
        this.setupButtonEventListeners();
        
        // Input changes
        this.setupInputEventListeners();
        
        // Keyboard shortcuts
        this.setupKeyboardEventListeners();
    }

    /**
     * Setup form event listeners
     */
    setupFormEventListeners() {
        // Server form
        const serverFormInputs = ['newServerId', 'newServerName', 'newServerDescription'];
        serverFormInputs.forEach(inputId => {
            const input = document.getElementById(inputId);
            if (input) {
                input.addEventListener('keypress', (e) => {
                    if (e.key === 'Enter') {
                        this.eventBus.emit('server:add');
                    }
                });
            }
        });

        // Console input
        const consoleInput = document.getElementById('consoleInput');
        if (consoleInput) {
            consoleInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.eventBus.emit('console:sendCommand');
                }
            });
        }
    }

    /**
     * Setup button event listeners
     */
    setupButtonEventListeners() {
        // Navigation tabs
        document.querySelectorAll('.nav-tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                const tabName = e.target.id.replace('-tab', '');
                this.router.navigate(tabName);
            });
        });
    }

    /**
     * Setup input event listeners
     */
    setupInputEventListeners() {
        // Message type filter
        const messageTypeFilter = document.getElementById('consoleMessageTypeFilter');
        if (messageTypeFilter) {
            messageTypeFilter.addEventListener('change', (e) => {
                this.state.set('messageTypeFilter', e.target.value);
                this.eventBus.emit('console:filterChanged');
            });
        }

        // Server filter
        const serverFilter = document.getElementById('monitorServerFilter');
        if (serverFilter) {
            serverFilter.addEventListener('change', (e) => {
                this.state.set('serverFilter', e.target.value);
                this.eventBus.emit('console:filterChanged');
            });
        }

        // Auto-scroll checkbox
        const autoScrollCheck = document.getElementById('consoleAutoScroll');
        if (autoScrollCheck) {
            autoScrollCheck.addEventListener('change', (e) => {
                this.state.set('autoScroll', e.target.checked);
            });
        }
    }

    /**
     * Setup keyboard event listeners
     */
    setupKeyboardEventListeners() {
        document.addEventListener('keydown', (e) => {
            // Ctrl+R or F5 - Refresh current view
            if ((e.ctrlKey && e.key === 'r') || e.key === 'F5') {
                e.preventDefault();
                this.refreshCurrentView();
            }
            
            // Escape - Clear console or close modals
            if (e.key === 'Escape') {
                this.eventBus.emit('ui:escape');
            }
        });
    }

    /**
     * Load initial application data
     */
    async loadInitialData() {
        try {
            // Load managed servers
            await this.loadManagedServers();
            
            // Update system status
            await this.updateSystemStatus();
            
            // Load dashboard data if on dashboard
            if (this.router.getCurrentRoute() === 'dashboard') {
                await this.loadDashboardData();
            }
            
        } catch (error) {
            console.error('❌ Error loading initial data:', error);
        }
    }

    /**
     * Load managed servers and auto-connect
     */
    async loadManagedServers() {
        try {
            const servers = await this.api.getServers();
            this.state.set('managedServers', servers);
            
            // Update all server dropdowns
            this.updateAllServerDropdowns();
            
            // Auto-connect to servers if WebSockets available
            if (this.state.get('websocketsAvailable')) {
                await this.autoConnectToAllServers();
            }
            
            console.log(`📋 Loaded ${servers.length} managed servers`);
            
        } catch (error) {
            console.error('❌ Error loading managed servers:', error);
            this.state.set('managedServers', []);
        }
    }

    /**
     * Auto-connect to all active servers
     */
    async autoConnectToAllServers() {
        const servers = this.state.get('managedServers', []);
        
        for (const server of servers) {
            if (server.isActive) {
                await this.autoConnectToServer(server);
                // Delay between connections
                await this.utils.delay(Config.DELAYS.SERVER_CONNECTION);
            }
        }
    }

    /**
     * Auto-connect to a specific server
     */
    async autoConnectToServer(server) {
        try {
            console.log(`🔄 Auto-connecting to ${server.serverName} (${server.serverId})`);
            
            const result = await this.api.connectLiveConsole(server.serverId, server.serverRegion);
            
            if (result.success) {
                console.log(`✅ Auto-connected to ${server.serverName}`);
                this.addSystemMessage(`🔄 Auto-connected to ${server.serverName} for live monitoring`);
            } else if (!result.error?.includes('demo')) {
                console.log(`❌ Auto-connect failed for ${server.serverName}: ${result.error}`);
                this.addSystemMessage(`⚠️ Auto-connect failed for ${server.serverName}: ${result.error}`);
            }
            
        } catch (error) {
            console.error(`Error auto-connecting to ${server.serverName}:`, error);
        }
    }

    /**
     * Start background tasks
     */
    startBackgroundTasks() {
        // Console refresh for live messages
        this.pollingIntervals.set('console', setInterval(() => {
            if (this.router.getCurrentRoute() === 'console') {
                this.eventBus.emit('console:refresh');
            }
        }, Config.POLLING.CONSOLE_REFRESH));

        // Connection status updates
        this.pollingIntervals.set('connections', setInterval(() => {
            this.updateConnectionStatus();
        }, Config.POLLING.CONNECTION_STATUS));

        // Auto-reconnect check
        this.pollingIntervals.set('reconnect', setInterval(() => {
            this.checkAndReconnectServers();
        }, Config.POLLING.RECONNECT_CHECK));

        // System status updates
        this.pollingIntervals.set('system', setInterval(() => {
            this.updateSystemStatus();
        }, Config.POLLING.SYSTEM_STATUS));

        console.log('📅 Background tasks started');
    }

    /**
     * Check system status
     */
    async checkSystemStatus() {
        try {
            const status = await this.api.getTokenStatus();
            this.state.set('tokenStatus', status);
            this.state.set('websocketsAvailable', status.websockets_available);
            this.state.set('demoMode', status.demo_mode);
            
        } catch (error) {
            console.error('Error checking system status:', error);
        }
    }

    /**
     * Update system status
     */
    async updateSystemStatus() {
        await this.checkSystemStatus();
        this.eventBus.emit('ui:updateSystemStatus');
    }

    /**
     * Update connection status
     */
    async updateConnectionStatus() {
        if (!this.state.get('websocketsAvailable')) return;
        
        try {
            const status = await this.api.getLiveConsoleStatus();
            this.state.set('connectionStatus', status.connections || {});
            this.eventBus.emit('connections:updated', status);
            
        } catch (error) {
            console.error('Error updating connection status:', error);
        }
    }

    /**
     * Check and reconnect servers
     */
    async checkAndReconnectServers() {
        if (!this.state.get('websocketsAvailable')) return;
        
        try {
            const status = await this.api.getLiveConsoleStatus();
            const connectedServerIds = Object.keys(status.connections || {});
            const activeServerIds = this.state.get('managedServers', [])
                .filter(s => s.isActive)
                .map(s => s.serverId);

            // Reconnect disconnected servers
            for (const serverId of activeServerIds) {
                if (!connectedServerIds.includes(serverId)) {
                    const server = this.getServerById(serverId);
                    if (server) {
                        console.log(`🔄 Auto-reconnecting to ${server.serverName}`);
                        await this.autoConnectToServer(server);
                        await this.utils.delay(1000);
                    }
                }
            }
            
        } catch (error) {
            console.error('Error checking connections for auto-reconnect:', error);
        }
    }

    /**
     * Initialize live console functionality
     */
    initializeLiveConsole() {
        console.log('📺 Initializing live console functionality...');
        this.eventBus.emit('console:initializeLive');
    }

    /**
     * Load dashboard data
     */
    async loadDashboardData() {
        try {
            // Load stats in parallel
            const [events, clans] = await Promise.all([
                this.api.getEvents().catch(() => []),
                this.api.getClans().catch(() => [])
            ]);

            this.state.set('activeEvents', events);
            this.state.set('totalClans', clans);
            
            this.eventBus.emit('dashboard:dataLoaded');
            
        } catch (error) {
            console.error('Error loading dashboard data:', error);
        }
    }

    /**
     * Update all server dropdowns
     */
    updateAllServerDropdowns() {
        const servers = this.state.get('managedServers', []);
        const dropdowns = Config.SERVER_DROPDOWNS;
        
        dropdowns.forEach(dropdownId => {
            const dropdown = document.getElementById(dropdownId);
            if (!dropdown) return;
            
            const currentValue = dropdown.value;
            const firstOption = dropdown.querySelector('option:first-child');
            
            // Clear and rebuild
            dropdown.innerHTML = '';
            if (firstOption) {
                dropdown.appendChild(firstOption.cloneNode(true));
            }
            
            // Add server options
            servers.filter(server => server.isActive).forEach(server => {
                const option = document.createElement('option');
                option.value = server.serverId;
                option.textContent = `${server.serverName} (${server.serverId}) - ${server.serverRegion}`;
                
                if (server.status === 'online') {
                    option.textContent += ' ✅';
                } else if (server.status === 'offline') {
                    option.textContent += ' ❌';
                }
                
                dropdown.appendChild(option);
            });
            
            // Restore selection
            if (currentValue) {
                dropdown.value = currentValue;
            }
        });
    }

    /**
     * Get server by ID
     */
    getServerById(serverId) {
        const servers = this.state.get('managedServers', []);
        return servers.find(server => server.serverId === serverId);
    }

    /**
     * Add system message to console
     */
    addSystemMessage(message) {
        this.eventBus.emit('console:addMessage', {
            timestamp: new Date().toISOString(),
            message: message,
            type: 'system',
            source: 'app'
        });
    }

    /**
     * Refresh current view
     */
    refreshCurrentView() {
        const currentRoute = this.router.getCurrentRoute();
        this.eventBus.emit(`${currentRoute}:refresh`);
    }

    /**
     * Event handlers
     */
    onServersUpdated() {
        this.updateAllServerDropdowns();
    }

    onRouteChanged(data) {
        // Load route-specific data
        if (data.route === 'dashboard') {
            this.loadDashboardData();
        }
    }

    onConnectionStatusChanged(data) {
        // Update UI indicators
        this.eventBus.emit('ui:updateConnectionIndicators', data);
    }

    /**
     * Cleanup resources
     */
    cleanup() {
        // Clear intervals
        this.pollingIntervals.forEach((interval, key) => {
            clearInterval(interval);
        });
        this.pollingIntervals.clear();
        
        // Cleanup components
        this.eventBus.cleanup();
        
        console.log('🧹 Application cleanup completed');
    }

    /**
     * Get application instance
     */
    static getInstance() {
        if (!GustApp.instance) {
            GustApp.instance = new GustApp();
        }
        return GustApp.instance;
    }
}

// Initialize app when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        const app = GustApp.getInstance();
        app.init();
        
        // Make app globally available for debugging
        window.gustApp = app;
    });
} else {
    const app = GustApp.getInstance();
    app.init();
    window.gustApp = app;
}

export { GustApp };