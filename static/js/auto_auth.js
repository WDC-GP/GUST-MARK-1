// Auto-authentication management - COMPLETE FIXED VERSION
class AutoAuthManager {
    constructor() {
        this.statusInterval = null;
        this.initialized = false;
        console.log('[AutoAuth] Initializing AutoAuthManager...');
        this.init();
    }
    
    init() {
        try {
            this.setupStatusMonitoring();
            this.setupControls();
            this.initialized = true;
            console.log('[AutoAuth] ✅ AutoAuthManager initialized successfully');
        } catch (error) {
            console.error('[AutoAuth] ❌ Initialization failed:', error);
        }
    }
    
    setupStatusMonitoring() {
        // Clear any existing interval
        if (this.statusInterval) {
            clearInterval(this.statusInterval);
        }
        
        // Set up status monitoring every 30 seconds
        this.statusInterval = setInterval(() => {
            this.updateStatus();
        }, 30000);
        
        // Initial status update
        this.updateStatus();
    }
    
    setupControls() {
        // Setup any UI controls for auto-auth
        const toggleButton = document.getElementById('auto-auth-toggle');
        if (toggleButton) {
            toggleButton.addEventListener('click', (e) => {
                this.toggleAutoAuth(e.target.checked);
            });
        }
        
        const enableCheckbox = document.getElementById('enableAutoAuth');
        if (enableCheckbox) {
            enableCheckbox.addEventListener('change', (e) => {
                console.log('[AutoAuth] Auto-auth preference changed:', e.target.checked);
            });
        }
    }
    
    async updateStatus() {
        try {
            // FIXED: Correct URL without /auth prefix
            const response = await fetch('/auto-auth/status');
            if (response.ok) {
                const status = await response.json();
                this.displayStatus(status);
            } else {
                console.warn('[AutoAuth] ⚠️ Status update failed:', response.status);
                this.displayStatus({ enabled: false, credentials_stored: false, service_status: { running: false } });
            }
        } catch (error) {
            console.error('[AutoAuth] ❌ Status error:', error);
            // Display fallback status
            this.displayStatus({ enabled: false, credentials_stored: false, service_status: { running: false } });
        }
    }
    
    displayStatus(status) {
        const statusElement = document.getElementById('auto-auth-status');
        if (!statusElement) {
            console.log('[AutoAuth] No status element found, skipping display');
            return;
        }
        
        const isActive = status.enabled && status.credentials_stored && 
                        (status.service_status && status.service_status.running);
        
        const renewalCount = status.service_status && status.service_status.renewal_count ? 
                           status.service_status.renewal_count : 0;
        
        // FIXED: Proper template literal syntax
        statusElement.innerHTML = `
            <div class="auto-auth-indicator ${isActive ? 'active' : 'inactive'}">
                <span class="status-dot"></span>
                <span class="status-text">
                    ${isActive ? 'AUTO-AUTH: Active' : 'AUTO-AUTH: Inactive'}
                </span>
                ${renewalCount > 0 ? 
                    `<span class="renewal-count">(${renewalCount} renewals)</span>` : ''}
            </div>
        `;
        
        console.log('[AutoAuth] Status updated:', isActive ? 'Active' : 'Inactive');
    }
    
