/**
 * GUST Bot Enhanced - Notification Service
 * =======================================
 * Manages user notifications, alerts, toasts, and status messages
 */

class NotificationService {
    constructor(options = {}) {
        this.options = { ...this.defaultOptions, ...options };
        this.notifications = new Map();
        this.queue = [];
        this.container = null;
        this.eventBus = options.eventBus || window.App?.eventBus || window.EventBus;
        this.storage = options.storage || window.App?.services?.storage;
        this.notificationId = 0;
        
        this.init();
    }
    
    get defaultOptions() {
        return {
            containerId: 'notification-container',
            position: 'top-right', // top-right, top-left, bottom-right, bottom-left, top-center, bottom-center
            maxNotifications: 5,
            defaultDuration: 5000,
            animationDuration: 300,
            showProgress: true,
            allowDuplicates: false,
            persistentTypes: ['error'],
            enableSound: false,
            enableBrowserNotifications: false,
            stackNewest: 'top', // top, bottom
            autoClose: true,
            pauseOnHover: true,
            showClose: true,
            theme: 'dark' // dark, light, auto
        };
    }
    
    init() {
        this.createContainer();
        this.bindEvents();
        this.requestNotificationPermission();
        this.loadStoredNotifications();
    }
    
    createContainer() {
        // Remove existing container
        const existing = document.getElementById(this.options.containerId);
        if (existing) {
            existing.remove();
        }
        
        // Create new container
        this.container = document.createElement('div');
        this.container.id = this.options.containerId;
        this.container.className = `notification-container notification-container--${this.options.position} notification-container--${this.options.theme}`;
        
        // Add CSS if not already present
        this.injectCSS();
        
        document.body.appendChild(this.container);
    }
    
    injectCSS() {
        if (document.getElementById('notification-service-css')) return;
        
        const css = `
            .notification-container {
                position: fixed;
                z-index: 10000;
                pointer-events: none;
                max-width: 400px;
                width: 100%;
            }
            
            .notification-container--top-right {
                top: 20px;
                right: 20px;
            }
            
            .notification-container--top-left {
                top: 20px;
                left: 20px;
            }
            
            .notification-container--bottom-right {
                bottom: 20px;
                right: 20px;
            }
            
            .notification-container--bottom-left {
                bottom: 20px;
                left: 20px;
            }
            
            .notification-container--top-center {
                top: 20px;
                left: 50%;
                transform: translateX(-50%);
            }
            
            .notification-container--bottom-center {
                bottom: 20px;
                left: 50%;
                transform: translateX(-50%);
            }
            
            .notification {
                pointer-events: auto;
                margin-bottom: 10px;
                border-radius: 8px;
                padding: 16px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
                transform: translateX(100%);
                transition: all 0.3s ease;
                position: relative;
                overflow: hidden;
                backdrop-filter: blur(10px);
            }
            
            .notification.notification--visible {
                transform: translateX(0);
            }
            
            .notification.notification--hiding {
                transform: translateX(100%);
                opacity: 0;
            }
            
            /* Dark theme */
            .notification-container--dark .notification {
                background: rgba(31, 41, 55, 0.95);
                border: 1px solid rgba(75, 85, 99, 0.5);
                color: #f9fafb;
            }
            
            /* Light theme */
            .notification-container--light .notification {
                background: rgba(255, 255, 255, 0.95);
                border: 1px solid rgba(229, 231, 235, 0.5);
                color: #111827;
            }
            
            .notification--success {
                border-left: 4px solid #10b981;
            }
            
            .notification--error {
                border-left: 4px solid #ef4444;
            }
            
            .notification--warning {
                border-left: 4px solid #f59e0b;
            }
            
            .notification--info {
                border-left: 4px solid #3b82f6;
            }
            
            .notification__header {
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin-bottom: 8px;
            }
            
            .notification__title {
                font-weight: 600;
                display: flex;
                align-items: center;
                gap: 8px;
            }
            
            .notification__icon {
                font-size: 18px;
            }
            
            .notification__close {
                background: none;
                border: none;
                cursor: pointer;
                padding: 4px;
                border-radius: 4px;
                opacity: 0.7;
                transition: opacity 0.2s ease;
            }
            
            .notification__close:hover {
                opacity: 1;
            }
            
            .notification-container--dark .notification__close {
                color: #f9fafb;
            }
            
            .notification-container--light .notification__close {
                color: #111827;
            }
            
            .notification__message {
                line-height: 1.5;
                margin-bottom: 8px;
            }
            
            .notification__actions {
                display: flex;
                gap: 8px;
                margin-top: 12px;
            }
            
            .notification__action {
                padding: 6px 12px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 12px;
                font-weight: 500;
                transition: all 0.2s ease;
            }
            
            .notification__action--primary {
                background: #3b82f6;
                color: white;
            }
            
            .notification__action--secondary {
                background: transparent;
                color: #6b7280;
                border: 1px solid #6b7280;
            }
            
            .notification__progress {
                position: absolute;
                bottom: 0;
                left: 0;
                height: 3px;
                background: linear-gradient(90deg, #3b82f6, #10b981);
                transition: width linear;
            }
            
            @keyframes notificationSlideIn {
                from {
                    transform: translateX(100%);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }
            
            @keyframes notificationSlideOut {
                from {
                    transform: translateX(0);
                    opacity: 1;
                }
                to {
                    transform: translateX(100%);
                    opacity: 0;
                }
            }
        `;
        
        const style = document.createElement('style');
        style.id = 'notification-service-css';
        style.textContent = css;
        document.head.appendChild(style);
    }
    
