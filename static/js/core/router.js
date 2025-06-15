/**
 * GUST Bot Enhanced - Navigation and Routing
 * =========================================
 * Client-side routing and navigation management
 */

import { Config } from './config.js';
import { EventBus } from './event-bus.js';

export class Router {
    constructor() {
        this.currentRoute = Config.ROUTES.DEFAULT;
        this.previousRoute = null;
        this.routes = new Map();
        this.beforeRouteHooks = [];
        this.afterRouteHooks = [];
        this.eventBus = new EventBus();
        this.initialized = false;
    }

    /**
     * Initialize the router
     */
    init() {
        if (this.initialized) return;

        // Register default routes
        this.registerDefaultRoutes();
        
        // Setup event listeners
        this.setupEventListeners();
        
        // Navigate to initial route
        this.navigateToInitialRoute();
        
        this.initialized = true;
        console.log('🧭 Router initialized');
    }

    /**
     * Register default application routes
     */
    registerDefaultRoutes() {
        // Dashboard
        this.register('dashboard', {
            title: '📊 Dashboard',
            element: 'dashboard-view',
            tab: 'dashboard-tab',
            beforeEnter: () => this.loadDashboardData(),
            afterEnter: () => this.updateDashboardUI()
        });

        // Server Manager
        this.register('server-manager', {
            title: '🖥️ Server Manager',
            element: 'server-manager-view',
            tab: 'server-manager-tab',
            beforeEnter: () => this.loadServerManager(),
            afterEnter: () => this.updateServerManagerUI()
        });

        // Console
        this.register('console', {
            title: '🔧 Console & Live Monitor',
            element: 'console-view',
            tab: 'console-tab',
            beforeEnter: () => this.initializeConsole(),
            afterEnter: () => this.updateConsoleUI()
        });

        // Events
        this.register('events', {
            title: '🎯 Events',
            element: 'events-view',
            tab: 'events-tab',
            beforeEnter: () => this.loadEvents(),
            afterEnter: () => this.updateEventsUI()
        });

        // Economy
        this.register('economy', {
            title: '💰 Economy',
            element: 'economy-view',
            tab: 'economy-tab',
            beforeEnter: () => this.loadEconomy(),
            afterEnter: () => this.updateEconomyUI()
        });

        // Gambling
        this.register('gambling', {
            title: '🎰 Gambling',
            element: 'gambling-view',
            tab: 'gambling-tab',
            beforeEnter: () => this.loadGambling(),
            afterEnter: () => this.updateGamblingUI()
        });

        // Clans
        this.register('clans', {
            title: '🛡️ Clans',
            element: 'clans-view',
            tab: 'clans-tab',
            beforeEnter: () => this.loadClans(),
            afterEnter: () => this.updateClansUI()
        });

        // User Management
        this.register('bans', {
            title: '🚫 User Mgmt',
            element: 'bans-view',
            tab: 'bans-tab',
            beforeEnter: () => this.loadUserManagement(),
            afterEnter: () => this.updateUserManagementUI()
        });
    }

    /**
     * Register a new route
     */
    register(name, config) {
        if (!name || !config) {
            throw new Error('Route name and configuration are required');
        }

        this.routes.set(name, {
            name,
            title: config.title || name,
            element: config.element,
            tab: config.tab,
            beforeEnter: config.beforeEnter || (() => {}),
            afterEnter: config.afterEnter || (() => {}),
            beforeLeave: config.beforeLeave || (() => {}),
            afterLeave: config.afterLeave || (() => {})
        });

        if (Config.DEBUG.ENABLED) {
            console.log(`🧭 Route registered: ${name}`);
        }
    }

