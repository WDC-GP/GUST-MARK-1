// Auto-authentication management
class AutoAuthManager {
    constructor() {
        this.statusInterval = null;
        this.init();
    }
    
    init() {
        this.setupStatusMonitoring();
        this.setupControls();
    }
    
    setupStatusMonitoring() {
        this.statusInterval = setInterval(() => {
            this.updateStatus();
        }, 30000);
        
        this.updateStatus();
    }
    
    async updateStatus() {
        try {
            const response = await fetch('/auth/auto-auth/status');
            const status = await response.json();
            
            this.displayStatus(status);
        } catch (error) {
            console.error('Auto-auth status error:', error);
        }
    }
    
    displayStatus(status) {
        const statusElement = document.getElementById('auto-auth-status');
        if (!statusElement) return;
        
        const isActive = status.enabled && status.credentials_stored && 
                        status.service_status.running;
        
        statusElement.innerHTML = 
            <div class="auto-auth-indicator " + (isActive ? 'active' : 'inactive') + ">
                <span class="status-dot"></span>
                <span class="status-text">
                     + (isActive ? 'AUTO-AUTH: Active' : 'AUTO-AUTH: Inactive') + 
                </span>
                 + (status.service_status.renewal_count > 0 ? 
                    <span class="renewal-count">( + status.service_status.renewal_count +  renewals)</span> : '') + 
            </div>
        ;
    }
    
    async toggleAutoAuth(enable) {
        try {
            const response = await fetch('/auth/auto-auth/toggle', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ enable })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showNotification(result.message, 'success');
                this.updateStatus();
            } else {
                this.showNotification(result.error, 'error');
            }
        } catch (error) {
            this.showNotification('Auto-auth toggle failed', 'error');
        }
    }
    
    showNotification(message, type) {
        console.log(type.toUpperCase() + ': ' + message);
        // Integrate with your existing notification system
    }
}

// Enhanced login function
function enhancedLogin() {
    const form = document.getElementById('loginForm');
    const enableAutoAuth = document.getElementById('enableAutoAuth')?.checked || false;
    
    const formData = new FormData(form);
    const loginData = {
        username: formData.get('username'),
        password: formData.get('password'),
        enable_auto_auth: enableAutoAuth
    };
    
    fetch('/auth/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(loginData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            if (data.auto_auth_enabled) {
                showNotification('Auto-authentication enabled! You will stay logged in automatically.', 'success');
            }
            window.location.href = '/dashboard';
        } else {
            showNotification(data.error, 'error');
        }
    })
    .catch(error => {
        showNotification('Login failed', 'error');
    });
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('auto-auth-status')) {
        new AutoAuthManager();
    }
});