    bindEvents() {
        if (this.eventBus) {
            this.eventBus.on('notification:show', (data) => this.show(data));
            this.eventBus.on('notification:success', (data) => this.success(data.message, data.options));
            this.eventBus.on('notification:error', (data) => this.error(data.message, data.options));
            this.eventBus.on('notification:warning', (data) => this.warning(data.message, data.options));
            this.eventBus.on('notification:info', (data) => this.info(data.message, data.options));
            this.eventBus.on('notification:clear', () => this.clearAll());
        }
    }
    
    /**
     * Show notification
     * @param {Object} options - Notification options
     * @param {string} options.message - Notification message
     * @param {string} options.type - Notification type (success, error, warning, info)
     * @param {string} options.title - Notification title
     * @param {number} options.duration - Auto-close duration (0 for persistent)
     * @param {Array} options.actions - Action buttons
     * @param {Function} options.onClick - Click handler
     * @param {Object} options.data - Custom data
     */
    show(options = {}) {
        const notification = this.createNotification(options);
        
        // Check for duplicates
        if (!this.options.allowDuplicates && this.isDuplicate(notification)) {
            return null;
        }
        
        // Add to queue if too many notifications
        if (this.notifications.size >= this.options.maxNotifications) {
            this.queue.push(notification);
            return notification.id;
        }
        
        this.displayNotification(notification);
        return notification.id;
    }
    
    createNotification(options) {
        const id = ++this.notificationId;
        const type = options.type || 'info';
        
        const notification = {
            id,
            type,
            title: options.title || this.getDefaultTitle(type),
            message: options.message || '',
            duration: options.duration !== undefined ? options.duration : this.getDefaultDuration(type),
            actions: options.actions || [],
            onClick: options.onClick,
            data: options.data || {},
            createdAt: Date.now(),
            element: null,
            timer: null,
            progressTimer: null
        };
        
        return notification;
    }
    
    getDefaultTitle(type) {
        const titles = {
            success: '✅ Success',
            error: '❌ Error',
            warning: '⚠️ Warning',
            info: 'ℹ️ Information'
        };
        return titles[type] || titles.info;
    }
    
    getDefaultDuration(type) {
        if (this.options.persistentTypes.includes(type)) {
            return 0; // Persistent
        }
        return this.options.defaultDuration;
    }
    
    isDuplicate(notification) {
        for (const [id, existing] of this.notifications) {
            if (existing.message === notification.message && 
                existing.type === notification.type) {
                return true;
            }
        }
        return false;
    }
    
    displayNotification(notification) {
        // Create DOM element
        const element = this.createNotificationElement(notification);
        notification.element = element;
        
        // Add to container
        if (this.options.stackNewest === 'top') {
            this.container.insertBefore(element, this.container.firstChild);
        } else {
            this.container.appendChild(element);
        }
        
        // Store notification
        this.notifications.set(notification.id, notification);
        
        // Animate in
        requestAnimationFrame(() => {
            element.classList.add('notification--visible');
        });
        
        // Set auto-close timer
        if (notification.duration > 0) {
            this.setAutoCloseTimer(notification);
        }
        
        // Emit event
        this.emitEvent('notification:displayed', notification);
        
        // Show browser notification if enabled
        if (this.options.enableBrowserNotifications) {
            this.showBrowserNotification(notification);
        }
        
        // Play sound if enabled
        if (this.options.enableSound) {
            this.playNotificationSound(notification.type);
        }
    }
    