    /**
     * Navigate to a route
     */
    async navigate(routeName, options = {}) {
        if (!this.routes.has(routeName)) {
            console.error(`❌ Route not found: ${routeName}`);
            return false;
        }

        const route = this.routes.get(routeName);
        const { force = false, silent = false } = options;

        // Don't navigate if already on the same route (unless forced)
        if (this.currentRoute === routeName && !force) {
            return true;
        }

        try {
            // Execute before route hooks
            for (const hook of this.beforeRouteHooks) {
                const result = await hook(routeName, this.currentRoute);
                if (result === false) {
                    return false; // Navigation cancelled
                }
            }

            // Execute current route's beforeLeave hook
            if (this.currentRoute && this.routes.has(this.currentRoute)) {
                const currentRoute = this.routes.get(this.currentRoute);
                await currentRoute.beforeLeave();
            }

            // Store previous route
            this.previousRoute = this.currentRoute;
            
            // Execute new route's beforeEnter hook
            await route.beforeEnter();

            // Update UI
            this.updateUI(routeName);

            // Update current route
            this.currentRoute = routeName;

            // Execute new route's afterEnter hook
            await route.afterEnter();

            // Execute after route hooks
            for (const hook of this.afterRouteHooks) {
                await hook(routeName, this.previousRoute);
            }

            // Emit navigation event
            if (!silent) {
                this.eventBus.emit('route:changed', {
                    route: routeName,
                    previousRoute: this.previousRoute
                });
            }

            if (Config.DEBUG.ENABLED) {
                console.log(`🧭 Navigated to: ${routeName}`);
            }

            return true;

        } catch (error) {
            console.error(`❌ Navigation error to ${routeName}:`, error);
            return false;
        }
    }

    /**
     * Update UI for route change
     */
    updateUI(routeName) {
        const route = this.routes.get(routeName);
        
        // Update navigation tabs
        document.querySelectorAll('.nav-tab').forEach(tab => {
            tab.classList.remove('active');
        });
        
        const activeTab = document.getElementById(route.tab);
        if (activeTab) {
            activeTab.classList.add('active');
        }

        // Update views
        document.querySelectorAll('.view').forEach(view => {
            view.classList.add('hidden');
        });

        const activeView = document.getElementById(route.element);
        if (activeView) {
            activeView.classList.remove('hidden');
            // Add fade-in animation
            activeView.classList.add('fade-in');
            setTimeout(() => {
                activeView.classList.remove('fade-in');
            }, Config.UI.ANIMATION_DURATION);
        }

        // Update page title
        if (route.title) {
            document.title = `${route.title} - ${Config.APP.NAME}`;
        }
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Handle back/forward browser buttons
        window.addEventListener('popstate', (event) => {
            const route = event.state?.route || Config.ROUTES.DEFAULT;
            this.navigate(route, { silent: true });
        });

        // Handle hash changes
        window.addEventListener('hashchange', () => {
            const hash = window.location.hash.substring(1);
            if (hash && this.routes.has(hash)) {
                this.navigate(hash);
            }
        });
    }

    /**
     * Navigate to initial route
     */
    navigateToInitialRoute() {
        // Check URL hash first
        const hash = window.location.hash.substring(1);
        if (hash && this.routes.has(hash)) {
            this.navigate(hash, { silent: true });
            return;
        }

        // Navigate to default route
        this.navigate(Config.ROUTES.DEFAULT, { silent: true });
    }

    /**
     * Add before route hook
     */
    beforeEach(hook) {
        if (typeof hook === 'function') {
            this.beforeRouteHooks.push(hook);
        }
    }

    /**
     * Add after route hook
     */
    afterEach(hook) {
        if (typeof hook === 'function') {
            this.afterRouteHooks.push(hook);
        }
    }

    /**
     * Get current route
     */
    getCurrentRoute() {
        return this.currentRoute;
    }

    /**
     * Get previous route
     */
    getPreviousRoute() {
        return this.previousRoute;
    }

    /**
     * Check if route exists
     */
    hasRoute(routeName) {
        return this.routes.has(routeName);
    }

    /**
     * Get route configuration
     */
    getRoute(routeName) {
        return this.routes.get(routeName);
    }