    async toggleAutoAuth(enable) {
        try {
            console.log('[AutoAuth] Toggling auto-auth:', enable);
            
            // FIXED: Correct URL without /auth prefix
            const response = await fetch('/auto-auth/toggle', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ enable })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showNotification(result.message || 'Auto-auth toggled successfully', 'success');
                // Update status after successful toggle
                setTimeout(() => this.updateStatus(), 1000);
            } else {
                this.showNotification(result.error || 'Toggle failed', 'error');
            }
        } catch (error) {
            console.error('[AutoAuth] ❌ Toggle failed:', error);
            this.showNotification('Auto-auth toggle failed - network error', 'error');
        }
    }
    
    showNotification(message, type = 'info') {
        console.log(`[AutoAuth] ${type.toUpperCase()}: ${message}`);
        
        // Try to use existing notification system
        if (typeof showNotification === 'function') {
            showNotification(message, type);
            return;
        }
        
        // Fallback notification system
        this.createFallbackNotification(message, type);
    }
    
    createFallbackNotification(message, type) {
        // Remove any existing notifications
        const existing = document.querySelectorAll('.auto-auth-notification');
        existing.forEach(n => n.remove());
        
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `auto-auth-notification notification-${type}`;
        notification.textContent = message;
        
        // Style the notification
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 12px 20px;
            border-radius: 6px;
            color: white;
            background: ${this.getNotificationColor(type)};
            z-index: 9999;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-size: 14px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            max-width: 300px;
            word-wrap: break-word;
            animation: slideInFromRight 0.3s ease;
        `;
        
        // Add animation styles if not already present
        if (!document.getElementById('auto-auth-animations')) {
            const style = document.createElement('style');
            style.id = 'auto-auth-animations';
            style.textContent = `
                @keyframes slideInFromRight {
                    from { transform: translateX(100%); opacity: 0; }
                    to { transform: translateX(0); opacity: 1; }
                }
                @keyframes slideOutToRight {
                    from { transform: translateX(0); opacity: 1; }
                    to { transform: translateX(100%); opacity: 0; }
                }
            `;
            document.head.appendChild(style);
        }
        
        document.body.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.style.animation = 'slideOutToRight 0.3s ease';
                setTimeout(() => {
                    if (notification.parentNode) {
                        notification.remove();
                    }
                }, 300);
            }
        }, 5000);
    }
    
    getNotificationColor(type) {
        const colors = {
            'success': '#28a745',
            'error': '#dc3545', 
            'warning': '#ffc107',
            'info': '#17a2b8'
        };
        return colors[type] || colors.info;
    }
    
    destroy() {
        if (this.statusInterval) {
            clearInterval(this.statusInterval);
            this.statusInterval = null;
        }
        this.initialized = false;
        console.log('[AutoAuth] ✅ AutoAuthManager destroyed');
    }
}

// Enhanced login function - STREAMLINED VERSION
function enhancedLogin() {
    console.log('[AutoAuth] Enhanced login function called');
    
    const form = document.getElementById('loginForm');
    if (!form) {
        console.error('[AutoAuth] ❌ Login form not found');
        return Promise.reject(new Error('Login form not found'));
    }
    
    // FIXED: Direct element access instead of FormData
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');
    const enableAutoAuthCheckbox = document.getElementById('enableAutoAuth');
    
    const username = usernameInput ? usernameInput.value.trim() : '';
    const password = passwordInput ? passwordInput.value.trim() : '';
    const enableAutoAuthValue = enableAutoAuthCheckbox ? enableAutoAuthCheckbox.checked : false;
    
    // Validation
    if (!username || !password) {
        const error = new Error('Please enter both username and password');
        showNotificationSafe(error.message, 'error');
        return Promise.reject(error);
    }
    
    // Debug logging
    console.log('[AutoAuth] Extracted data:', {
        username: username ? `${username.length} chars` : 'empty',
        password: password ? `${password.length} chars` : 'empty',
        autoAuth: enableAutoAuthValue
    });
    
    const loginData = {
        username: username,
        password: password,
        enable_auto_auth: enableAutoAuthValue
    };
    
    console.log('[AutoAuth] Login data prepared, auto-auth enabled:', enableAutoAuthValue);
    
    // Show loading state
    const submitButton = form.querySelector('button[type="submit"]') || form.querySelector('#loginButton');
    const loadingDiv = document.getElementById('loading');
    const errorDiv = document.getElementById('error');
    const originalText = submitButton ? submitButton.textContent : '';
    
    if (submitButton) {
        submitButton.disabled = true;
        submitButton.textContent = 'Authenticating...';
    }
    if (loadingDiv) loadingDiv.classList.remove('hidden');
    if (errorDiv) errorDiv.classList.add('hidden');
    
    // FIXED: Correct URL without /auth prefix
    return fetch('/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(loginData)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('[AutoAuth] Login response received:', data.success);
        
        if (data.success) {
            if (data.auto_auth_enabled) {
                showNotificationSafe('✅ Auto-authentication enabled! You will stay logged in automatically.', 'success');
            } else {
                showNotificationSafe('✅ Login successful!', 'success');
            }
            
            // Redirect to dashboard
            setTimeout(() => {
                window.location.href = data.redirect_url || '/';
            }, 1000);
            
            return data;
        } else {
            throw new Error(data.error || 'Login failed');
        }
    })
    .catch(error => {
        console.error('[AutoAuth] ❌ Login error:', error);
        showNotificationSafe(error.message || 'Login failed - network error', 'error');
        throw error;
    })
    .finally(() => {
        // Restore button state
        if (submitButton) {
            submitButton.disabled = false;
            submitButton.textContent = originalText || 'Login';
        }
        if (loadingDiv) loadingDiv.classList.add('hidden');
    });
}

// Safe notification function that works everywhere
function showNotificationSafe(message, type = 'info') {
    console.log(`[AutoAuth] ${type.toUpperCase()}: ${message}`);
    
    // Try multiple notification systems
    if (typeof showNotification === 'function') {
        showNotification(message, type);
    } else if (window.autoAuthManager && window.autoAuthManager.showNotification) {
        window.autoAuthManager.showNotification(message, type);
    } else {
        // Create a simple notification in the error div
        const errorDiv = document.getElementById('error');
        if (errorDiv) {
            errorDiv.textContent = message;
            errorDiv.className = `mt-4 text-sm ${type === 'success' ? 'text-green-500' : type === 'error' ? 'text-red-500' : 'text-blue-500'}`;
            errorDiv.classList.remove('hidden');
            
            // Auto-hide success messages
            if (type === 'success') {
                setTimeout(() => {
                    errorDiv.classList.add('hidden');
                }, 3000);
            }
        }
    }
}

// Make functions globally available
window.showNotificationSafe = showNotificationSafe;
window.enhancedLogin = enhancedLogin;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    console.log('[AutoAuth] 🚀 DOM loaded, initializing AutoAuth system...');
    
    // Only initialize if we have auto-auth elements or if this is the login page
    const hasAutoAuthElements = document.getElementById('auto-auth-status') || 
                               document.getElementById('enableAutoAuth') ||
                               document.getElementById('loginForm');
    
    if (hasAutoAuthElements) {
        try {
            // Create global instance
            window.autoAuthManager = new AutoAuthManager();
            console.log('[AutoAuth] ✅ Global AutoAuthManager created and ready');
        } catch (error) {
            console.error('[AutoAuth] ❌ Failed to create AutoAuthManager:', error);
            
            // Create a dummy manager to prevent errors
            window.autoAuthManager = {
                updateStatus: () => console.log('[AutoAuth] Dummy status update'),
                toggleAutoAuth: () => console.log('[AutoAuth] Dummy toggle'),
                showNotification: showNotificationSafe,
                destroy: () => console.log('[AutoAuth] Dummy destroy')
            };
        }
    } else {
        console.log('[AutoAuth] ℹ️ No auto-auth elements found, skipping initialization');
    }
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (window.autoAuthManager && typeof window.autoAuthManager.destroy === 'function') {
        window.autoAuthManager.destroy();
    }
});

// Export for module systems (if needed)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { AutoAuthManager, enhancedLogin, showNotificationSafe };
}