    createNotificationElement(notification) {
        const element = document.createElement('div');
        element.className = `notification notification--${notification.type}`;
        element.dataset.notificationId = notification.id;
        
        element.innerHTML = `
            <div class="notification__header">
                <div class="notification__title">
                    <span class="notification__icon">${this.getTypeIcon(notification.type)}</span>
                    ${notification.title}
                </div>
                ${this.options.showClose ? `
                    <button class="notification__close" title="Close">
                        ✕
                    </button>
                ` : ''}
            </div>
            
            <div class="notification__message">
                ${this.formatMessage(notification.message)}
            </div>
            
            ${notification.actions.length > 0 ? `
                <div class="notification__actions">
                    ${notification.actions.map((action, index) => `
                        <button class="notification__action notification__action--${action.type || 'secondary'}" 
                                data-action-index="${index}">
                            ${action.label}
                        </button>
                    `).join('')}
                </div>
            ` : ''}
            
            ${notification.duration > 0 && this.options.showProgress ? `
                <div class="notification__progress"></div>
            ` : ''}
        `;
        
        this.bindNotificationEvents(element, notification);
        
        return element;
    }
    
    bindNotificationEvents(element, notification) {
        // Close button
        const closeBtn = element.querySelector('.notification__close');
        if (closeBtn) {
            closeBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.close(notification.id);
            });
        }
        
        // Click handler
        if (notification.onClick) {
            element.addEventListener('click', (e) => {
                if (!e.target.closest('.notification__close, .notification__action')) {
                    notification.onClick(notification);
                }
            });
        }
        
        // Action buttons
        const actionButtons = element.querySelectorAll('.notification__action');
        actionButtons.forEach((button, index) => {
            button.addEventListener('click', (e) => {
                e.stopPropagation();
                const action = notification.actions[index];
                if (action.handler) {
                    action.handler(notification);
                }
                if (action.close !== false) {
                    this.close(notification.id);
                }
            });
        });
        
        // Pause on hover
        if (this.options.pauseOnHover && notification.duration > 0) {
            element.addEventListener('mouseenter', () => {
                this.pauseTimer(notification);
            });
            
            element.addEventListener('mouseleave', () => {
                this.resumeTimer(notification);
            });
        }
    }
    
    setAutoCloseTimer(notification) {
        if (notification.duration <= 0) return;
        
        const startTime = Date.now();
        
        // Progress bar animation
        if (this.options.showProgress) {
            const progressBar = notification.element.querySelector('.notification__progress');
            if (progressBar) {
                progressBar.style.width = '100%';
                progressBar.style.transitionDuration = `${notification.duration}ms`;
                
                requestAnimationFrame(() => {
                    progressBar.style.width = '0%';
                });
            }
        }
        
        // Auto-close timer
        notification.timer = setTimeout(() => {
            this.close(notification.id);
        }, notification.duration);
    }
    
    pauseTimer(notification) {
        if (notification.timer) {
            clearTimeout(notification.timer);
            notification.pausedAt = Date.now();
        }
        
        // Pause progress bar
        const progressBar = notification.element.querySelector('.notification__progress');
        if (progressBar) {
            const computedStyle = window.getComputedStyle(progressBar);
            const currentWidth = computedStyle.width;
            progressBar.style.width = currentWidth;
            progressBar.style.transitionDuration = '0ms';
        }
    }
    
    resumeTimer(notification) {
        if (notification.pausedAt && notification.duration > 0) {
            const elapsed = notification.pausedAt - notification.createdAt;
            const remaining = Math.max(0, notification.duration - elapsed);
            
            if (remaining > 0) {
                // Resume progress bar
                const progressBar = notification.element.querySelector('.notification__progress');
                if (progressBar) {
                    progressBar.style.transitionDuration = `${remaining}ms`;
                    progressBar.style.width = '0%';
                }
                
                // Resume timer
                notification.timer = setTimeout(() => {
                    this.close(notification.id);
                }, remaining);
            } else {
                this.close(notification.id);
            }
            
            notification.pausedAt = null;
        }
    }
    
    getTypeIcon(type) {
        const icons = {
            success: '✅',
            error: '❌',
            warning: '⚠️',
            info: 'ℹ️'
        };
        return icons[type] || icons.info;
    }
    
    formatMessage(message) {
        // Convert plain text to HTML, preserve line breaks
        return message.replace(/\n/g, '<br>');
    }
    
    /**
     * Close notification
     */
    close(id) {
        const notification = this.notifications.get(id);
        if (!notification) return;
        
        // Clear timers
        if (notification.timer) {
            clearTimeout(notification.timer);
        }
        
        // Animate out
        notification.element.classList.add('notification--hiding');
        
        setTimeout(() => {
            // Remove from DOM
            if (notification.element && notification.element.parentNode) {
                notification.element.parentNode.removeChild(notification.element);
            }
            
            // Remove from storage
            this.notifications.delete(id);
            
            // Process queue
            this.processQueue();
            
            // Emit event
            this.emitEvent('notification:closed', { id, notification });
            
        }, this.options.animationDuration);
    }
    
    /**
     * Process notification queue
     */
    processQueue() {
        if (this.queue.length > 0 && this.notifications.size < this.options.maxNotifications) {
            const notification = this.queue.shift();
            this.displayNotification(notification);
        }
    }
    
    /**
     * Clear all notifications
     */
    clearAll() {
        const ids = Array.from(this.notifications.keys());
        ids.forEach(id => this.close(id));
        this.queue = [];
    }
    
    /**
     * Convenience methods
     */
    success(message, options = {}) {
        return this.show({ ...options, message, type: 'success' });
    }
    
    error(message, options = {}) {
        return this.show({ ...options, message, type: 'error' });
    }
    
    warning(message, options = {}) {
        return this.show({ ...options, message, type: 'warning' });
    }
    
    info(message, options = {}) {
        return this.show({ ...options, message, type: 'info' });
    }
    
    /**
     * Show browser notification
     */
    async showBrowserNotification(notification) {
        if ('Notification' in window && Notification.permission === 'granted') {
            try {
                const browserNotification = new Notification(notification.title, {
                    body: notification.message,
                    icon: '/favicon.ico',
                    tag: `gust-${notification.id}`
                });
                
                browserNotification.onclick = () => {
                    window.focus();
                    if (notification.onClick) {
                        notification.onClick(notification);
                    }
                    browserNotification.close();
                };
                
                // Auto-close browser notification
                setTimeout(() => {
                    browserNotification.close();
                }, notification.duration || 5000);
                
            } catch (error) {
                console.warn('Browser notification failed:', error);
            }
        }
    }
    
    /**
     * Request notification permission
     */
    async requestNotificationPermission() {
        if (!this.options.enableBrowserNotifications) return;
        
        if ('Notification' in window && Notification.permission === 'default') {
            try {
                const permission = await Notification.requestPermission();
                return permission === 'granted';
            } catch (error) {
                console.warn('Notification permission request failed:', error);
                return false;
            }
        }
        
        return Notification.permission === 'granted';
    }
    
    /**
     * Play notification sound
     */
    playNotificationSound(type) {
        // Simple beep sound - you can replace with actual sound files
        if ('AudioContext' in window) {
            try {
                const audioContext = new AudioContext();
                const oscillator = audioContext.createOscillator();
                const gainNode = audioContext.createGain();
                
                oscillator.connect(gainNode);
                gainNode.connect(audioContext.destination);
                
                const frequency = type === 'error' ? 400 : type === 'warning' ? 600 : 800;
                oscillator.frequency.setValueAtTime(frequency, audioContext.currentTime);
                oscillator.type = 'sine';
                
                gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
                gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.3);
                
                oscillator.start(audioContext.currentTime);
                oscillator.stop(audioContext.currentTime + 0.3);
            } catch (error) {
                console.warn('Notification sound failed:', error);
            }
        }
    }
    
    /**
     * Load stored notifications (for persistent ones)
     */
    loadStoredNotifications() {
        if (!this.storage) return;
        
        try {
            const stored = this.storage.get('notifications', []);
            stored.forEach(notificationData => {
                if (Date.now() - notificationData.createdAt < 24 * 60 * 60 * 1000) { // 24 hours
                    this.show(notificationData);
                }
            });
        } catch (error) {
            console.warn('Failed to load stored notifications:', error);
        }
    }
    
    /**
     * Store persistent notifications
     */
    storeNotification(notification) {
        if (!this.storage || notification.duration > 0) return;
        
        try {
            const stored = this.storage.get('notifications', []);
            stored.push({
                type: notification.type,
                title: notification.title,
                message: notification.message,
                createdAt: notification.createdAt
            });
            
            // Keep only last 10 persistent notifications
            this.storage.set('notifications', stored.slice(-10));
        } catch (error) {
            console.warn('Failed to store notification:', error);
        }
    }
    
    /**
     * Get notification statistics
     */
    getStats() {
        return {
            active: this.notifications.size,
            queued: this.queue.length,
            total: this.notificationId,
            types: Array.from(this.notifications.values()).reduce((acc, n) => {
                acc[n.type] = (acc[n.type] || 0) + 1;
                return acc;
            }, {})
        };
    }
    
    /**
     * Emit event through event bus
     */
    emitEvent(event, data) {
        if (this.eventBus) {
            this.eventBus.emit(event, data);
        }
    }
    
    /**
     * Destroy service and cleanup
     */
    destroy() {
        this.clearAll();
        
        if (this.container && this.container.parentNode) {
            this.container.parentNode.removeChild(this.container);
        }
        
        const style = document.getElementById('notification-service-css');
        if (style) {
            style.remove();
        }
    }
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = NotificationService;
} else {
    window.NotificationService = NotificationService;
}