/**
 * Status Indicator Widget
 * Displays status badges and indicators with animations and tooltips
 */
class StatusIndicator extends BaseComponent {
    constructor(containerId, options = {}) {
        super(containerId, options);
        this.animationFrame = null;
        this.pulseInterval = null;
    }
    
    get defaultOptions() {
        return {
            ...super.defaultOptions,
            status: 'unknown',
            showText: true,
            showIcon: true,
            animate: true,
            size: 'medium', // small, medium, large
            variant: 'default', // default, pill, dot, badge
            clickable: false,
            tooltip: true,
            pulseOnChange: true,
            customStates: {}
        };
    }
    
    getInitialState() {
        return {
            ...super.getInitialState(),
            status: this.options.status,
            previousStatus: null,
            isAnimating: false,
            lastUpdate: Date.now()
        };
    }
    
    render() {
        const { status } = this.state;
        const { showText, showIcon, size, variant, clickable, tooltip } = this.options;
        
        const statusInfo = this.getStatusInfo(status);
        const sizeClass = `status-indicator--${size}`;
        const variantClass = `status-indicator--${variant}`;
        const clickableClass = clickable ? 'status-indicator--clickable' : '';
        const animatingClass = this.state.isAnimating ? 'status-indicator--animating' : '';
        
        this.container.innerHTML = `
            <div class="status-indicator ${sizeClass} ${variantClass} ${clickableClass} ${animatingClass}"
                 data-status="${status}"
                 ${tooltip ? `title="${statusInfo.tooltip}"` : ''}>
                
                ${showIcon ? `
                    <div class="status-indicator__icon-container">
                        <div class="status-indicator__icon ${statusInfo.colorClass}">
                            ${statusInfo.icon}
                        </div>
                        ${this.options.animate ? `
                            <div class="status-indicator__pulse ${statusInfo.colorClass}"></div>
                        ` : ''}
                    </div>
                ` : ''}
                
                ${showText ? `
                    <span class="status-indicator__text ${statusInfo.colorClass}">
                        ${statusInfo.text}
                    </span>
                ` : ''}
                
                ${this.shouldShowBadge() ? `
                    <div class="status-indicator__badge">
                        ${this.getBadgeContent()}
                    </div>
                ` : ''}
                
                ${this.options.animate ? `
                    <div class="status-indicator__loading ${this.state.isAnimating ? 'active' : ''}">
                        <div class="loading-spinner"></div>
                    </div>
                ` : ''}
            </div>
        `;
        
        if (this.options.animate && this.state.isAnimating) {
            this.startAnimation();
        }
    }
    
    bindEvents() {
        if (this.options.clickable) {
            this.addEventListener(this.container, 'click', () => {
                this.handleClick();
            });
        }
        
        // Hover effects
        this.addEventListener(this.container, 'mouseenter', () => {
            this.handleHover(true);
        });
        
        this.addEventListener(this.container, 'mouseleave', () => {
            this.handleHover(false);
        });
    }
    
