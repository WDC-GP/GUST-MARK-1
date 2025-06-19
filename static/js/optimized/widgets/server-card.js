/**
 * Server Card Widget
 * Displays individual server information with actions
 */
class ServerCard extends BaseComponent{constructor(containerId,server,options ={}){super(containerId,options);this.server = server;this.eventBus = options.eventBus || window.App.eventBus;this.statusIndicator = null;}get defaultOptions(){return{...super.defaultOptions,showActions: true,showStatus: true,showStats: true,enableSelection: false,compact: false};}getInitialState(){return{...super.getInitialState(),server: this.server,isSelected: false,isConnected: false,lastPing: null,actionInProgress: null};}render(){const{server}= this.state;const{compact,showActions,showStatus,showStats,enableSelection}= this.options;this.container.innerHTML = `
 <div class="server-card ${compact ? 'server-card--compact' : ''}${this.state.isSelected ? 'server-card--selected' : ''}"
 data-server-id="${server.serverId}">
 ${enableSelection ? `
 <div class="server-card__selection">
 <input type="checkbox" id="select-${server.serverId}" 
 class="server-checkbox"
 ${this.state.isSelected ? 'checked' : ''}>
 </div>
 ` : ''}<!-- Header -->
 <div class="server-card__header">
 <div class="server-card__title">
 <h3 class="server-card__name" title="${server.serverName}">
 ${this.truncateText(server.serverName,25)}</h3>
 ${server.isFavorite ? '<i class="icon-star text-yellow-400" title="Favorite"></i>' : ''}</div>
 ${showStatus ? `
 <div class="server-card__status" id="status-${server.serverId}">
 <!-- Status indicator will be rendered here -->
 </div>
 ` : ''}</div>
 <!-- Server Info -->
 <div class="server-card__info">
 <div class="server-info-grid">
 <div class="server-info-item">
 <span class="server-info-label">ID:</span>
 <span class="server-info-value" title="${server.serverId}">
 ${server.serverId}</span>
 </div>
 <div class="server-info-item">
 <span class="server-info-label">Region:</span>
 <span class="server-info-value">
 ${this.getRegionDisplay(server.serverRegion)}</span>
 </div>
 <div class="server-info-item">
 <span class="server-info-label">Type:</span>
 <span class="server-info-value">
 ${server.serverType || 'Standard'}</span>
 </div>
 ${server.description ? `
 <div class="server-info-item server-info-item--full">
 <span class="server-info-label">Description:</span>
 <span class="server-info-value text-sm text-gray-400">
 ${this.truncateText(server.description,50)}</span>
 </div>
 ` : ''}${showStats && server.playerCount !== undefined ? `
 <div class="server-info-item">
 <span class="server-info-label">Players:</span>
 <span class="server-info-value">
 ${server.playerCount}/${server.maxPlayers || '?'}</span>
 </div>
 ` : ''}${this.state.lastPing ? `
 <div class="server-info-item">
 <span class="server-info-label">Last Ping:</span>
 <span class="server-info-value text-xs">
 ${this.formatRelativeTime(this.state.lastPing)}</span>
 </div>
 ` : ''}</div>
 </div>
 <!-- Live Connection Indicator -->
 <div class="server-card__connection">
 <div class="connection-indicator ${this.state.isConnected ? 'connection-indicator--active' : ''}">
 <i class="icon-wifi"></i>
 <span class="connection-text">
 ${this.state.isConnected ? 'Live Connected' : 'Not Connected'}</span>
 </div>
 </div>
 <!-- Actions -->
 ${showActions ? `
 <div class="server-card__actions">
 <div class="server-actions-grid">
 <button class="btn-action btn-action--primary" 
 data-action="ping" 
 title="Ping Server"
 ${this.state.actionInProgress === 'ping' ? 'disabled' : ''}>
 <i class="icon-pulse"></i>
 <span>Ping</span>
 </button>
 <button class="btn-action btn-action--info" 
 data-action="console" 
 title="Open Console">
 <i class="icon-terminal"></i>
 <span>Console</span>
 </button>
 <button class="btn-action btn-action--success" 
 data-action="connect" 
 title="Connect Live Console"
 ${this.state.isConnected ? 'disabled' : ''}>
 <i class="icon-plug"></i>
 <span>Connect</span>
 </button>
 <button class="btn-action btn-action--warning" 
 data-action="edit" 
 title="Edit Server">
 <i class="icon-edit"></i>
 <span>Edit</span>
 </button>
 <button class="btn-action btn-action--danger" 
 data-action="delete" 
 title="Delete Server">
 <i class="icon-trash"></i>
 <span>Delete</span>
 </button>
 </div>
 </div>
 ` : ''}<!-- Loading Overlay -->
 <div class="server-card__loading ${this.state.actionInProgress ? 'active' : ''}">
 <div class="loading-spinner"></div>
 <span class="loading-text">
 ${this.getActionText(this.state.actionInProgress)}</span>
 </div>
 </div>
 `;if(showStatus){this.initializeStatusIndicator();}}bindEvents(){const actionButtons = this.container.querySelectorAll('[data-action]');actionButtons.forEach(button =>{const action = button.dataset.action;this.addEventListener(button,'click',(e) =>{e.stopPropagation();this.handleAction(action);});});if(this.options.enableSelection){const checkbox = this.container.querySelector('.server-checkbox');this.addEventListener(checkbox,'change',(e) =>{this.handleSelection(e.target.checked);});}this.addEventListener(this.container,'click',() =>{this.handleCardClick();});this.addEventListener(this.container,'contextmenu',(e) =>{e.preventDefault();this.showContextMenu(e);});this.eventBus.on('server:updated',(data) =>{if(data.serverId === this.server.serverId){this.updateServer(data.server);}});this.eventBus.on('server:status-changed',(data) =>{if(data.serverId === this.server.serverId){this.updateStatus(data.status);}});this.eventBus.on('server:connection-changed',(data) =>{if(data.serverId === this.server.serverId){this.updateConnectionStatus(data.connected);}});}initializeStatusIndicator(){const container = this.container.querySelector(`#status-${this.server.serverId}`);if(container){this.statusIndicator = new StatusIndicator(container,{status: this.server.status || 'unknown',showText: true,animate: true});}}async handleAction(action){if(this.state.actionInProgress){return;}this.setState({actionInProgress: action});try{switch (action){case 'ping':
 await this.pingServer();break;case 'console':
 this.openConsole();break;case 'connect':
 await this.connectLiveConsole();break;case 'edit':
 this.editServer();break;case 'delete':
 await this.deleteServer();break;default:
 console.warn(`Unknown action: ${action}`);}}catch (error){this.handleError(error);}finally{this.setState({actionInProgress: null});}}async pingServer(){try{const result = await this.api.servers.ping(this.server.serverId);if(result.success){this.setState({lastPing: new Date().toISOString()});this.updateStatus(result.status);this.showNotification('Server pinged successfully','success');this.eventBus.emit('server:pinged',{serverId: this.server.serverId,status: result.status,timestamp: new Date().toISOString()});}else{this.showNotification('Ping failed','error');}}catch (error){this.showNotification('Failed to ping server','error');throw error;}}openConsole(){this.eventBus.emit('navigation:goto',{tab: 'console',serverId: this.server.serverId});}async connectLiveConsole(){try{const result = await this.api.console.liveConnect({serverId: this.server.serverId,region: this.server.serverRegion});if(result.success){this.updateConnectionStatus(true);this.showNotification('Live console connected','success');this.eventBus.emit('server:live-connected',{serverId: this.server.serverId});}else{this.showNotification(result.error || 'Connection failed','error');}}catch (error){this.showNotification('Failed to connect live console','error');throw error;}}editServer(){this.eventBus.emit('server:edit-requested',{server: this.server});}async deleteServer(){const confirmed = await this.showConfirmDialog(
 'Delete Server',`Are you sure you want to delete "${this.server.serverName}"?\n\nThis action cannot be undone.`
 );if(!confirmed){return;}try{const result = await this.api.servers.delete(this.server.serverId);if(result.success){this.showNotification('Server deleted successfully','success');this.eventBus.emit('server:deleted',{serverId: this.server.serverId,server: this.server});this.animateRemoval();}else{this.showNotification('Failed to delete server','error');}}catch (error){this.showNotification('Failed to delete server','error');throw error;}}handleSelection(selected){this.setState({isSelected: selected});this.container.classList.toggle('server-card--selected',selected);this.eventBus.emit('server:selection-changed',{serverId: this.server.serverId,selected: selected});}handleCardClick(){if(!this.options.enableSelection){this.openConsole();}}showContextMenu(event){const menuItems = [{label: 'Open Console',action: 'console',icon: 'icon-terminal'},{label: 'Ping Server',action: 'ping',icon: 'icon-pulse'},{label: 'Connect Live',action: 'connect',icon: 'icon-plug'},{type: 'separator'},{label: 'Edit Server',action: 'edit',icon: 'icon-edit'},{label: 'Delete Server',action: 'delete',icon: 'icon-trash',destructive: true}];this.eventBus.emit('context-menu:show',{x: event.clientX,y: event.clientY,items: menuItems,onSelect: (action) => this.handleAction(action)});}updateServer(serverData){this.server ={...this.server,...serverData};this.setState({server: this.server});this.render();}updateStatus(status){this.server.status = status;if(this.statusIndicator){this.statusIndicator.updateStatus(status);}if(status === 'online'){this.setState({lastPing: new Date().toISOString()});}}updateConnectionStatus(connected){this.setState({isConnected: connected});const indicator = this.container.querySelector('.connection-indicator');if(indicator){indicator.classList.toggle('connection-indicator--active',connected);const text = indicator.querySelector('.connection-text');if(text){text.textContent = connected ? 'Live Connected' : 'Not Connected';}}const connectBtn = this.container.querySelector('[data-action="connect"]');if(connectBtn){connectBtn.disabled = connected;}}getRegionDisplay(region){const regionMap ={'US': '🇺🇸 United States','EU': '🇪🇺 Europe','AS': '🌏 Asia'};return regionMap[region] || region;}getActionText(action){const actionTexts ={ping: 'Pinging server...',connect: 'Connecting...',delete: 'Deleting server...'};return actionTexts[action] || 'Processing...';}truncateText(text,maxLength){if(!text) return '';return text.length > maxLength ? text.substring(0,maxLength) + '...' : text;}formatRelativeTime(timestamp){const now = new Date();const time = new Date(timestamp);const diffMs = now - time;const diffMins = Math.floor(diffMs / 60000);if(diffMins < 1) return 'Just now';if(diffMins < 60) return `${diffMins}m ago`;if(diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`;return `${Math.floor(diffMins / 1440)}d ago`;}animateRemoval(){this.container.style.transition = 'all 0.3s ease-out';this.container.style.transform = 'scale(0)';this.container.style.opacity = '0';setTimeout(() =>{if(this.container.parentNode){this.container.parentNode.removeChild(this.container);}},300);}async showConfirmDialog(title,message){return new Promise((resolve) =>{this.eventBus.emit('modal:confirm',{title,message,onConfirm: () => resolve(true),onCancel: () => resolve(false)});});}showNotification(message,type = 'info'){this.eventBus.emit('notification:show',{message,type});}onDestroy(){if(this.statusIndicator){this.statusIndicator.destroy();}this.eventBus.off('server:updated');this.eventBus.off('server:status-changed');this.eventBus.off('server:connection-changed');}}