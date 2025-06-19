/**
 * GUST Bot Enhanced - Clan Management Component
 * =============================================
 * Modular component for clan creation,management,and member operations
 */
class ClansComponent extends BaseComponent{constructor(containerId,options ={}){super(containerId,options);this.api = options.api || window.App.api;this.eventBus = options.eventBus || window.App.eventBus;this.stateManager = options.stateManager || window.App.stateManager;this.servers = options.servers || [];}get defaultOptions(){return{...super.defaultOptions,enableClanCreation: true,enableMemberManagement: true,maxClanNameLength: 50,maxDescriptionLength: 200,showClanStats: true,refreshInterval: 30000};}getInitialState(){return{...super.getInitialState(),clans: [],selectedClan: null,newClanName: '',newClanLeader: '',newClanServerId: '',newClanDescription: '',memberToAdd: '',memberToRemove: '',filterText: '',sortBy: 'name',sortDirection: 'asc',serverFilter: '',stats:{}};}render(){this.container.innerHTML = `
 <div class="clans-management">
 <div class="clans-header">
 <h2 class="text-3xl font-bold mb-6">🛡️ Clan Management</h2>
 <div class="clans-info bg-blue-800 border border-blue-600 p-4 rounded-lg mb-6">
 <p class="text-blue-200">
 <strong>🛡️ Clan System:</strong> Create and manage player clans across your servers. 
 Clans help organize communities and foster teamwork.
 </p>
 </div>
 </div>
 <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
 <!-- Create Clan Section -->
 ${this.options.enableClanCreation ? this.renderCreateClanSection() : ''}<!-- Clan Management Section -->
 <div class="bg-gray-800 p-6 rounded-lg">
 <h3 class="text-xl font-semibold mb-4">🛡️ Active Clans</h3>
 <!-- Filters -->
 <div class="clans-filters mb-4 space-y-2">
 <div class="flex flex-col sm:flex-row gap-2">
 <input type="text" 
 id="clanFilter" 
 placeholder="Filter clans..." 
 class="flex-1 bg-gray-700 p-2 rounded border border-gray-600 focus:border-purple-500"
 value="${this.state.filterText}">
 <select id="serverFilter" 
 class="bg-gray-700 p-2 rounded border border-gray-600 focus:border-purple-500">
 <option value="">All Servers</option>
 ${this.renderServerOptions()}</select>
 </div>
 <div class="flex gap-2 text-sm">
 <button id="sortByName" 
 class="px-3 py-1 rounded ${this.state.sortBy === 'name' ? 'bg-purple-600' : 'bg-gray-600'}">
 Name
 </button>
 <button id="sortByMembers" 
 class="px-3 py-1 rounded ${this.state.sortBy === 'memberCount' ? 'bg-purple-600' : 'bg-gray-600'}">
 Members
 </button>
 <button id="sortByCreated" 
 class="px-3 py-1 rounded ${this.state.sortBy === 'createdDate' ? 'bg-purple-600' : 'bg-gray-600'}">
 Created
 </button>
 </div>
 </div>
 <!-- Clans List -->
 <div id="clansList" class="space-y-3 max-h-96 overflow-y-auto">
 <!-- Clans will be populated here -->
 </div>
 <button id="refreshClansBtn" 
 class="mt-4 w-full bg-blue-600 hover:bg-blue-700 p-2 rounded text-sm">
 🔄 Refresh Clans
 </button>
 </div>
 <!-- Clan Details Section -->
 <div class="bg-gray-800 p-6 rounded-lg lg:col-span-2" id="clanDetailsSection">
 <h3 class="text-xl font-semibold mb-4">📋 Clan Details</h3>
 <div id="clanDetails" class="text-gray-400 text-center py-8">
 Select a clan to view details and manage members
 </div>
 </div>
 </div>
 <!-- Clan Statistics -->
 ${this.options.showClanStats ? this.renderStatsSection() : ''}<!-- Member Management Modal -->
 ${this.options.enableMemberManagement ? this.renderMemberModal() : ''}</div>
 `;}renderCreateClanSection(){return `
 <div class="bg-gray-800 p-6 rounded-lg">
 <h3 class="text-xl font-semibold mb-4">⚔️ Create New Clan</h3>
 <div class="space-y-4">
 <div class="form-group">
 <label class="block text-sm font-medium mb-2">Clan Name *</label>
 <input type="text" 
 id="clanName" 
 placeholder="Enter clan name" 
 maxlength="${this.options.maxClanNameLength}"
 class="w-full bg-gray-700 p-3 rounded border border-gray-600 focus:border-purple-500"
 value="${this.state.newClanName}">
 <div class="text-xs text-gray-400 mt-1">
 ${this.state.newClanName.length}/${this.options.maxClanNameLength}characters
 </div>
 </div>
 <div class="form-group">
 <label class="block text-sm font-medium mb-2">Leader ID *</label>
 <input type="text" 
 id="clanLeader" 
 placeholder="Steam ID or username of clan leader" 
 class="w-full bg-gray-700 p-3 rounded border border-gray-600 focus:border-purple-500"
 value="${this.state.newClanLeader}">
 </div>
 <div class="form-group">
 <label class="block text-sm font-medium mb-2">Server *</label>
 <select id="clanServerSelect" 
 class="w-full bg-gray-700 p-3 rounded border border-gray-600 focus:border-purple-500">
 <option value="">Choose a server...</option>
 ${this.renderServerOptions()}</select>
 <div class="text-xs text-gray-400 mt-1">
 No servers? <button class="text-purple-400 hover:text-purple-300 underline" onclick="window.App.router.navigate('servers')">Manage servers</button>
 </div>
 </div>
 <div class="form-group">
 <label class="block text-sm font-medium mb-2">Description</label>
 <textarea id="clanDescription" 
 placeholder="Optional clan description" 
 maxlength="${this.options.maxDescriptionLength}"
 rows="3"
 class="w-full bg-gray-700 p-3 rounded border border-gray-600 focus:border-purple-500 resize-none">${this.state.newClanDescription}</textarea>
 <div class="text-xs text-gray-400 mt-1">
 ${this.state.newClanDescription.length}/${this.options.maxDescriptionLength}characters
 </div>
 </div>
 <button id="createClanBtn" 
 class="w-full bg-purple-600 hover:bg-purple-700 p-3 rounded font-medium">
 ⚔️ Create Clan
 </button>
 </div>
 </div>
 `;}renderStatsSection(){return `
 <div class="mt-6 bg-gray-800 p-6 rounded-lg">
 <h3 class="text-xl font-semibold mb-4">📊 Clan Statistics</h3>
 <div id="clanStats" class="grid grid-cols-2 md:grid-cols-4 gap-4">
 <!-- Stats will be populated here -->
 </div>
 </div>
 `;}renderMemberModal(){return `
 <div id="memberManagementModal" class="modal fixed inset-0 bg-black bg-opacity-50 hidden z-50">
 <div class="modal-content bg-gray-800 rounded-lg p-6 max-w-md mx-auto mt-20">
 <div class="modal-header flex items-center justify-between mb-4">
 <h3 class="text-lg font-semibold">👥 Manage Members</h3>
 <button id="closeMemberModal" class="text-gray-400 hover:text-white">✕</button>
 </div>
 <div class="modal-body">
 <div id="memberModalContent">
 <!-- Content will be populated dynamically -->
 </div>
 </div>
 </div>
 </div>
 `;}renderServerOptions(){return this.servers.map(server => 
 `<option value="${server.serverId}">${server.serverName}(${server.serverId})</option>`
 ).join('');}bindEvents(){if(this.options.enableClanCreation){const createBtn = this.container.querySelector('#createClanBtn');const nameInput = this.container.querySelector('#clanName');const leaderInput = this.container.querySelector('#clanLeader');const serverSelect = this.container.querySelector('#clanServerSelect');const descriptionInput = this.container.querySelector('#clanDescription');this.addEventListener(createBtn,'click',() => this.createClan());this.addEventListener(nameInput,'input',(e) =>{this.setState({newClanName: e.target.value});this.updateCharacterCount(e.target,this.options.maxClanNameLength);});this.addEventListener(leaderInput,'input',(e) =>{this.setState({newClanLeader: e.target.value});});this.addEventListener(serverSelect,'change',(e) =>{this.setState({newClanServerId: e.target.value});});this.addEventListener(descriptionInput,'input',(e) =>{this.setState({newClanDescription: e.target.value});this.updateCharacterCount(e.target,this.options.maxDescriptionLength);});}const filterInput = this.container.querySelector('#clanFilter');const serverFilter = this.container.querySelector('#serverFilter');const refreshBtn = this.container.querySelector('#refreshClansBtn');this.addEventListener(filterInput,'input',(e) =>{this.setState({filterText: e.target.value});this.filterAndSortClans();});this.addEventListener(serverFilter,'change',(e) =>{this.setState({serverFilter: e.target.value});this.filterAndSortClans();});this.addEventListener(refreshBtn,'click',() => this.loadData());const sortButtons = this.container.querySelectorAll('[id^="sortBy"]');sortButtons.forEach(button =>{this.addEventListener(button,'click',(e) =>{const sortBy = e.target.id.replace('sortBy','').toLowerCase();this.setSorting(sortBy === 'name' ? 'name' : sortBy === 'members' ? 'memberCount' : 'createdDate');});});if(this.options.enableMemberManagement){const closeModalBtn = this.container.querySelector('#closeMemberModal');if(closeModalBtn){this.addEventListener(closeModalBtn,'click',() => this.closeMemberModal());}}this.eventBus.on('servers:updated',() => this.updateServerOptions());this.eventBus.on('clan:member-updated',() => this.loadData());}async loadData(){try{this.setState({loading: true,error: null});await Promise.all([
 this.loadClans(),this.loadStats()
 ]);this.setState({loading: false});}catch (error){this.handleError(error);}}async loadClans(){try{const clans = await this.api.clans.list();this.setState({clans});this.renderClansList(clans);}catch (error){console.error('Failed to load clans:',error);this.renderClansList([]);}}async createClan(){const{newClanName,newClanLeader,newClanServerId,newClanDescription}= this.state;if(!this.validateClanForm()){return;}try{this.showLoader();const result = await this.api.clans.create({name: newClanName.trim(),leader: newClanLeader.trim(),serverId: newClanServerId,description: newClanDescription.trim()});if(result.success){this.showNotification('Clan created successfully!','success');this.clearCreateForm();this.eventBus.emit('clan:created',{clanId: result.clanId,name: newClanName,leader: newClanLeader});await this.loadData();}else{this.showNotification(result.error || 'Failed to create clan','error');}this.hideLoader();}catch (error){this.handleError(error);this.showNotification('Error creating clan','error');}}validateClanForm(){const{newClanName,newClanLeader,newClanServerId}= this.state;if(!newClanName.trim()){this.showNotification('Please enter a clan name','warning');return false;}if(newClanName.trim().length < 3){this.showNotification('Clan name must be at least 3 characters','warning');return false;}if(!newClanLeader.trim()){this.showNotification('Please enter a leader ID','warning');return false;}if(!newClanServerId){this.showNotification('Please select a server','warning');return false;}return true;}renderClansList(clans){const clansList = this.container.querySelector('#clansList');if(!clansList) return;const filteredClans = this.getFilteredAndSortedClans(clans || this.state.clans);if(filteredClans.length === 0){clansList.innerHTML = `
 <div class="text-gray-400 text-center py-8">
 <div class="text-4xl mb-4">🛡️</div>
 <div>No clans found</div>
 <div class="text-sm mt-2">
 ${this.state.filterText || this.state.serverFilter ? 'Try adjusting your filters' : 'Create your first clan above'}</div>
 </div>
 `;return;}clansList.innerHTML = filteredClans.map(clan => this.renderClanCard(clan)).join('');this.bindClanCardEvents();}renderClanCard(clan){const serverName = this.getServerName(clan.serverId);const memberCount = clan.memberCount || clan.members?.length || 0;const createdDate = new Date(clan.createdDate).toLocaleDateString();return `
 <div class="clan-card bg-gray-700 p-4 rounded-lg border border-gray-600 hover:border-gray-500 transition-colors"
 data-clan-id="${clan.clanId}">
 <div class="flex items-start justify-between">
 <div class="flex-1">
 <div class="flex items-center space-x-2 mb-2">
 <h4 class="font-semibold text-lg text-purple-400">${clan.name}</h4>
 <span class="text-xs px-2 py-1 bg-gray-600 rounded">${clan.isActive ? '✅ Active' : '❌ Inactive'}</span>
 </div>
 <div class="space-y-1 text-sm text-gray-300">
 <div><span class="text-gray-400">Leader:</span> ${clan.leader}</div>
 <div><span class="text-gray-400">Members:</span> ${memberCount}</div>
 <div><span class="text-gray-400">Server:</span> ${serverName}</div>
 <div><span class="text-gray-400">Created:</span> ${createdDate}</div>
 ${clan.description ? `<div class="text-xs text-gray-400 mt-2">${clan.description}</div>` : ''}</div>
 </div>
 <div class="flex flex-col space-y-2">
 <button class="clan-action-btn bg-blue-600 hover:bg-blue-700 px-3 py-1 rounded text-xs"
 data-action="view" data-clan-id="${clan.clanId}">
 📋 View
 </button>
 ${this.options.enableMemberManagement ? `
 <button class="clan-action-btn bg-green-600 hover:bg-green-700 px-3 py-1 rounded text-xs"
 data-action="manage" data-clan-id="${clan.clanId}">
 👥 Members
 </button>
 ` : ''}<button class="clan-action-btn bg-red-600 hover:bg-red-700 px-3 py-1 rounded text-xs"
 data-action="delete" data-clan-id="${clan.clanId}">
 🗑️ Delete
 </button>
 </div>
 </div>
 </div>
 `;}bindClanCardEvents(){const actionButtons = this.container.querySelectorAll('.clan-action-btn');actionButtons.forEach(button =>{this.addEventListener(button,'click',(e) =>{const action = e.target.dataset.action;const clanId = e.target.dataset.clanId;this.handleClanAction(action,clanId);});});}async handleClanAction(action,clanId){const clan = this.state.clans.find(c => c.clanId === clanId);if(!clan) return;switch (action){case 'view':
 this.showClanDetails(clan);break;case 'manage':
 this.showMemberManagement(clan);break;case 'delete':
 if(confirm(`Delete clan "${clan.name}"? This action cannot be undone.`)){await this.deleteClan(clanId);}break;}}showClanDetails(clan){this.setState({selectedClan: clan});const detailsContainer = this.container.querySelector('#clanDetails');const membersList = clan.members ? clan.members.map(member => 
 `<span class="inline-block bg-gray-600 px-2 py-1 rounded text-sm mr-2 mb-2">${member}</span>`
 ).join('') : 'No members listed';detailsContainer.innerHTML = `
 <div class="clan-details-content">
 <div class="flex items-start justify-between mb-6">
 <div>
 <h4 class="text-2xl font-bold text-purple-400 mb-2">${clan.name}</h4>
 <div class="text-sm text-gray-400">
 Led by ${clan.leader}• ${clan.memberCount || 0}members • ${this.getServerName(clan.serverId)}</div>
 </div>
 <span class="text-xs px-3 py-1 rounded ${clan.isActive ? 'bg-green-800 text-green-200' : 'bg-red-800 text-red-200'}">
 ${clan.isActive ? 'Active' : 'Inactive'}</span>
 </div>
 ${clan.description ? `
 <div class="mb-6">
 <h5 class="font-semibold mb-2">Description</h5>
 <p class="text-gray-300 bg-gray-700 p-3 rounded">${clan.description}</p>
 </div>
 ` : ''}<div class="mb-6">
 <h5 class="font-semibold mb-2">Members (${clan.memberCount || 0})</h5>
 <div class="members-list bg-gray-700 p-3 rounded min-h-[60px]">
 ${membersList}</div>
 </div>
 <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
 <div class="bg-gray-700 p-3 rounded">
 <div class="text-lg font-bold">${clan.level || 1}</div>
 <div class="text-xs text-gray-400">Level</div>
 </div>
 <div class="bg-gray-700 p-3 rounded">
 <div class="text-lg font-bold">${clan.experience || 0}</div>
 <div class="text-xs text-gray-400">Experience</div>
 </div>
 <div class="bg-gray-700 p-3 rounded">
 <div class="text-lg font-bold">${clan.bank || 0}</div>
 <div class="text-xs text-gray-400">Bank</div>
 </div>
 <div class="bg-gray-700 p-3 rounded">
 <div class="text-lg font-bold">${new Date(clan.createdDate).toLocaleDateString()}</div>
 <div class="text-xs text-gray-400">Created</div>
 </div>
 </div>
 </div>
 `;}showMemberManagement(clan){if(!this.options.enableMemberManagement) return;const modal = this.container.querySelector('#memberManagementModal');const content = this.container.querySelector('#memberModalContent');content.innerHTML = `
 <div class="member-management">
 <h4 class="font-semibold mb-4">👥 ${clan.name}Members</h4>
 <!-- Add Member -->
 <div class="mb-4 p-3 bg-gray-700 rounded">
 <h5 class="text-sm font-semibold mb-2">Add Member</h5>
 <div class="flex gap-2">
 <input type="text" 
 id="addMemberInput" 
 placeholder="User ID" 
 class="flex-1 bg-gray-600 p-2 rounded text-sm">
 <button id="addMemberBtn" 
 class="bg-green-600 hover:bg-green-700 px-3 py-2 rounded text-sm">
 Add
 </button>
 </div>
 </div>
 <!-- Current Members -->
 <div class="members-list">
 <h5 class="text-sm font-semibold mb-2">Current Members</h5>
 <div class="space-y-2 max-h-40 overflow-y-auto">
 ${(clan.members || []).map(member => `
 <div class="flex items-center justify-between p-2 bg-gray-600 rounded">
 <span class="text-sm">${member}${member === clan.leader ? '(Leader)' : ''}</span>
 ${member !== clan.leader ? `
 <button class="remove-member-btn bg-red-600 hover:bg-red-700 px-2 py-1 rounded text-xs"
 data-member="${member}" data-clan-id="${clan.clanId}">
 Remove
 </button>
 ` : ''}</div>
 `).join('')}</div>
 </div>
 </div>
 `;const addMemberBtn = content.querySelector('#addMemberBtn');const removeButtons = content.querySelectorAll('.remove-member-btn');this.addEventListener(addMemberBtn,'click',() =>{const input = content.querySelector('#addMemberInput');this.addClanMember(clan.clanId,input.value.trim());});removeButtons.forEach(button =>{this.addEventListener(button,'click',(e) =>{const member = e.target.dataset.member;this.removeClanMember(clan.clanId,member);});});modal.classList.remove('hidden');}async addClanMember(clanId,userId){if(!userId){this.showNotification('Please enter a user ID','warning');return;}try{const result = await this.api.clans.join(clanId,{userId});if(result.success){this.showNotification('Member added successfully','success');this.closeMemberModal();await this.loadData();}else{this.showNotification(result.error || 'Failed to add member','error');}}catch (error){this.handleError(error);}}async removeClanMember(clanId,memberId){if(!confirm(`Remove ${memberId}from clan?`)){return;}try{const result = await this.api.clans.kick(clanId,{leaderId: this.state.selectedClan?.leader,targetId: memberId});if(result.success){this.showNotification('Member removed successfully','success');this.closeMemberModal();await this.loadData();}else{this.showNotification(result.error || 'Failed to remove member','error');}}catch (error){this.handleError(error);}}closeMemberModal(){const modal = this.container.querySelector('#memberManagementModal');if(modal){modal.classList.add('hidden');}}async deleteClan(clanId){try{const result = await this.api.clans.delete(clanId,{leaderId: this.state.selectedClan?.leader});if(result.success){this.showNotification('Clan deleted successfully','success');this.eventBus.emit('clan:deleted',{clanId});await this.loadData();}else{this.showNotification(result.error || 'Failed to delete clan','error');}}catch (error){this.handleError(error);}}getFilteredAndSortedClans(clans){let filtered = [...clans];if(this.state.filterText){const filter = this.state.filterText.toLowerCase();filtered = filtered.filter(clan => 
 clan.name.toLowerCase().includes(filter) ||
 clan.leader.toLowerCase().includes(filter) ||
 clan.description?.toLowerCase().includes(filter)
 );}if(this.state.serverFilter){filtered = filtered.filter(clan => clan.serverId === this.state.serverFilter);}filtered.sort((a,b) =>{let aVal,bVal;switch (this.state.sortBy){case 'memberCount':
 aVal = a.memberCount || 0;bVal = b.memberCount || 0;break;case 'createdDate':
 aVal = new Date(a.createdDate);bVal = new Date(b.createdDate);break;default:
 aVal = a.name.toLowerCase();bVal = b.name.toLowerCase();}const result = aVal < bVal ? -1 : aVal > bVal ? 1 : 0;return this.state.sortDirection === 'desc' ? -result : result;});return filtered;}filterAndSortClans(){this.renderClansList();}setSorting(sortBy){const newDirection = this.state.sortBy === sortBy && this.state.sortDirection === 'asc' ? 'desc' : 'asc';this.setState({sortBy,sortDirection: newDirection});this.filterAndSortClans();this.updateSortButtons();}updateSortButtons(){const buttons = this.container.querySelectorAll('[id^="sortBy"]');buttons.forEach(button =>{const sortType = button.id.replace('sortBy','').toLowerCase();const isActive = (sortType === 'name' && this.state.sortBy === 'name') ||
 (sortType === 'members' && this.state.sortBy === 'memberCount') ||
 (sortType === 'created' && this.state.sortBy === 'createdDate');button.className = `px-3 py-1 rounded ${isActive ? 'bg-purple-600' : 'bg-gray-600'}`;});}clearCreateForm(){this.setState({newClanName: '',newClanLeader: '',newClanServerId: '',newClanDescription: ''});const form = this.container.querySelector('#createClanSection');if(form){form.querySelectorAll('input,select,textarea').forEach(input =>{input.value = '';});}}updateCharacterCount(input,maxLength){const sibling = input.nextElementSibling;if(sibling && sibling.classList.contains('text-xs')){sibling.textContent = `${input.value.length}/${maxLength}characters`;}}updateServerOptions(){const selects = this.container.querySelectorAll('#clanServerSelect,#serverFilter');selects.forEach(select =>{const currentValue = select.value;const isServerFilter = select.id === 'serverFilter';select.innerHTML = isServerFilter ? 
 '<option value="">All Servers</option>' : 
 '<option value="">Choose a server...</option>';select.innerHTML += this.renderServerOptions();select.value = currentValue;});}getServerName(serverId){const server = this.servers.find(s => s.serverId === serverId);return server ? server.serverName : `Server ${serverId}`;}async loadStats(){try{const stats = await this.api.clans.getStats();this.setState({stats});this.renderStats(stats);}catch (error){console.error('Failed to load clan stats:',error);}}renderStats(stats){const statsContainer = this.container.querySelector('#clanStats');if(statsContainer){statsContainer.innerHTML = `
 <div class="text-center">
 <div class="text-lg font-bold">${stats.total_clans || 0}</div>
 <div class="text-sm text-gray-400">Total Clans</div>
 </div>
 <div class="text-center">
 <div class="text-lg font-bold">${stats.total_members || 0}</div>
 <div class="text-sm text-gray-400">Total Members</div>
 </div>
 <div class="text-center">
 <div class="text-lg font-bold">${stats.average_clan_size || 0}</div>
 <div class="text-sm text-gray-400">Avg Size</div>
 </div>
 <div class="text-center">
 <div class="text-lg font-bold">${stats.largest_clan?.name || 'N/A'}</div>
 <div class="text-sm text-gray-400">Largest Clan</div>
 </div>
 `;}}showNotification(message,type = 'info'){this.eventBus.emit('notification:show',{message,type});}onDestroy(){this.eventBus.off('servers:updated');this.eventBus.off('clan:member-updated');}}if(typeof module !== 'undefined' && module.exports){module.exports = ClansComponent;}else{window.ClansComponent = ClansComponent;}