    getStatusInfo(status) {
        const customState = this.options.customStates[status];
        if (customState) {
            return {
                ...customState,
                colorClass: customState.colorClass || this.getDefaultColorClass(status)
            };
        }
        
        const statusMap = {
            online: {
                icon: this.getStatusIcon('online'),
                text: 'Online',
                colorClass: 'status-success',
                tooltip: 'Server is online and responsive',
                description: 'All systems operational'
            },
            offline: {
                icon: this.getStatusIcon('offline'),
                text: 'Offline',
                colorClass: 'status-error',
                tooltip: 'Server is offline or unreachable',
                description: 'Server connection failed'
            },
            loading: {
                icon: this.getStatusIcon('loading'),
                text: 'Loading',
                colorClass: 'status-loading',
                tooltip: 'Checking server status...',
                description: 'Status check in progress'
            },
            warning: {
                icon: this.getStatusIcon('warning'),
                text: 'Warning',
                colorClass: 'status-warning',
                tooltip: 'Server has warnings or issues',
                description: 'Attention required'
            },
            error: {
                icon: this.getStatusIcon('error'),
                text: 'Error',
                colorClass: 'status-error',
                tooltip: 'Server has errors',
                description: 'Critical issues detected'
            },
            maintenance: {
                icon: this.getStatusIcon('maintenance'),
                text: 'Maintenance',
                colorClass: 'status-maintenance',
                tooltip: 'Server is under maintenance',
                description: 'Scheduled maintenance in progress'
            },
            unknown: {
                icon: this.getStatusIcon('unknown'),
                text: 'Unknown',
                colorClass: 'status-unknown',
                tooltip: 'Server status is unknown',
                description: 'Status could not be determined'
            },
            connected: {
                icon: this.getStatusIcon('connected'),
                text: 'Connected',
                colorClass: 'status-connected',
                tooltip: 'Live connection established',
                description: 'Real-time monitoring active'
            },
            disconnected: {
                icon: this.getStatusIcon('disconnected'),
                text: 'Disconnected',
                colorClass: 'status-disconnected',
                tooltip: 'Live connection lost',
                description: 'Real-time monitoring inactive'
            },
            pending: {
                icon: this.getStatusIcon('pending'),
                text: 'Pending',
                colorClass: 'status-pending',
                tooltip: 'Operation pending',
                description: 'Waiting for response'
            },
            success: {
                icon: this.getStatusIcon('success'),
                text: 'Success',
                colorClass: 'status-success',
                tooltip: 'Operation completed successfully',
                description: 'All good!'
            }
        };
        
        return statusMap[status] || statusMap.unknown;
    }
    
    getStatusIcon(status) {
        const iconMap = {
            online: '<i class="icon-check-circle"></i>',
            offline: '<i class="icon-x-circle"></i>',
            loading: '<i class="icon-loader"></i>',
            warning: '<i class="icon-alert-triangle"></i>',
            error: '<i class="icon-alert-circle"></i>',
            maintenance: '<i class="icon-tool"></i>',
            unknown: '<i class="icon-help-circle"></i>',
            connected: '<i class="icon-wifi"></i>',
            disconnected: '<i class="icon-wifi-off"></i>',
            pending: '<i class="icon-clock"></i>',
            success: '<i class="icon-check"></i>'
        };
        
        return iconMap[status] || iconMap.unknown;
    }
    
    getDefaultColorClass(status) {
        const colorMap = {
            online: 'status-success',
            connected: 'status-success',
            success: 'status-success',
            offline: 'status-error',
            disconnected: 'status-error',
            error: 'status-error',
            warning: 'status-warning',
            maintenance: 'status-warning',
            loading: 'status-loading',
            pending: 'status-loading',
            unknown: 'status-unknown'
        };
        
        return colorMap[status] || 'status-unknown';
    }
    
    updateStatus(newStatus, options = {}) {
        const previousStatus = this.state.status;
        
        if (previousStatus === newStatus && !options.force) {
            return; // No change needed
        }
        
        this.setState({
            previousStatus,
            status: newStatus,
            lastUpdate: Date.now()
        });
        
        // Trigger pulse animation if enabled
        if (this.options.pulseOnChange && this.options.animate) {
            this.triggerPulse();
        }
        
        // Re-render with new status
        this.render();
        
        // Emit status change event
        this.emit('statusChanged', {
            previous: previousStatus,
            current: newStatus,
            timestamp: this.state.lastUpdate
        });
        
        // Auto-clear temporary statuses
        if (options.duration) {
            setTimeout(() => {
                if (this.state.status === newStatus) {
                    this.updateStatus(options.revertTo || 'unknown');
                }
            }, options.duration);
        }
    }
    
    setLoading(loading = true) {
        if (loading) {
            this.setState({ 
                isAnimating: true,
                previousStatus: this.state.status
            });
            this.updateStatus('loading');
        } else {
            this.setState({ isAnimating: false });
            if (this.state.previousStatus) {
                this.updateStatus(this.state.previousStatus);
            }
        }
    }
    
    triggerPulse() {
        const indicator = this.container.querySelector('.status-indicator');
        if (!indicator) return;
        
        // Clear existing pulse
        if (this.pulseInterval) {
            clearTimeout(this.pulseInterval);
        }
        
        // Add pulse class
        indicator.classList.add('status-indicator--pulse');
        
        // Remove pulse class after animation
        this.pulseInterval = setTimeout(() => {
            indicator.classList.remove('status-indicator--pulse');
        }, 600);
    }
    
