/**
 * Console Output Widget
 * Displays formatted console messages with filtering and auto-scroll
 */
class ConsoleOutput extends BaseComponent {
    constructor(containerId, options = {}) {
        super(containerId, options);
        this.eventBus = options.eventBus || window.App.eventBus;
        this.messages = [];
        this.filteredMessages = [];
        this.virtualScroll = null;
        this.observer = null;
    }
    
    get defaultOptions() {
        return {
            ...super.defaultOptions,
            maxMessages: 1000,
            autoScroll: true,
            showTimestamps: true,
            showIcons: true,
            enableFiltering: true,
            enableSearch: true,
            virtualScrolling: true,
            messageHeight: 24,
            bufferSize: 10,
            animateNew: true,
            highlightPatterns: []
        };
    }
    
    getInitialState() {
        return {
            ...super.getInitialState(),
            messages: [],
            filteredMessages: [],
            filters: {
                types: new Set(['all']),
                servers: new Set(['all']),
                searchText: ''
            },
            autoScroll: this.options.autoScroll,
            isScrolledToBottom: true,
            newMessageCount: 0
        };
    }
    
    render() {
        this.container.innerHTML = `
            <div class="console-output">
                <!-- Controls -->
                <div class="console-controls">
                    <div class="console-controls__left">
                        ${this.options.enableFiltering ? `
                            <div class="filter-group">
                                <label class="filter-label">Type:</label>
                                <select id="message-type-filter" class="filter-select">
                                    <option value="all">All Messages</option>
                                    <option value="chat">💬 Chat</option>
                                    <option value="auth">🔐 Auth/VIP</option>
                                    <option value="save">💾 Server Saves</option>
                                    <option value="kill">⚔️ Kill Feed</option>
                                    <option value="error">❌ Errors</option>
                                    <option value="warning">⚠️ Warnings</option>
                                    <option value="command">🔧 Commands</option>
                                    <option value="player">👥 Player Events</option>
                                    <option value="system">🖥️ System</option>
                                    <option value="event">🎯 Events</option>
                                </select>
                            </div>
                            
                            <div class="filter-group">
                                <label class="filter-label">Server:</label>
                                <select id="server-filter" class="filter-select">
                                    <option value="all">All Servers</option>
                                </select>
                            </div>
                        ` : ''}
                        
                        ${this.options.enableSearch ? `
                            <div class="filter-group">
                                <div class="search-input-group">
                                    <input type="text" id="message-search" 
                                           placeholder="Search messages..."
                                           class="search-input">
                                    <button id="clear-search" class="search-clear" title="Clear search">
                                        <i class="icon-x"></i>
                                    </button>
                                </div>
                            </div>
                        ` : ''}
                    </div>
                    
                    <div class="console-controls__right">
                        <div class="control-group">
                            <label class="checkbox-label">
                                <input type="checkbox" id="auto-scroll" 
                                       ${this.state.autoScroll ? 'checked' : ''}>
                                <span class="checkbox-text">Auto-scroll</span>
                            </label>
                        </div>
                        
                        <div class="control-group">
                            <button id="scroll-to-bottom" class="btn-control" title="Scroll to bottom">
                                <i class="icon-arrow-down"></i>
                            </button>
                            
                            <button id="clear-console" class="btn-control" title="Clear console">
                                <i class="icon-trash"></i>
                            </button>
                            
                            <button id="export-log" class="btn-control" title="Export log">
                                <i class="icon-download"></i>
                            </button>
                        </div>
                    </div>
                </div>
                
                <!-- Message Counter -->
                <div class="message-counter">
                    <span id="message-count">0 messages</span>
                    <span id="filtered-info" class="filtered-info hidden">
                        (filtered from <span id="total-count">0</span>)
                    </span>
                    <div id="new-message-indicator" class="new-message-indicator hidden">
                        <span id="new-count">0</span> new messages
                        <button id="view-new" class="view-new-btn">View</button>
                    </div>
                </div>
                
                <!-- Console Messages -->
                <div class="console-messages" id="console-messages">
                    <div class="console-messages__container" id="messages-container">
                        ${this.options.virtualScrolling ? `
                            <div class="virtual-scroll-content" id="virtual-content">
                                <!-- Virtual scroll content -->
                            </div>
                        ` : `
                            <div class="messages-list" id="messages-list">
                                <!-- Messages will be rendered here -->
                            </div>
                        `}
                    </div>
                    
                    <!-- Empty State -->
                    <div class="console-empty ${this.state.messages.length > 0 ? 'hidden' : ''}" id="console-empty">
                        <div class="empty-icon">
                            <i class="icon-terminal"></i>
                        </div>
                        <div class="empty-title">No console messages</div>
                        <div class="empty-subtitle">
                            Console output and live messages will appear here
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        this.initializeVirtualScroll();
        this.setupScrollObserver();
    }
    
    bindEvents() {
        // Filter controls
        if (this.options.enableFiltering) {
            const typeFilter = this.container.querySelector('#message-type-filter');
            const serverFilter = this.container.querySelector('#server-filter');
            
            this.addEventListener(typeFilter, 'change', (e) => {
                this.updateFilter('types', new Set([e.target.value]));
            });
            
            this.addEventListener(serverFilter, 'change', (e) => {
                this.updateFilter('servers', new Set([e.target.value]));
            });
        }
        
        // Search functionality
        if (this.options.enableSearch) {
            const searchInput = this.container.querySelector('#message-search');
            const clearSearch = this.container.querySelector('#clear-search');
            
            this.addEventListener(searchInput, 'input', 
                this.debounce((e) => this.updateFilter('searchText', e.target.value), 300)
            );
            
            this.addEventListener(clearSearch, 'click', () => {
                searchInput.value = '';
                this.updateFilter('searchText', '');
            });
        }
        
        // Control buttons
        const autoScrollCheck = this.container.querySelector('#auto-scroll');
        const scrollToBottomBtn = this.container.querySelector('#scroll-to-bottom');
        const clearConsoleBtn = this.container.querySelector('#clear-console');
        const exportLogBtn = this.container.querySelector('#export-log');
        const viewNewBtn = this.container.querySelector('#view-new');
        
        this.addEventListener(autoScrollCheck, 'change', (e) => {
            this.setAutoScroll(e.target.checked);
        });
        
        this.addEventListener(scrollToBottomBtn, 'click', () => {
            this.scrollToBottom();
        });
        
        this.addEventListener(clearConsoleBtn, 'click', () => {
            this.clearConsole();
        });
        
        this.addEventListener(exportLogBtn, 'click', () => {
            this.exportLog();
        });
        
        this.addEventListener(viewNewBtn, 'click', () => {
            this.viewNewMessages();
        });
        
        // Scroll event for auto-scroll detection
        const messagesContainer = this.container.querySelector('#console-messages');
        this.addEventListener(messagesContainer, 'scroll', 
            this.throttle(() => this.handleScroll(), 100)
        );
        
        // Message click events (for message details)
        this.addEventListener(messagesContainer, 'click', (e) => {
            this.handleMessageClick(e);
        });
        
        // Global events
        this.eventBus.on('console:message', (data) => this.addMessage(data));
        this.eventBus.on('console:clear', () => this.clearConsole());
        this.eventBus.on('servers:updated', (data) => this.updateServerFilter(data.servers));
    }
    
    initializeVirtualScroll() {
        if (!this.options.virtualScrolling) return;
        
        const container = this.container.querySelector('#console-messages');
        const content = this.container.querySelector('#virtual-content');
        
        this.virtualScroll = {
            container,
            content,
            itemHeight: this.options.messageHeight,
            visibleStart: 0,
            visibleEnd: 0,
            scrollTop: 0
        };
    }
    
    setupScrollObserver() {
        const messagesContainer = this.container.querySelector('#console-messages');
        
        // Intersection Observer to detect when scrolled to bottom
        this.observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                this.setState({ isScrolledToBottom: entry.isIntersecting });
                
                if (entry.isIntersecting && this.state.newMessageCount > 0) {
                    this.resetNewMessageCount();
                }
            });
        }, { 
            root: messagesContainer,
            threshold: 1.0 
        });
        
        // Create bottom sentinel
        const sentinel = document.createElement('div');
        sentinel.className = 'scroll-sentinel';
        sentinel.style.height = '1px';
        messagesContainer.appendChild(sentinel);
        
        this.observer.observe(sentinel);
    }
    
    addMessage(message) {
        const formattedMessage = this.formatMessage(message);
        
        // Add to messages array
        this.messages.push(formattedMessage);
        
        // Maintain max message limit
        if (this.messages.length > this.options.maxMessages) {
            this.messages = this.messages.slice(-this.options.maxMessages);
        }
        
        this.setState({ messages: this.messages });
        
        // Apply filters and render
        this.applyFilters();
        
        // Handle new message indicators
        if (!this.state.isScrolledToBottom) {
            this.incrementNewMessageCount();
        }
        
        // Auto-scroll if enabled and scrolled to bottom
        if (this.state.autoScroll && this.state.isScrolledToBottom) {
            this.scrollToBottom();
        }
        
        // Animate new message if enabled
        if (this.options.animateNew) {
            this.animateNewMessage();
        }
        
        this.updateMessageCounter();
    }
    
    formatMessage(message) {
        const timestamp = new Date(message.timestamp || Date.now());
        const messageType = this.classifyMessage(message.message);
        
        return {
            id: message.id || this.generateMessageId(),
            timestamp: timestamp.toISOString(),
            formattedTime: timestamp.toLocaleTimeString(),
            message: message.message || '',
            type: message.type || messageType,
            serverId: message.serverId || message.server_id,
            source: message.source || 'unknown',
            level: this.getMessageLevel(message),
            raw: message
        };
    }
    
    classifyMessage(messageText) {
        if (!messageText) return 'system';
        
        const text = messageText.toLowerCase();
        
        // Chat messages
        if (text.includes('[chat]') || text.includes('global.say')) return 'chat';
        
        // Authentication/VIP
        if (text.includes('vip') || text.includes('admin') || text.includes('auth')) return 'auth';
        
        // Server saves
        if (text.includes('save') || text.includes('saving')) return 'save';
        
        // Kill feed
        if (text.includes('killed') || text.includes('died') || text.includes('death')) return 'kill';
        
        // Errors
        if (text.includes('error') || text.includes('exception') || text.includes('failed')) return 'error';
        
        // Warnings
        if (text.includes('warning') || text.includes('warn')) return 'warning';
        
        // Commands
        if (text.includes('executing') || text.includes('command')) return 'command';
        
        // Player events
        if (text.includes('connected') || text.includes('disconnected') || text.includes('joined')) return 'player';
        
        // Events
        if (text.includes('event') || text.includes('koth')) return 'event';
        
        return 'system';
    }
    
    getMessageLevel(message) {
        const type = message.type || this.classifyMessage(message.message);
        
        switch (type) {
            case 'error': return 'error';
            case 'warning': return 'warning';
            case 'auth': case 'event': return 'info';
            case 'chat': case 'player': return 'success';
            default: return 'default';
        }
    }
    
    renderMessages() {
        if (this.options.virtualScrolling) {
            this.renderVirtualMessages();
        } else {
            this.renderAllMessages();
        }
    }
    
    renderAllMessages() {
        const container = this.container.querySelector('#messages-list');
        if (!container) return;
        
        container.innerHTML = this.state.filteredMessages
            .map(message => this.renderMessageElement(message))
            .join('');
        
        this.updateEmptyState();
    }
    
    renderVirtualMessages() {
        const { container, content } = this.virtualScroll;
        const messages = this.state.filteredMessages;
        
        const containerHeight = container.clientHeight;
        const itemHeight = this.options.messageHeight;
        const totalHeight = messages.length * itemHeight;
        
        const scrollTop = container.scrollTop;
        const visibleStart = Math.floor(scrollTop / itemHeight);
        const visibleCount = Math.ceil(containerHeight / itemHeight) + this.options.bufferSize;
        const visibleEnd = Math.min(visibleStart + visibleCount, messages.length);
        
        // Update virtual scroll state
        this.virtualScroll.visibleStart = visibleStart;
        this.virtualScroll.visibleEnd = visibleEnd;
        this.virtualScroll.scrollTop = scrollTop;
        
        // Set total height
        content.style.height = `${totalHeight}px`;
        
        // Render visible messages
        const visibleMessages = messages.slice(visibleStart, visibleEnd);
        const offset = visibleStart * itemHeight;
        
        content.innerHTML = `
            <div style="transform: translateY(${offset}px)">
                ${visibleMessages.map(message => this.renderMessageElement(message)).join('')}
            </div>
        `;
        
        this.updateEmptyState();
    }
    
    renderMessageElement(message) {
        const typeIcon = this.getTypeIcon(message.type);
        const levelClass = `message-level--${message.level}`;
        const sourceClass = `message-source--${message.source}`;
        
        return `
            <div class="console-message ${levelClass} ${sourceClass}" 
                 data-message-id="${message.id}"
                 data-type="${message.type}"
                 data-server="${message.serverId || 'unknown'}">
                
                ${this.options.showTimestamps ? `
                    <span class="message-time">[${message.formattedTime}]</span>
                ` : ''}
                
                ${this.options.showIcons ? `
                    <span class="message-icon" title="${message.type}">${typeIcon}</span>
                ` : ''}
                
                ${message.serverId ? `
                    <span class="message-server" title="Server ID">[${message.serverId}]</span>
                ` : ''}
                
                <span class="message-content">
                    ${this.highlightMessage(this.escapeHtml(message.message))}
                </span>
                
                ${message.source !== 'unknown' ? `
                    <span class="message-source-indicator" title="Source: ${message.source}">
                        <i class="icon-${this.getSourceIcon(message.source)}"></i>
                    </span>
                ` : ''}
            </div>
        `;
    }
    
    getTypeIcon(type) {
        const icons = {
            chat: '💬',
            auth: '🔐',
            save: '💾',
            kill: '⚔️',
            error: '❌',
            warning: '⚠️',
            command: '🔧',
            player: '👥',
            system: '🖥️',
            event: '🎯'
        };
        return icons[type] || '📋';
    }
    
    getSourceIcon(source) {
        const sourceIcons = {
            websocket_live: 'wifi',
            api: 'server',
            demo: 'play',
            demo_simulation: 'cpu',
            event_system: 'calendar',
            auto_connection: 'plug'
        };
        return sourceIcons[source] || 'info';
    }
    
    highlightMessage(message) {
        let highlighted = message;
        
        // Apply search highlighting
        if (this.state.filters.searchText) {
            const searchText = this.escapeRegex(this.state.filters.searchText);
            const regex = new RegExp(`(${searchText})`, 'gi');
            highlighted = highlighted.replace(regex, '<mark class="search-highlight">$1</mark>');
        }
        
        // Apply custom highlight patterns
        this.options.highlightPatterns.forEach(pattern => {
            const regex = new RegExp(pattern.regex, pattern.flags || 'gi');
            highlighted = highlighted.replace(regex, `<span class="highlight highlight--${pattern.class}">$1</span>`);
        });
        
        return highlighted;
    }
    
    updateFilter(filterType, value) {
        const newFilters = { ...this.state.filters };
        newFilters[filterType] = value;
        
        this.setState({ filters: newFilters });
        this.applyFilters();
    }
    
    applyFilters() {
        const { types, servers, searchText } = this.state.filters;
        
        let filtered = this.messages;
        
        // Filter by type
        if (!types.has('all')) {
            filtered = filtered.filter(msg => types.has(msg.type));
        }
        
        // Filter by server
        if (!servers.has('all')) {
            filtered = filtered.filter(msg => 
                servers.has(msg.serverId) || (!msg.serverId && servers.has('unknown'))
            );
        }
        
        // Filter by search text
        if (searchText) {
            const searchLower = searchText.toLowerCase();
            filtered = filtered.filter(msg => 
                msg.message.toLowerCase().includes(searchLower)
            );
        }
        
        this.setState({ filteredMessages: filtered });
        this.renderMessages();
        this.updateMessageCounter();
    }
    
    updateServerFilter(servers) {
        const serverFilter = this.container.querySelector('#server-filter');
        if (!serverFilter) return;
        
        const currentValue = serverFilter.value;
        
        // Rebuild options
        serverFilter.innerHTML = '<option value="all">All Servers</option>';
        
        const activeServers = servers.filter(server => server.isActive);
        activeServers.forEach(server => {
            const option = document.createElement('option');
            option.value = server.serverId;
            option.textContent = `${server.serverName} (${server.serverId})`;
            serverFilter.appendChild(option);
        });
        
        // Restore selection
        if (currentValue && activeServers.some(s => s.serverId === currentValue)) {
            serverFilter.value = currentValue;
        }
    }
    
    updateMessageCounter() {
        const messageCount = this.container.querySelector('#message-count');
        const filteredInfo = this.container.querySelector('#filtered-info');
        const totalCount = this.container.querySelector('#total-count');
        
        const filtered = this.state.filteredMessages.length;
        const total = this.messages.length;
        
        messageCount.textContent = `${filtered} message${filtered !== 1 ? 's' : ''}`;
        
        if (filtered !== total) {
            filteredInfo.classList.remove('hidden');
            totalCount.textContent = total;
        } else {
            filteredInfo.classList.add('hidden');
        }
    }
    
    updateEmptyState() {
        const emptyState = this.container.querySelector('#console-empty');
        const hasMessages = this.state.filteredMessages.length > 0;
        
        emptyState.classList.toggle('hidden', hasMessages);
    }
    
    incrementNewMessageCount() {
        const newCount = this.state.newMessageCount + 1;
        this.setState({ newMessageCount: newCount });
        
        const indicator = this.container.querySelector('#new-message-indicator');
        const countSpan = this.container.querySelector('#new-count');
        
        indicator.classList.remove('hidden');
        countSpan.textContent = newCount;
    }
    
    resetNewMessageCount() {
        this.setState({ newMessageCount: 0 });
        
        const indicator = this.container.querySelector('#new-message-indicator');
        indicator.classList.add('hidden');
    }
    
    viewNewMessages() {
        this.scrollToBottom();
        this.resetNewMessageCount();
    }
    
    setAutoScroll(enabled) {
        this.setState({ autoScroll: enabled });
        
        if (enabled && this.state.isScrolledToBottom) {
            this.scrollToBottom();
        }
    }
    
    scrollToBottom() {
        const container = this.container.querySelector('#console-messages');
        container.scrollTop = container.scrollHeight;
        
        this.setState({ isScrolledToBottom: true });
        this.resetNewMessageCount();
    }
    
    handleScroll() {
        const container = this.container.querySelector('#console-messages');
        const isAtBottom = container.scrollTop + container.clientHeight >= container.scrollHeight - 10;
        
        this.setState({ isScrolledToBottom: isAtBottom });
        
        if (this.options.virtualScrolling) {
            this.renderVirtualMessages();
        }
    }
    
    handleMessageClick(event) {
        const messageElement = event.target.closest('.console-message');
        if (!messageElement) return;
        
        const messageId = messageElement.dataset.messageId;
        const message = this.messages.find(m => m.id === messageId);
        
        if (message) {
            this.showMessageDetails(message);
        }
    }
    
    showMessageDetails(message) {
        this.eventBus.emit('modal:show', {
            title: 'Message Details',
            content: `
                <div class="message-details">
                    <div class="detail-row">
                        <span class="detail-label">Time:</span>
                        <span class="detail-value">${new Date(message.timestamp).toLocaleString()}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Type:</span>
                        <span class="detail-value">${message.type}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Server:</span>
                        <span class="detail-value">${message.serverId || 'Unknown'}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Source:</span>
                        <span class="detail-value">${message.source}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Message:</span>
                        <div class="detail-message">${this.escapeHtml(message.message)}</div>
                    </div>
                </div>
            `,
            actions: [
                {
                    label: 'Copy Message',
                    action: () => this.copyToClipboard(message.message)
                },
                {
                    label: 'Copy Raw Data',
                    action: () => this.copyToClipboard(JSON.stringify(message.raw, null, 2))
                }
            ]
        });
    }
    
    clearConsole() {
        this.messages = [];
        this.setState({ 
            messages: [], 
            filteredMessages: [],
            newMessageCount: 0
        });
        
        this.renderMessages();
        this.updateMessageCounter();
        this.resetNewMessageCount();
        
        this.eventBus.emit('notification:show', {
            message: 'Console cleared',
            type: 'info'
        });
    }
    
    exportLog() {
        const messages = this.state.filteredMessages;
        
        if (messages.length === 0) {
            this.eventBus.emit('notification:show', {
                message: 'No messages to export',
                type: 'warning'
            });
            return;
        }
        
        const logContent = messages.map(msg => 
            `[${msg.formattedTime}] [${msg.type}] ${msg.serverId ? `[${msg.serverId}] ` : ''}${msg.message}`
        ).join('\n');
        
        const blob = new Blob([logContent], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `console-log-${new Date().toISOString().split('T')[0]}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        
        URL.revokeObjectURL(url);
        
        this.eventBus.emit('notification:show', {
            message: 'Console log exported',
            type: 'success'
        });
    }
    
