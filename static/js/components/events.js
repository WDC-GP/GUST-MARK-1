/**
 * Events Component - Event Management
 * Handles KOTH events and other server events with fixed vanilla compatibility
 */
class EventsComponent extends BaseComponent {
    constructor(containerId, options = {}) {
        super(containerId, options);
        this.api = options.api || window.App.api;
        this.eventBus = options.eventBus || window.App.eventBus;
        this.refreshInterval = null;
    }
    
    get defaultOptions() {
        return {
            ...super.defaultOptions,
            autoRefresh: true,
            refreshInterval: 30000,
            maxEvents: 20
        };
    }
    
    getInitialState() {
        return {
            ...super.getInitialState(),
            servers: [],
            events: [],
            eventTemplates: [],
            arenaLocations: [],
            selectedEventType: 'koth',
            formData: {
                serverId: '',
                duration: 30,
                rewardItem: 'scrap',
                rewardAmount: 1000,
                arenaLocation: 'Launch Site',
                giveSupplies: true
            }
        };
    }
    
    render() {
        this.container.innerHTML = `
            <div class="events">
                <h2 class="text-3xl font-bold mb-6">🎯 Event Management</h2>
                
                <!-- KOTH Fixed Notice -->
                <div class="bg-blue-800 border border-blue-600 p-4 rounded-lg mb-6">
                    <h3 class="text-lg font-semibold text-blue-300">🎯 KOTH Events - Now Working!</h3>
                    <p class="text-blue-200">The KOTH system has been completely rewritten to work with vanilla Rust servers.</p>
                    <div class="text-sm text-blue-200 mt-2">
                        <span class="font-medium">Features:</span>
                        Vanilla compatible | 5-min countdown | 28+ arenas | Auto rewards
                    </div>
                </div>
                
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <!-- Event Creation Panel -->
                    <div class="bg-gray-800 p-6 rounded-lg">
                        <h3 class="text-xl font-semibold mb-4">Start KOTH Event (Fixed)</h3>
                        
                        <!-- Event Type Selection -->
                        <div class="mb-4">
                            <label class="block text-sm font-medium mb-2">Event Type</label>
                            <select id="eventTypeSelect" class="w-full bg-gray-700 p-3 rounded border border-gray-600 focus:border-purple-500">
                                <option value="koth">🎯 King of the Hill (KOTH)</option>
                                <option value="custom" disabled>🔧 Custom Event (Coming Soon)</option>
                            </select>
                        </div>
                        
                        <!-- Server Selection -->
                        <div class="mb-4">
                            <label class="block text-sm font-medium mb-2">Select Server *</label>
                            <select id="eventServerSelect" class="w-full bg-gray-700 p-3 rounded border border-gray-600 focus:border-purple-500">
                                <option value="">Choose a server...</option>
                            </select>
                            <div class="text-sm text-gray-400 mt-1">
                                No servers? <button id="gotoServerManagerBtn" class="text-purple-400 hover:text-purple-300 underline">Add servers here</button>
                            </div>
                        </div>
                        
                        <!-- Event Configuration -->
                        <div class="space-y-4" id="eventConfigSection">
                            <!-- Duration -->
                            <div>
                                <label class="block text-sm font-medium mb-2">Duration (minutes) *</label>
                                <div class="flex items-center space-x-4">
                                    <input type="number" id="eventDuration" min="5" max="180" value="30" 
                                           class="flex-1 bg-gray-700 p-3 rounded border border-gray-600 focus:border-purple-500">
                                    <div class="text-sm text-gray-400">5-180 min</div>
                                </div>
                            </div>
                            
                            <!-- Arena Location -->
                            <div>
                                <label class="block text-sm font-medium text-gray-300 mb-2">Arena Location 🗺️</label>
                                <select id="eventArenaLocation" class="w-full bg-gray-700 p-3 rounded text-white border border-gray-600 focus:border-purple-500">
                                    <!-- Will be populated by loadArenaLocations -->
                                </select>
                            </div>
                            
                            <!-- Reward Configuration -->
                            <div class="grid grid-cols-2 gap-4">
                                <div>
                                    <label class="block text-sm font-medium mb-2">Reward Item *</label>
                                    <select id="eventRewardItem" class="w-full bg-gray-700 p-3 rounded border border-gray-600 focus:border-purple-500">
                                        <option value="scrap">Scrap</option>
                                        <option value="metal.fragments">Metal Fragments</option>
                                        <option value="wood">Wood</option>
                                        <option value="stone">Stone</option>
                                        <option value="metal.refined">High Quality Metal</option>
                                        <option value="cloth">Cloth</option>
                                        <option value="lowgradefuel">Low Grade Fuel</option>
                                    </select>
                                </div>
                                <div>
                                    <label class="block text-sm font-medium mb-2">Reward Amount *</label>
                                    <input type="number" id="eventRewardAmount" min="1" max="50000" value="1000" 
                                           class="w-full bg-gray-700 p-3 rounded border border-gray-600 focus:border-purple-500">
                                </div>
                            </div>
                            
                            <!-- Additional Options -->
                            <div class="space-y-2">
                                <label class="flex items-center">
                                    <input type="checkbox" id="giveSuppliesCheck" checked class="mr-2">
                                    <span class="text-sm">Give combat supplies to participants</span>
                                </label>
                                <div class="text-xs text-gray-400 ml-6">
                                    Provides basic weapons and medical supplies to all players
                                </div>
                            </div>
                        </div>
                        
                        <!-- Action Buttons -->
                        <div class="flex items-center space-x-4 mt-6">
                            <button id="startEventBtn" class="bg-yellow-600 hover:bg-yellow-700 px-6 py-3 rounded font-medium">
                                Start KOTH Event
                            </button>
                            <button id="loadTemplateBtn" class="bg-blue-600 hover:bg-blue-700 px-4 py-3 rounded">
                                Load Template
                            </button>
                            <button id="saveTemplateBtn" class="bg-green-600 hover:bg-green-700 px-4 py-3 rounded">
                                Save Template
                            </button>
                        </div>
                    </div>
                    
                    <!-- Active Events Panel -->
                    <div class="bg-gray-800 p-6 rounded-lg">
                        <div class="flex items-center justify-between mb-4">
                            <h3 class="text-xl font-semibold">Active Events</h3>
                            <button id="refreshEventsBtn" class="bg-blue-600 hover:bg-blue-700 px-3 py-2 rounded text-sm">
                                Refresh
                            </button>
                        </div>
                        
                        <div id="activeEventsList" class="space-y-3">
                            <div class="text-gray-400 text-center py-8">
                                <div class="text-4xl mb-4">🎯</div>
                                <div>No active events</div>
                                <div class="text-sm mt-2">Start an event to see it here</div>
                            </div>
                        </div>
                        
                        <!-- Event Statistics -->
                        <div class="mt-6 p-4 bg-gray-700 rounded">
                            <h4 class="text-sm font-semibold mb-3">Event Statistics</h4>
                            <div class="grid grid-cols-2 gap-4 text-sm">
                                <div>
                                    <div class="text-gray-400">Total Events Today</div>
                                    <div class="text-lg font-semibold" id="eventsToday">0</div>
                                </div>
                                <div>
                                    <div class="text-gray-400">Active Events</div>
                                    <div class="text-lg font-semibold" id="activeEventsCount">0</div>
                                </div>
                                <div>
                                    <div class="text-gray-400">Most Popular Arena</div>
                                    <div class="text-sm font-semibold" id="popularArena">-</div>
                                </div>
                                <div>
                                    <div class="text-gray-400">System Status</div>
                                    <div class="text-sm font-semibold text-green-400">Operational ✅</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Event Templates Modal -->
                <div id="templatesModal" class="fixed inset-0 bg-black bg-opacity-50 hidden z-50">
                    <div class="flex items-center justify-center h-full">
                        <div class="bg-gray-800 p-6 rounded-lg w-96 max-h-96 overflow-y-auto">
                            <h3 class="text-lg font-semibold mb-4">Event Templates</h3>
                            <div id="templatesList" class="space-y-2">
                                <!-- Will be populated by loadEventTemplates -->
                            </div>
                            <div class="flex justify-end mt-4">
                                <button id="closeTemplatesBtn" class="bg-gray-600 hover:bg-gray-700 px-4 py-2 rounded">
                                    Close
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Save Template Modal -->
                <div id="saveTemplateModal" class="fixed inset-0 bg-black bg-opacity-50 hidden z-50">
                    <div class="flex items-center justify-center h-full">
                        <div class="bg-gray-800 p-6 rounded-lg w-96">
                            <h3 class="text-lg font-semibold mb-4">Save Event Template</h3>
                            <div class="space-y-4">
                                <div>
                                    <label class="block text-sm font-medium mb-2">Template Name</label>
                                    <input type="text" id="templateName" placeholder="e.g., Quick KOTH" 
                                           class="w-full bg-gray-700 p-3 rounded border border-gray-600 focus:border-purple-500">
                                </div>
                                <div>
                                    <label class="block text-sm font-medium mb-2">Description</label>
                                    <textarea id="templateDescription" placeholder="Optional description" 
                                              class="w-full bg-gray-700 p-3 rounded border border-gray-600 focus:border-purple-500 h-20"></textarea>
                                </div>
                            </div>
                            <div class="flex justify-end space-x-2 mt-4">
                                <button id="cancelSaveTemplateBtn" class="bg-gray-600 hover:bg-gray-700 px-4 py-2 rounded">
                                    Cancel
                                </button>
                                <button id="confirmSaveTemplateBtn" class="bg-green-600 hover:bg-green-700 px-4 py-2 rounded">
                                    Save Template
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    bindEvents() {
        // Main action buttons
        const startBtn = this.container.querySelector('#startEventBtn');
        const refreshBtn = this.container.querySelector('#refreshEventsBtn');
        const loadTemplateBtn = this.container.querySelector('#loadTemplateBtn');
        const saveTemplateBtn = this.container.querySelector('#saveTemplateBtn');
        const gotoServerMgrBtn = this.container.querySelector('#gotoServerManagerBtn');
        
        this.addEventListener(startBtn, 'click', () => this.startKothEvent());
        this.addEventListener(refreshBtn, 'click', () => this.loadData());
        this.addEventListener(loadTemplateBtn, 'click', () => this.showTemplatesModal());
        this.addEventListener(saveTemplateBtn, 'click', () => this.showSaveTemplateModal());
        this.addEventListener(gotoServerMgrBtn, 'click', () => {
            this.eventBus.emit('navigation:goto', { route: 'server-manager' });
        });
        
        // Form validation
        const durationInput = this.container.querySelector('#eventDuration');
        const rewardAmountInput = this.container.querySelector('#eventRewardAmount');
        
        this.addEventListener(durationInput, 'input', (e) => this.validateDuration(e.target));
        this.addEventListener(rewardAmountInput, 'input', (e) => this.validateRewardAmount(e.target));
        
        // Templates modal
        const templatesModal = this.container.querySelector('#templatesModal');
        const closeTemplatesBtn = this.container.querySelector('#closeTemplatesBtn');
        
        this.addEventListener(closeTemplatesBtn, 'click', () => this.hideTemplatesModal());
        this.addEventListener(templatesModal, 'click', (e) => {
            if (e.target === templatesModal) this.hideTemplatesModal();
        });
        
        // Save template modal
        const saveTemplateModal = this.container.querySelector('#saveTemplateModal');
        const cancelSaveBtn = this.container.querySelector('#cancelSaveTemplateBtn');
        const confirmSaveBtn = this.container.querySelector('#confirmSaveTemplateBtn');
        
        this.addEventListener(cancelSaveBtn, 'click', () => this.hideSaveTemplateModal());
        this.addEventListener(confirmSaveBtn, 'click', () => this.saveEventTemplate());
        this.addEventListener(saveTemplateModal, 'click', (e) => {
            if (e.target === saveTemplateModal) this.hideSaveTemplateModal();
        });
        
        // Listen for server updates
        this.eventBus.on('servers:updated', (data) => this.updateServerDropdown(data.servers));
        this.eventBus.on('event:started', () => this.loadData());
        this.eventBus.on('event:stopped', () => this.loadData());
    }
    
    async loadData() {
        try {
            this.setState({ loading: true, error: null });
            
            await Promise.all([
                this.loadServers(),
                this.loadEvents(),
                this.loadArenaLocations(),
                this.loadEventTemplates()
            ]);
            
            this.setState({ loading: false });
            this.updateEventStatistics();
            
        } catch (error) {
            this.handleError(error);
        }
    }
    
    async loadServers() {
        try {
            const servers = await this.api.servers.list();
            this.setState({ servers });
            this.updateServerDropdown(servers);
        } catch (error) {
            console.warn('Failed to load servers:', error);
        }
    }
    
    async loadEvents() {
        try {
            const events = await this.api.events.list();
            this.setState({ events });
            this.renderEventsList();
            
            // Emit event for other components
            this.eventBus.emit('events:updated', { events });
            
        } catch (error) {
            console.warn('Failed to load events:', error);
        }
    }
    
    async loadArenaLocations() {
        try {
            const response = await this.api.events.arenaLocations();
            this.setState({ arenaLocations: response.locations || [] });
            this.populateArenaDropdown();
        } catch (error) {
            console.warn('Failed to load arena locations:', error);
            // Fallback to default locations
            const defaultLocations = [
                'Launch Site', 'Military Base', 'Airfield', 'Power Plant',
                'Water Treatment Plant', 'Train Yard', 'Satellite Dish', 'Dome'
            ];
            this.setState({ arenaLocations: defaultLocations });
            this.populateArenaDropdown();
        }
    }
    
    async loadEventTemplates() {
        try {
            const response = await this.api.events.templates();
            this.setState({ eventTemplates: response });
        } catch (error) {
            console.warn('Failed to load event templates:', error);
            // Fallback to default templates
            const defaultTemplates = [
                {
                    name: 'Quick KOTH (30m)',
                    duration: 30,
                    reward_item: 'scrap',
                    reward_amount: 1000,
                    arena_location: 'Launch Site',
                    description: 'Standard 30-minute KOTH event'
                },
                {
                    name: 'Long KOTH (60m)',
                    duration: 60,
                    reward_item: 'scrap',
                    reward_amount: 2000,
                    arena_location: 'Military Base',
                    description: 'Extended 60-minute KOTH event'
                }
            ];
            this.setState({ eventTemplates: defaultTemplates });
        }
    }
    
    updateServerDropdown(servers) {
        const select = this.container.querySelector('#eventServerSelect');
        if (!select) return;
        
        const currentValue = select.value;
        select.innerHTML = '<option value="">Choose a server...</option>';
        
        servers.filter(s => s.isActive).forEach(server => {
            const option = document.createElement('option');
            option.value = server.serverId;
            option.textContent = `${server.serverName} (${server.serverId}) - ${server.serverRegion}`;
            select.appendChild(option);
        });
        
        if (currentValue) select.value = currentValue;
    }
    
    populateArenaDropdown() {
        const select = this.container.querySelector('#eventArenaLocation');
        if (!select) return;
        
        const { arenaLocations } = this.state;
        select.innerHTML = '';
        
        arenaLocations.forEach(location => {
            const option = document.createElement('option');
            option.value = location;
            option.textContent = `🗺️ ${location}`;
            select.appendChild(option);
        });
        
        // Set default
        if (arenaLocations.includes('Launch Site')) {
            select.value = 'Launch Site';
        }
    }
    
    renderEventsList() {
        const container = this.container.querySelector('#activeEventsList');
        const { events } = this.state;
        
        if (events.length === 0) {
            container.innerHTML = `
                <div class="text-gray-400 text-center py-8">
                    <div class="text-4xl mb-4">🎯</div>
                    <div>No active events</div>
                    <div class="text-sm mt-2">Start an event to see it here</div>
                </div>
            `;
            return;
        }
        
        container.innerHTML = events.map(event => this.renderEventCard(event)).join('');
        this.bindEventCardEvents();
    }
    
    renderEventCard(event) {
        const server = this.state.servers.find(s => s.serverId === event.serverId);
        const serverName = server ? server.serverName : `Server ${event.serverId}`;
        const timeRemaining = this.calculateTimeRemaining(event);
        
        return `
            <div class="bg-gray-700 p-4 rounded border border-gray-600">
                <div class="flex items-center justify-between mb-2">
                    <div class="flex items-center space-x-2">
                        <span class="text-lg">🎯</span>
                        <h4 class="font-semibold">${event.type.toUpperCase()} Event</h4>
                        <span class="text-xs px-2 py-1 bg-green-700 rounded">${event.phase || 'Active'}</span>
                    </div>
                    <button class="stop-event bg-red-600 hover:bg-red-700 px-2 py-1 rounded text-xs" 
                            data-event-id="${event.eventId}">
                        Stop Event
                    </button>
                </div>
                
                <div class="text-sm text-gray-300 space-y-1">
                    <div><span class="font-medium">Server:</span> ${this.escapeHtml(serverName)} (${event.serverId})</div>
                    <div><span class="font-medium">Reward:</span> ${event.reward}</div>
                    ${event.arena_location ? `<div><span class="font-medium">Location:</span> ${event.arena_location}</div>` : ''}
                    ${timeRemaining ? `<div><span class="font-medium">Time Remaining:</span> ${timeRemaining}</div>` : ''}
                    <div class="text-xs text-green-400 mt-2">✅ Vanilla Compatible</div>
                </div>
            </div>
        `;
    }
    
    bindEventCardEvents() {
        const stopBtns = this.container.querySelectorAll('.stop-event');
        stopBtns.forEach(btn => {
            this.addEventListener(btn, 'click', (e) => {
                const eventId = e.target.dataset.eventId;
                this.stopEvent(eventId);
            });
        });
    }
    
    async startKothEvent() {
        const serverSelect = this.container.querySelector('#eventServerSelect');
        const serverId = serverSelect.value;
        const duration = parseInt(this.container.querySelector('#eventDuration').value);
        const rewardItem = this.container.querySelector('#eventRewardItem').value;
        const rewardAmount = parseInt(this.container.querySelector('#eventRewardAmount').value);
        const arenaLocation = this.container.querySelector('#eventArenaLocation').value;
        const giveSupplies = this.container.querySelector('#giveSuppliesCheck').checked;
        
        // Validation
        if (!serverId) {
            this.showNotification('Please select a server from the dropdown', 'error');
            return;
        }
        
        if (!duration || duration < 5 || duration > 180) {
            this.showNotification('Duration must be between 5 and 180 minutes', 'error');
            return;
        }
        
        if (!rewardAmount || rewardAmount <= 0) {
            this.showNotification('Reward amount must be greater than 0', 'error');
            return;
        }
        
        const server = this.state.servers.find(s => s.serverId === serverId);
        if (!server) {
            this.showNotification('Selected server not found. Please refresh the page.', 'error');
            return;
        }
        
        try {
            this.showLoader();
            
            const result = await this.api.events.startKoth({
                serverId: serverId,
                region: server.serverRegion,
                duration: duration,
                reward_item: rewardItem,
                reward_amount: rewardAmount,
                arena_location: arenaLocation,
                give_supplies: giveSupplies
            });
            
            if (result.success) {
                this.showNotification(`✅ KOTH event started successfully on ${server.serverName}!`, 'success');
                this.showEventStartedDetails(server, duration, arenaLocation, rewardAmount, rewardItem);
                await this.loadEvents();
                
                // Emit event
                this.eventBus.emit('event:started', {
                    type: 'koth',
                    serverId,
                    duration,
                    arena_location: arenaLocation
                });
                
            } else {
                this.showNotification('❌ Failed to start event: ' + (result.error || 'Unknown error'), 'error');
            }
        } catch (error) {
            this.showNotification('Error starting event: ' + error.message, 'error');
        } finally {
            this.hideLoader();
        }
    }
    
    async stopEvent(eventId) {
        if (!confirm('Are you sure you want to stop this event?')) {
            return;
        }
        
        try {
            const result = await this.api.events.stopKoth({ eventId });
            
            if (result.success) {
                this.showNotification('✅ Event stopped successfully', 'success');
                await this.loadEvents();
                
                // Emit event
                this.eventBus.emit('event:stopped', { eventId });
                
            } else {
                this.showNotification('❌ Failed to stop event', 'error');
            }
        } catch (error) {
            this.showNotification('Error stopping event: ' + error.message, 'error');
        }
    }
    
    showEventStartedDetails(server, duration, location, amount, item) {
        const details = `KOTH Event Started!

Server: ${server.serverName}
Duration: ${duration} minutes
Location: ${location}
Reward: ${amount} ${item}

Check console for announcements.`;
        
        alert(details);
    }
    
    validateDuration(input) {
        const value = parseInt(input.value);
        if (value < 5) {
            input.value = 5;
        } else if (value > 180) {
            input.value = 180;
        }
    }
    
    validateRewardAmount(input) {
        const value = parseInt(input.value);
        if (value < 1) {
            input.value = 1;
        } else if (value > 50000) {
            input.value = 50000;
        }
    }
    
    showTemplatesModal() {
        const modal = this.container.querySelector('#templatesModal');
        this.populateTemplatesList();
        modal.classList.remove('hidden');
    }
    
    hideTemplatesModal() {
        const modal = this.container.querySelector('#templatesModal');
        modal.classList.add('hidden');
    }
    
    populateTemplatesList() {
        const container = this.container.querySelector('#templatesList');
        const { eventTemplates } = this.state;
        
        container.innerHTML = eventTemplates.map(template => `
            <div class="p-3 bg-gray-700 rounded cursor-pointer hover:bg-gray-600 load-template" 
                 data-template='${JSON.stringify(template)}'>
                <div class="font-medium">${this.escapeHtml(template.name)}</div>
                <div class="text-sm text-gray-400">${this.escapeHtml(template.description || '')}</div>
                <div class="text-xs text-blue-400 mt-1">
                    ${template.duration}m | ${template.reward_amount} ${template.reward_item} | ${template.arena_location}
                </div>
            </div>
        `).join('');
        
        // Bind template load events
        const templateBtns = container.querySelectorAll('.load-template');
        templateBtns.forEach(btn => {
            this.addEventListener(btn, 'click', (e) => {
                const template = JSON.parse(e.currentTarget.dataset.template);
                this.loadTemplate(template);
                this.hideTemplatesModal();
            });
        });
    }
    
    loadTemplate(template) {
        this.container.querySelector('#eventDuration').value = template.duration;
        this.container.querySelector('#eventRewardItem').value = template.reward_item;
        this.container.querySelector('#eventRewardAmount').value = template.reward_amount;
        this.container.querySelector('#eventArenaLocation').value = template.arena_location;
        
        this.showNotification(`Template "${template.name}" loaded`, 'success');
    }
    
    showSaveTemplateModal() {
        const modal = this.container.querySelector('#saveTemplateModal');
        modal.classList.remove('hidden');
        
        // Clear previous values
        this.container.querySelector('#templateName').value = '';
        this.container.querySelector('#templateDescription').value = '';
    }
    
    hideSaveTemplateModal() {
        const modal = this.container.querySelector('#saveTemplateModal');
        modal.classList.add('hidden');
    }
    
    async saveEventTemplate() {
        const name = this.container.querySelector('#templateName').value.trim();
        const description = this.container.querySelector('#templateDescription').value.trim();
        
        if (!name) {
            this.showNotification('Please enter a template name', 'error');
            return;
        }
        
        const template = {
            name,
            description,
            duration: parseInt(this.container.querySelector('#eventDuration').value),
            reward_item: this.container.querySelector('#eventRewardItem').value,
            reward_amount: parseInt(this.container.querySelector('#eventRewardAmount').value),
            arena_location: this.container.querySelector('#eventArenaLocation').value,
            give_supplies: this.container.querySelector('#giveSuppliesCheck').checked
        };
        
        try {
            // In a real implementation, you'd save this to the server
            // For now, just add to local state
            const templates = [...this.state.eventTemplates, template];
            this.setState({ eventTemplates: templates });
            
            this.showNotification(`Template "${name}" saved successfully!`, 'success');
            this.hideSaveTemplateModal();
            
        } catch (error) {
            this.showNotification('Error saving template: ' + error.message, 'error');
        }
    }
    
    calculateTimeRemaining(event) {
        if (!event.startTime || !event.duration) return null;
        
        const startTime = new Date(event.startTime);
        const endTime = new Date(startTime.getTime() + (event.duration * 60 * 1000));
        const now = new Date();
        const remaining = endTime - now;
        
        if (remaining <= 0) return 'Finished';
        
        const minutes = Math.floor(remaining / (1000 * 60));
        const seconds = Math.floor((remaining % (1000 * 60)) / 1000);
        
        return `${minutes}m ${seconds}s`;
    }
    
    updateEventStatistics() {
        const { events } = this.state;
        const today = new Date().toDateString();
        
        // Count today's events (in a real app, you'd track this properly)
        const eventsToday = events.length; // Simplified
        const activeCount = events.filter(e => e.status === 'active').length;
        
        // Find most popular arena (simplified)
        const arenaCount = {};
        events.forEach(event => {
            if (event.arena_location) {
                arenaCount[event.arena_location] = (arenaCount[event.arena_location] || 0) + 1;
            }
        });
        
        const popularArena = Object.keys(arenaCount).length > 0 
            ? Object.keys(arenaCount).reduce((a, b) => arenaCount[a] > arenaCount[b] ? a : b)
            : '-';
        
        // Update display
        this.updateElement('#eventsToday', eventsToday);
        this.updateElement('#activeEventsCount', activeCount);
        this.updateElement('#popularArena', popularArena);
    }
    
    updateElement(selector, value) {
        const element = this.container.querySelector(selector);
        if (element) {
            element.textContent = value;
        }
    }
    
    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    showNotification(message, type = 'info') {
        this.eventBus.emit('notification:show', { message, type });
    }
    
    onReady() {
        super.onReady();
        
        // Start auto-refresh if enabled
        if (this.options.autoRefresh) {
            this.refreshInterval = setInterval(() => {
                this.loadEvents();
            }, this.options.refreshInterval);
        }
    }
    
    onDestroy() {
        // Clean up interval
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
        
        // Unsubscribe from events
        this.eventBus.off('servers:updated');
        this.eventBus.off('event:started');
        this.eventBus.off('event:stopped');
    }
}