    startAnimation() {
        if (this.animationFrame) {
            cancelAnimationFrame(this.animationFrame);
        }
        
        const animate = () => {
            const loader = this.container.querySelector('.status-indicator__loading');
            if (loader && this.state.isAnimating) {
                // Rotate the loader
                const rotation = (Date.now() / 10) % 360;
                const spinner = loader.querySelector('.loading-spinner');
                if (spinner) {
                    spinner.style.transform = `rotate(${rotation}deg)`;
                }
                
                this.animationFrame = requestAnimationFrame(animate);
            }
        };
        
        if (this.state.isAnimating) {
            animate();
        }
    }
    
    shouldShowBadge() {
        // Override in subclasses or options to show badges
        return this.options.showBadge && this.getBadgeContent();
    }
    
    getBadgeContent() {
        // Override in subclasses or provide via options
        if (this.options.badgeContent) {
            return this.options.badgeContent;
        }
        
        // Show connection count for connected status
        if (this.state.status === 'connected' && this.options.connectionCount) {
            return this.options.connectionCount;
        }
        
        return null;
    }
    
    handleClick() {
        if (!this.options.clickable) return;
        
        this.emit('click', {
            status: this.state.status,
            timestamp: Date.now()
        });
        
        // Add click animation
        const indicator = this.container.querySelector('.status-indicator');
        if (indicator) {
            indicator.classList.add('status-indicator--clicked');
            setTimeout(() => {
                indicator.classList.remove('status-indicator--clicked');
            }, 200);
        }
    }
    
    handleHover(isHovering) {
        const indicator = this.container.querySelector('.status-indicator');
        if (!indicator) return;
        
        indicator.classList.toggle('status-indicator--hover', isHovering);
        
        this.emit('hover', {
            hovering: isHovering,
            status: this.state.status
        });
    }
    
    // Static factory methods for common patterns
    static createServerStatus(containerId, status = 'unknown', options = {}) {
        return new StatusIndicator(containerId, {
            status,
            showText: true,
            showIcon: true,
            animate: true,
            tooltip: true,
            ...options
        });
    }
    
    static createConnectionStatus(containerId, connected = false, options = {}) {
        return new StatusIndicator(containerId, {
            status: connected ? 'connected' : 'disconnected',
            showText: true,
            showIcon: true,
            animate: true,
            tooltip: true,
            variant: 'dot',
            ...options
        });
    }
    
    static createLoadingIndicator(containerId, options = {}) {
        return new StatusIndicator(containerId, {
            status: 'loading',
            showText: false,
            showIcon: true,
            animate: true,
            size: 'small',
            variant: 'dot',
            ...options
        });
    }
    
    static createCustomStatus(containerId, status, customConfig, options = {}) {
        const customStates = {};
        customStates[status] = customConfig;
        
        return new StatusIndicator(containerId, {
            status,
            customStates,
            ...options
        });
    }
    
    // Utility methods
    isOnline() {
        return this.state.status === 'online';
    }
    
    isOffline() {
        return this.state.status === 'offline';
    }
    
    isLoading() {
        return this.state.status === 'loading' || this.state.isAnimating;
    }
    
    hasError() {
        return ['error', 'offline'].includes(this.state.status);
    }
    
    hasWarning() {
        return ['warning', 'maintenance'].includes(this.state.status);
    }
    
    getStatusAge() {
        return Date.now() - this.state.lastUpdate;
    }
    
    getStatusAgeFormatted() {
        const age = this.getStatusAge();
        const seconds = Math.floor(age / 1000);
        const minutes = Math.floor(seconds / 60);
        const hours = Math.floor(minutes / 60);
        
        if (hours > 0) return `${hours}h ago`;
        if (minutes > 0) return `${minutes}m ago`;
        return `${seconds}s ago`;
    }
    
    // Animation helpers
    flash(duration = 1000) {
        const indicator = this.container.querySelector('.status-indicator');
        if (!indicator) return;
        
        indicator.classList.add('status-indicator--flash');
        setTimeout(() => {
            indicator.classList.remove('status-indicator--flash');
        }, duration);
    }
    
