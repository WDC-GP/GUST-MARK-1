/**
 * GUST Bot Enhanced - Base Component Class
 * =======================================
 * Foundation class for all UI components in the GUST Bot system.
 * Provides common functionality for lifecycle management,event handling,* state management,and error handling.
 */
class BaseComponent{/**
 * Initialize a new component
 * @param{string}containerId - ID of the DOM element to render into
 * @param{Object}options - Component configuration options
 */
 constructor(containerId,options ={}){this.containerId = containerId;this.container = document.getElementById(containerId);this.options ={...this.defaultOptions,...options};this.state = this.getInitialState();this.eventListeners = [];this.isInitialized = false;this.isDestroyed = false;this.api = options.api || window.App?.api || this.createMockAPI();this.eventBus = options.eventBus || window.App?.eventBus || this.createMockEventBus();this.stateManager = options.stateManager || window.App?.stateManager;if(!this.container){throw new Error(`Container element '${containerId}' not found`);}if(this.options.autoInit !== false){this.init();}}/**
 * Default options for all components
 */
 get defaultOptions(){return{autoInit: true,autoLoad: true,showLoader: true,errorContainer: null,className: '',templateSelector: null,debugMode: false};}/**
 * Get initial state for the component
 * Override in subclasses to provide component-specific initial state
 */
 getInitialState(){return{loading: false,error: null,data: null,initialized: false};}/**
 * Initialize the component
 * Main lifecycle method that sets up the component
 */
 async init(){if(this.isInitialized){console.warn(`Component ${this.constructor.name}already initialized`);return;}try{this.log('Initializing component...');this.container.classList.add('component',this.constructor.name.toLowerCase());if(this.options.className){this.container.classList.add(this.options.className);}await this.onBeforeInit();this.render();this.bindEvents();if(this.options.autoLoad){await this.loadData();}this.setState({initialized: true});this.isInitialized = true;await this.onReady();this.log('Component initialized successfully');}catch (error){this.handleError(error,'initialization');}}/**
 * Render the component HTML
 * Must be implemented by subclasses
 */
 render(){throw new Error(`render() method must be implemented in ${this.constructor.name}`);}/**
 * Bind event listeners
 * Override in subclasses to add component-specific event handling
 */
 bindEvents(){this.log('Binding events (base implementation)');}/**
 * Load component data
 * Override in subclasses to implement data loading logic
 */
 async loadData(){this.log('Loading data (base implementation)');}/**
 * Called before component initialization
 * Hook for setup logic that needs to run before rendering
 */
 async onBeforeInit(){}/**
 * Called when component is fully initialized and ready
 * Hook for post-initialization logic
 */
 async onReady(){this.container.classList.add('component-ready');this.eventBus.emit(`component:ready:${this.constructor.name.toLowerCase()}`,{component: this,containerId: this.containerId});}/**
 * Update component state and trigger re-render if needed
 * @param{Object}newState - Partial state to merge with current state
 * @param{boolean}shouldRender - Whether to trigger re-render
 */
 setState(newState,shouldRender = false){const oldState ={...this.state};this.state ={...this.state,...newState};this.log('State updated:',{oldState,newState: this.state});this.onStateChange(oldState,this.state);if(shouldRender){this.renderUpdate();}}/**
 * Called when state changes
 * Override in subclasses to react to state changes
 * @param{Object}oldState - Previous state
 * @param{Object}newState - Current state
 */
 onStateChange(oldState,newState){if(newState.loading !== oldState.loading){if(newState.loading){this.showLoader();}else{this.hideLoader();}}if(newState.error !== oldState.error){if(newState.error){this.showError(newState.error);}else{this.hideError();}}}/**
 * Render updates without full re-render
 * Override in subclasses for efficient partial updates
 */
 renderUpdate(){this.log('Rendering update (base implementation)');}/**
 * Add event listener with automatic cleanup tracking
 * @param{Element}element - Target element
 * @param{string}event - Event type
 * @param{Function}handler - Event handler
 * @param{Object}options - Event listener options
 */
 addEventListener(element,event,handler,options ={}){if(!element){console.error('Cannot add event listener to null element');return;}element.addEventListener(event,handler,options);this.eventListeners.push({element,event,handler,options});this.log(`Added event listener: ${event}`);}/**
 * Remove specific event listener
 * @param{Element}element - Target element
 * @param{string}event - Event type
 * @param{Function}handler - Event handler
 */
 removeEventListener(element,event,handler){element.removeEventListener(event,handler);this.eventListeners = this.eventListeners.filter(listener => 
 !(listener.element === element && 
 listener.event === event && 
 listener.handler === handler)
 );this.log(`Removed event listener: ${event}`);}/**
 * Show loading indicator
 */
 showLoader(){if(this.options.showLoader){this.container.classList.add('loading');if(!this.container.querySelector('.component-loader')){const loader = document.createElement('div');loader.className = 'component-loader';loader.innerHTML = `
 <div class="spinner">
 <div class="bounce1"></div>
 <div class="bounce2"></div>
 <div class="bounce3"></div>
 </div>
 `;this.container.appendChild(loader);}}}/**
 * Hide loading indicator
 */
 hideLoader(){this.container.classList.remove('loading');const loader = this.container.querySelector('.component-loader');if(loader){loader.remove();}}/**
 * Show error message
 * @param{string|Error}error - Error message or Error object
 */
 showError(error){const errorMessage = error instanceof Error ? error.message : error;this.hideError();if(this.options.errorContainer){const errorElement = document.getElementById(this.options.errorContainer);if(errorElement){errorElement.textContent = errorMessage;errorElement.classList.remove('hidden');return;}}const errorDiv = document.createElement('div');errorDiv.className = 'component-error bg-red-800 border border-red-600 text-red-200 p-3 rounded mb-4';errorDiv.innerHTML = `
 <div class="flex items-center justify-between">
 <span>❌ ${this.escapeHtml(errorMessage)}</span>
 <button class="error-close text-red-300 hover:text-red-100 ml-2" type="button">×</button>
 </div>
 `;const closeBtn = errorDiv.querySelector('.error-close');closeBtn.addEventListener('click',() => this.hideError());this.container.insertBefore(errorDiv,this.container.firstChild);}/**
 * Hide error message
 */
 hideError(){if(this.options.errorContainer){const errorElement = document.getElementById(this.options.errorContainer);if(errorElement){errorElement.classList.add('hidden');}}const errorElements = this.container.querySelectorAll('.component-error');errorElements.forEach(el => el.remove());}/**
 * Handle errors with logging and user feedback
 * @param{Error}error - Error object
 * @param{string}context - Context where error occurred
 */
 handleError(error,context = 'unknown'){const errorMessage = error instanceof Error ? error.message : String(error);const fullMessage = `Error in ${this.constructor.name}(${context}): ${errorMessage}`;console.error(fullMessage,error);this.setState({error: errorMessage,loading: false});this.eventBus.emit('component:error',{component: this.constructor.name,error: errorMessage,context,containerId: this.containerId});this.showError(this.getUserFriendlyError(error));}/**
 * Convert technical errors to user-friendly messages
 * @param{Error}error - Error object
 * @returns{string}User-friendly error message
 */
 getUserFriendlyError(error){if(error.status){switch (error.status){case 401: return 'Authentication required. Please log in again.';case 403: return 'Access denied. You don\'t have permission for this action.';case 404: return 'Resource not found. It may have been deleted or moved.';case 408: return 'Request timeout. Please check your connection and try again.';case 429: return 'Too many requests. Please wait a moment and try again.';case 500: return 'Server error. Please try again later.';case 503: return 'Service unavailable. Please try again later.';}}if(error.message){if(error.message.includes('fetch')){return 'Network error. Please check your connection.';}if(error.message.includes('JSON')){return 'Data format error. Please refresh the page.';}}return 'An unexpected error occurred. Please try again.';}/**
 * Show notification message
 * @param{string}message - Notification message
 * @param{string}type - Notification type (success,warning,error,info)
 */
 showNotification(message,type = 'info'){this.eventBus.emit('notification:show',{message,type,source: this.constructor.name});}/**
 * Escape HTML to prevent XSS
 * @param{string}text - Text to escape
 * @returns{string}Escaped text
 */
 escapeHtml(text){if(!text) return '';const div = document.createElement('div');div.textContent = text;return div.innerHTML;}/**
 * Debug logging
 * @param{...any}args - Arguments to log
 */
 log(...args){if(this.options.debugMode || (window.App && window.App.debugMode)){}}/**
 * Get element within component
 * @param{string}selector - CSS selector
 * @returns{Element|null}Found element or null
 */
 $(selector){return this.container.querySelector(selector);}/**
 * Get all elements within component matching selector
 * @param{string}selector - CSS selector
 * @returns{NodeList}Found elements
 */
 $$(selector){return this.container.querySelectorAll(selector);}/**
 * Create mock API for testing/demo mode
 */
 createMockAPI(){return{get: () => Promise.resolve({}),post: () => Promise.resolve({}),put: () => Promise.resolve({}),delete: () => Promise.resolve({})};}/**
 * Create mock event bus for testing
 */
 createMockEventBus(){return{on: () =>{},off: () =>{},emit: () =>{}};}/**
 * Destroy component and clean up resources
 */
 destroy(){if(this.isDestroyed){console.warn(`Component ${this.constructor.name}already destroyed`);return;}this.log('Destroying component...');this.onBeforeDestroy();this.eventListeners.forEach(({element,event,handler,options}) =>{try{element.removeEventListener(event,handler,options);}catch (error){console.warn('Error removing event listener:',error);}});this.eventListeners = [];if(this.container){this.container.innerHTML = '';this.container.classList.remove(
 'component','component-ready','loading',this.constructor.name.toLowerCase()
 );if(this.options.className){this.container.classList.remove(this.options.className);}}this.state ={};this.isDestroyed = true;this.isInitialized = false;this.eventBus.emit(`component:destroyed:${this.constructor.name.toLowerCase()}`,{component: this,containerId: this.containerId});this.onDestroy();this.log('Component destroyed');}/**
 * Called before component destruction
 * Hook for cleanup logic that needs to run before destruction
 */
 onBeforeDestroy(){}/**
 * Called after component destruction
 * Hook for final cleanup logic
 */
 onDestroy(){}/**
 * Refresh/reload the component
 */
 async refresh(){this.log('Refreshing component...');try{this.setState({loading: true,error: null});await this.loadData();this.renderUpdate();this.setState({loading: false});this.log('Component refreshed successfully');}catch (error){this.handleError(error,'refresh');}}/**
 * Check if component is in a specific state
 * @param{string}stateName - State property name
 * @returns{boolean}State value
 */
 isInState(stateName){return Boolean(this.state[stateName]);}/**
 * Get component information for debugging
 * @returns{Object}Component info
 */
 getInfo(){return{name: this.constructor.name,containerId: this.containerId,isInitialized: this.isInitialized,isDestroyed: this.isDestroyed,state:{...this.state},options:{...this.options},eventListenerCount: this.eventListeners.length};}}if(typeof module !== 'undefined' && module.exports){module.exports = BaseComponent;}else{window.BaseComponent = BaseComponent;}