    animateNewMessage() {
        // Add animation class to the last message
        setTimeout(() => {
            const messages = this.container.querySelectorAll('.console-message');
            const lastMessage = messages[messages.length - 1];
            
            if (lastMessage) {
                lastMessage.classList.add('message-new');
                setTimeout(() => {
                    lastMessage.classList.remove('message-new');
                }, 1000);
            }
        }, 10);
    }
    
    generateMessageId() {
        return `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    escapeRegex(string) {
        return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }
    
    copyToClipboard(text) {
        navigator.clipboard.writeText(text).then(() => {
            this.eventBus.emit('notification:show', {
                message: 'Copied to clipboard',
                type: 'success'
            });
        }).catch(() => {
            // Fallback for older browsers
            const textarea = document.createElement('textarea');
            textarea.value = text;
            document.body.appendChild(textarea);
            textarea.select();
            document.execCommand('copy');
            document.body.removeChild(textarea);
            
            this.eventBus.emit('notification:show', {
                message: 'Copied to clipboard',
                type: 'success'
            });
        });
    }
    
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
    
    throttle(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }
    
    onDestroy() {
        // Clean up virtual scroll
        this.virtualScroll = null;
        
        // Clean up observer
        if (this.observer) {
            this.observer.disconnect();
        }
        
        // Unsubscribe from events
        this.eventBus.off('console:message');
        this.eventBus.off('console:clear');
        this.eventBus.off('servers:updated');
    }
}