    bounce() {
        const indicator = this.container.querySelector('.status-indicator');
        if (!indicator) return;
        
        indicator.classList.add('status-indicator--bounce');
        setTimeout(() => {
            indicator.classList.remove('status-indicator--bounce');
        }, 500);
    }
    
    shake() {
        const indicator = this.container.querySelector('.status-indicator');
        if (!indicator) return;
        
        indicator.classList.add('status-indicator--shake');
        setTimeout(() => {
            indicator.classList.remove('status-indicator--shake');
        }, 500);
    }
    
    // Event emitter methods
    emit(eventName, data) {
        if (this.options.eventBus) {
            this.options.eventBus.emit(`status-indicator:${eventName}`, {
                component: this,
                ...data
            });
        }
        
        // Also emit on the container element
        const event = new CustomEvent(`statusIndicator:${eventName}`, {
            detail: data,
            bubbles: true
        });
        this.container.dispatchEvent(event);
    }
    
    onDestroy() {
        // Clean up animations
        if (this.animationFrame) {
            cancelAnimationFrame(this.animationFrame);
        }
        
        if (this.pulseInterval) {
            clearTimeout(this.pulseInterval);
        }
    }
}

// CSS classes that should be included in the stylesheet:
/*
.status-indicator {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    position: relative;
}

.status-indicator--small { font-size: 0.875rem; }
.status-indicator--medium { font-size: 1rem; }
.status-indicator--large { font-size: 1.125rem; }

.status-indicator--pill {
    padding: 0.25rem 0.75rem;
    border-radius: 9999px;
    background: rgba(255, 255, 255, 0.1);
}

.status-indicator--badge {
    padding: 0.125rem 0.5rem;
    border-radius: 0.25rem;
    font-weight: 600;
    text-transform: uppercase;
    font-size: 0.75rem;
}

.status-indicator--dot .status-indicator__icon-container {
    width: 0.75rem;
    height: 0.75rem;
    border-radius: 50%;
    overflow: hidden;
}

.status-indicator--clickable {
    cursor: pointer;
    transition: transform 0.2s ease;
}

.status-indicator--clickable:hover {
    transform: scale(1.05);
}

.status-indicator--animating .status-indicator__loading {
    display: block;
}

.status-indicator__icon-container {
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
}

.status-indicator__pulse {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    border-radius: 50%;
    animation: status-pulse 2s infinite;
    opacity: 0.6;
}

.status-indicator__loading {
    display: none;
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
}

.loading-spinner {
    width: 1rem;
    height: 1rem;
    border: 2px solid transparent;
    border-top: 2px solid currentColor;
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

.status-success { color: #22c55e; }
.status-error { color: #ef4444; }
.status-warning { color: #f59e0b; }
.status-loading { color: #3b82f6; }
.status-unknown { color: #6b7280; }
.status-connected { color: #10b981; }
.status-disconnected { color: #f87171; }
.status-maintenance { color: #8b5cf6; }
.status-pending { color: #06b6d4; }

@keyframes status-pulse {
    0% { transform: scale(1); opacity: 0.6; }
    50% { transform: scale(1.2); opacity: 0.3; }
    100% { transform: scale(1); opacity: 0.6; }
}

@keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}

.status-indicator--pulse {
    animation: status-pulse-single 0.6s ease-out;
}

.status-indicator--flash {
    animation: status-flash 1s ease-in-out;
}

.status-indicator--bounce {
    animation: status-bounce 0.5s ease-in-out;
}

.status-indicator--shake {
    animation: status-shake 0.5s ease-in-out;
}

@keyframes status-pulse-single {
    0% { transform: scale(1); }
    50% { transform: scale(1.1); }
    100% { transform: scale(1); }
}

@keyframes status-flash {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.3; }
}

@keyframes status-bounce {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-0.25rem); }
}

@keyframes status-shake {
    0%, 100% { transform: translateX(0); }
    25% { transform: translateX(-0.25rem); }
    75% { transform: translateX(0.25rem); }
}
*/