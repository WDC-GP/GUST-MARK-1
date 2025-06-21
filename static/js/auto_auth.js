// GUST Bot Enhanced - Auto-Authentication Manager
// =============================================
// Complete working version with no external dependencies

console.log('[AutoAuth] Loading auto-authentication manager...');

// Auto-authentication manager class
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
        // Setup auto-auth checkbox if it exists
        const enableCheckbox = document.getElementById('enableAutoAuth');
        if (enableCheckbox) {
            enableCheckbox.addEventListener('change', (e) => {
                console.log('[AutoAuth] Auto-auth preference changed:', e.target.checked);
                
                // Update form validation when checkbox changes
                if (typeof updateFormValidation === 'function') {
                    updateFormValidation();
                } else if (typeof window.updateFormValidation === 'function') {
                    window.updateFormValidation();
                }
            });
        }
    }
    
    async updateStatus() {
        try {
            const response = await fetch('/auto-auth/status');
            if (response.ok) {
                const status = await response.json();
                this.displayStatus(status);
            } else {
                console.warn('[AutoAuth] ⚠️ Status update failed:', response.status);
                this.displayStatus({ 
                    enabled: false, 
                    credentials_stored: false, 
                    service_status: { running: false } 
                });
            }
        } catch (error) {
            console.error('[AutoAuth] ❌ Status error:', error);
            // Display fallback status
            this.displayStatus({ 
                enabled: false, 
                credentials_stored: false, 
                service_status: { running: false } 
            });
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
        
        // Try to use existing error display system
        const errorDiv = document.getElementById('error');
        if (errorDiv) {
            errorDiv.textContent = message;
            errorDiv.className = `mt-4 text-sm ${
                type === 'success' ? 'text-green-500' : 
                type === 'error' ? 'text-red-500' : 
                'text-blue-500'
            }`;
            errorDiv.classList.remove('hidden');
            
            // Auto-hide success messages
            if (type === 'success') {
                setTimeout(() => {
                    errorDiv.classList.add('hidden');
                }, 3000);
            }
        }
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

// Enhanced login function with proper auto-auth support
function enhancedLogin() {
    console.log('[AutoAuth] Enhanced login function called');
    
    const form = document.getElementById('loginForm');
    if (!form) {
        console.error('[AutoAuth] ❌ Login form not found');
        return Promise.reject(new Error('Login form not found'));
    }
    
    // Get form elements
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');
    const enableAutoAuthCheckbox = document.getElementById('enableAutoAuth');
    
    const username = usernameInput ? usernameInput.value.trim() : '';
    const password = passwordInput ? passwordInput.value.trim() : '';
    const enableAutoAuthValue = enableAutoAuthCheckbox ? enableAutoAuthCheckbox.checked : false;
    
    // Validation - only require credentials if auto-auth is NOT enabled
    if (!username || !password) {
        if (!enableAutoAuthValue) {
            const error = new Error('Please enter both username and password, or enable auto-authentication');
            // Use safe error display
            const errorDiv = document.getElementById('error');
            if (errorDiv) {
                errorDiv.textContent = error.message;
                errorDiv.className = 'mt-4 text-red-500 text-sm';
                errorDiv.classList.remove('hidden');
            }
            return Promise.reject(error);
        } else {
            // Auto-auth enabled with empty credentials - this is allowed!
            console.log('[AutoAuth] 🔐 Auto-auth enabled with empty credentials - proceeding to server');
        }
    }
    
    // Debug logging
    console.log('[AutoAuth] Extracted data:', {
        username: username ? `${username.length} chars` : 'empty',
        password: password ? `${password.length} chars` : 'empty',
        autoAuth: enableAutoAuthValue,
        allowingEmptyCredentials: enableAutoAuthValue && (!username || !password)
    });
    
    const loginData = {
        username: username,
        password: password,
        enable_auto_auth: enableAutoAuthValue
    };
    
    console.log('[AutoAuth] Proceeding with login request...');
    
    // Show loading state
    const submitButton = form.querySelector('button[type="submit"]') || form.querySelector('#loginButton');
    const loadingDiv = document.getElementById('loading');
    const errorDiv = document.getElementById('error');
    const originalText = submitButton ? submitButton.textContent : '';
    
    if (submitButton) {
        submitButton.disabled = true;
        submitButton.textContent = enableAutoAuthValue && (!username || !password) ? 
            'Auto-authenticating...' : 'Authenticating...';
    }
    if (loadingDiv) loadingDiv.classList.remove('hidden');
    if (errorDiv) errorDiv.classList.add('hidden');
    
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
            let message = '✅ Login successful!';
            
            if (data.auto_auth_enabled && data.auto_auth_used) {
                message = '✅ Auto-authentication successful! Logged in using stored credentials.';
            } else if (data.auto_auth_enabled) {
                message = '✅ Login successful with auto-authentication enabled! Future logins will be automatic.';
            }
            
            // Safe success display
            if (errorDiv) {
                errorDiv.textContent = message;
                errorDiv.className = 'mt-4 text-green-500 text-sm';
                errorDiv.classList.remove('hidden');
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
        
        // Enhanced error messaging for auto-auth scenarios
        let errorMessage = error.message || 'Login failed - network error';
        if (enableAutoAuthValue && (!username || !password)) {
            if (errorMessage.includes('No stored credentials')) {
                errorMessage = '🔐 Auto-auth failed: No stored credentials found. Please enter your username and password to set up auto-authentication.';
            } else if (errorMessage.includes('Stored credentials are no longer valid')) {
                errorMessage = '🔐 Auto-auth failed: Stored credentials expired. Please enter your current username and password to update auto-authentication.';
            }
        }
        
        // Safe error display
        if (errorDiv) {
            errorDiv.textContent = errorMessage;
            errorDiv.className = 'mt-4 text-red-500 text-sm';
            errorDiv.classList.remove('hidden');
        }
        
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

// Dynamic form validation management
function updateFormValidation() {
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');
    const enableAutoAuthCheckbox = document.getElementById('enableAutoAuth');
    const autoAuthHelp = document.getElementById('auto-auth-help');
    
    if (!usernameInput || !passwordInput || !enableAutoAuthCheckbox) {
        return;
    }
    
    const autoAuthEnabled = enableAutoAuthCheckbox.checked;
    
    if (autoAuthEnabled) {
        // Remove required attributes when auto-auth is enabled
        usernameInput.removeAttribute('required');
        passwordInput.removeAttribute('required');
        if (autoAuthHelp) autoAuthHelp.classList.remove('hidden');
        console.log('[AutoAuth] ✅ Required attributes removed (auto-auth enabled)');
    } else {
        // Add required attributes when auto-auth is disabled
        usernameInput.setAttribute('required', 'required');
        passwordInput.setAttribute('required', 'required');
        if (autoAuthHelp) autoAuthHelp.classList.add('hidden');
        console.log('[AutoAuth] ✅ Required attributes restored (auto-auth disabled)');
    }
}

// Safe notification function
function showNotificationSafe(message, type = 'info') {
    console.log(`[AutoAuth] ${type.toUpperCase()}: ${message}`);
    
    // Use the error div for all notifications
    const errorDiv = document.getElementById('error');
    if (errorDiv) {
        errorDiv.textContent = message;
        errorDiv.className = `mt-4 text-sm ${
            type === 'success' ? 'text-green-500' : 
            type === 'error' ? 'text-red-500' : 
            'text-blue-500'
        }`;
        errorDiv.classList.remove('hidden');
        
        // Auto-hide success messages
        if (type === 'success') {
            setTimeout(() => {
                errorDiv.classList.add('hidden');
            }, 3000);
        }
    }
}

// Make functions globally available
window.enhancedLogin = enhancedLogin;
window.updateFormValidation = updateFormValidation;
window.showNotificationSafe = showNotificationSafe;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    console.log('[AutoAuth] 🚀 DOM loaded, initializing AutoAuth system...');
    
    // Only initialize if we have auto-auth elements
    const hasAutoAuthElements = document.getElementById('auto-auth-status') || 
                               document.getElementById('enableAutoAuth') ||
                               document.getElementById('loginForm');
    
    if (hasAutoAuthElements) {
        try {
            // Create global instance
            window.autoAuthManager = new AutoAuthManager();
            console.log('[AutoAuth] ✅ Global AutoAuthManager created and ready');
            
            // Setup form validation management
            const enableAutoAuthCheckbox = document.getElementById('enableAutoAuth');
            if (enableAutoAuthCheckbox) {
                enableAutoAuthCheckbox.addEventListener('change', updateFormValidation);
                // Initial validation setup
                updateFormValidation();
            }
            
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
    module.exports = { AutoAuthManager, enhancedLogin, showNotificationSafe, updateFormValidation };
}

console.log('[AutoAuth] ✅ Auto-authentication manager loaded successfully');