    /**
     * Get all routes
     */
    getAllRoutes() {
        return Array.from(this.routes.keys());
    }

    /**
     * Go back to previous route
     */
    goBack() {
        if (this.previousRoute && this.routes.has(this.previousRoute)) {
            this.navigate(this.previousRoute);
        }
    }

    /**
     * Refresh current route
     */
    refresh() {
        this.navigate(this.currentRoute, { force: true });
    }

    // ===========================================
    // ROUTE HANDLERS
    // ===========================================

    /**
     * Dashboard route handlers
     */
    async loadDashboardData() {
        this.eventBus.emit('dashboard:beforeLoad');
    }

    updateDashboardUI() {
        this.eventBus.emit('dashboard:load');
    }

    /**
     * Server Manager route handlers
     */
    async loadServerManager() {
        this.eventBus.emit('server-manager:beforeLoad');
    }

    updateServerManagerUI() {
        this.eventBus.emit('server-manager:load');
    }

    /**
     * Console route handlers
     */
    async initializeConsole() {
        this.eventBus.emit('console:beforeInit');
    }

    updateConsoleUI() {
        this.eventBus.emit('console:load');
    }

    /**
     * Events route handlers
     */
    async loadEvents() {
        this.eventBus.emit('events:beforeLoad');
    }

    updateEventsUI() {
        this.eventBus.emit('events:load');
    }

    /**
     * Economy route handlers
     */
    async loadEconomy() {
        this.eventBus.emit('economy:beforeLoad');
    }

    updateEconomyUI() {
        this.eventBus.emit('economy:load');
    }

    /**
     * Gambling route handlers
     */
    async loadGambling() {
        this.eventBus.emit('gambling:beforeLoad');
    }

    updateGamblingUI() {
        this.eventBus.emit('gambling:load');
    }

    /**
     * Clans route handlers
     */
    async loadClans() {
        this.eventBus.emit('clans:beforeLoad');
    }

    updateClansUI() {
        this.eventBus.emit('clans:load');
    }

    /**
     * User Management route handlers
     */
    async loadUserManagement() {
        this.eventBus.emit('user-management:beforeLoad');
    }

    updateUserManagementUI() {
        this.eventBus.emit('user-management:load');
    }

    // ===========================================
    // UTILITIES
    // ===========================================

    /**
     * Set URL hash without triggering navigation
     */
    setHash(hash) {
        history.replaceState({ route: hash }, '', `#${hash}`);
    }

    /**
     * Push state to browser history
     */
    pushState(route) {
        history.pushState({ route }, '', `#${route}`);
    }

    /**
     * Check if we can navigate away from current route
     */
    async canNavigateAway() {
        if (!this.currentRoute || !this.routes.has(this.currentRoute)) {
            return true;
        }

        const route = this.routes.get(this.currentRoute);
        try {
            const result = await route.beforeLeave();
            return result !== false;
        } catch (error) {
            console.error('Error in beforeLeave hook:', error);
            return true; // Allow navigation on error
        }
    }

    /**
     * Get navigation breadcrumbs
     */
    getBreadcrumbs() {
        const breadcrumbs = [];
        
        if (this.previousRoute) {
            const previousRoute = this.routes.get(this.previousRoute);
            breadcrumbs.push({
                name: this.previousRoute,
                title: previousRoute.title,
                isCurrent: false
            });
        }
        
        if (this.currentRoute) {
            const currentRoute = this.routes.get(this.currentRoute);
            breadcrumbs.push({
                name: this.currentRoute,
                title: currentRoute.title,
                isCurrent: true
            });
        }
        
        return breadcrumbs;
    }

    /**
     * Cleanup router
     */
    cleanup() {
        this.beforeRouteHooks = [];
        this.afterRouteHooks = [];
        this.routes.clear();
        console.log('🧭 Router cleaned up');
    }
}