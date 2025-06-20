#!/usr/bin/env python3
"""
GUST Bot Auto-Authentication Setup Script
=========================================
This script sets up the auto-authentication system step by step.
Run this after reviewing the implementation guide.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def print_step(step, description):
    print(f"\n{'='*60}")
    print(f"STEP {step}: {description}")
    print('='*60)

def install_requirements():
    """Install required packages"""
    print_step(1, "Installing Required Packages")
    
    requirements = [
        'cryptography>=3.4.8',
        'schedule>=1.2.0'
    ]
    
    for req in requirements:
        try:
            print(f"Installing {req}...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', req])
            print(f"✅ {req} installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install {req}: {e}")
            return False
    
    return True

def create_directories():
    """Create required directories"""
    print_step(2, "Creating Required Directories")
    
    directories = [
        'data',
        'utils',
        'services',
        'static/js',
        'templates'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {directory}")

def create_credential_manager():
    """Create the credential manager module"""
    print_step(3, "Creating Credential Manager")
    
    credential_manager_code = '''"""
Secure credential storage and retrieval for auto-authentication
"""
import os
import json
import time
import logging
from cryptography.fernet import Fernet
from config import Config

logger = logging.getLogger(__name__)

class CredentialManager:
    def __init__(self):
        self.encryption_key = Config.get_encryption_key()
        self.fernet = Fernet(self.encryption_key)
        self.credentials_file = Config.CREDENTIALS_FILE
        
    def store_credentials(self, username, password, user_session_id=None):
        """Securely store G-Portal credentials for auto-authentication"""
        try:
            credential_data = {
                'username': username,
                'password': password,
                'stored_at': time.time(),
                'session_id': user_session_id or 'default'
            }
            
            json_data = json.dumps(credential_data)
            encrypted_data = self.fernet.encrypt(json_data.encode())
            
            os.makedirs(os.path.dirname(self.credentials_file), exist_ok=True)
            
            with open(self.credentials_file, 'wb') as f:
                f.write(encrypted_data)
            
            # Set secure file permissions (Windows compatible)
            try:
                os.chmod(self.credentials_file, 0o600)
            except OSError:
                pass  # Windows may not support chmod
            
            logger.info(f"SECURE: Credentials stored securely for {username}")
            return True
            
        except Exception as e:
            logger.error(f"ERROR: Failed to store credentials: {e}")
            return False
    
    def load_credentials(self):
        """Load and decrypt stored credentials"""
        try:
            if not os.path.exists(self.credentials_file):
                return None
                
            with open(self.credentials_file, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = self.fernet.decrypt(encrypted_data)
            credential_data = json.loads(decrypted_data.decode())
            
            return credential_data
            
        except Exception as e:
            logger.error(f"ERROR: Failed to load credentials: {e}")
            return None
    
    def clear_credentials(self):
        """Remove stored credentials"""
        try:
            if os.path.exists(self.credentials_file):
                os.remove(self.credentials_file)
                logger.info("INFO: Stored credentials cleared")
                return True
        except Exception as e:
            logger.error(f"ERROR: Failed to clear credentials: {e}")
        return False
    
    def credentials_exist(self):
        """Check if credentials are stored"""
        return os.path.exists(self.credentials_file)

# Global instance
credential_manager = CredentialManager()
'''
    
    # Use UTF-8 encoding for Windows compatibility
    with open('utils/credential_manager.py', 'w', encoding='utf-8') as f:
        f.write(credential_manager_code)
    
    print("✅ Created utils/credential_manager.py")

def create_auth_service():
    """Create the background authentication service"""
    print_step(4, "Creating Background Authentication Service")
    
    auth_service_code = '''"""
Background authentication service for continuous token renewal
"""
import time
import threading
import schedule
import logging
from datetime import datetime, timedelta
from utils.helpers import enhanced_refresh_token, validate_token_file
from utils.credential_manager import credential_manager
from config import Config

logger = logging.getLogger(__name__)

class BackgroundAuthService:
    def __init__(self):
        self.running = False
        self.thread = None
        self.last_renewal = None
        self.renewal_count = 0
        self.failure_count = 0
        
    def start(self):
        """Start the background authentication service"""
        if self.running:
            logger.warning("WARNING: Auth service already running")
            return
            
        if not Config.AUTO_AUTH_ENABLED:
            logger.info("INFO: Auto-authentication disabled in config")
            return
            
        if not credential_manager.credentials_exist():
            logger.info("INFO: No stored credentials, auth service not started")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run_service, daemon=True)
        self.thread.start()
        logger.info(f"SUCCESS: Background auth service started (renewal every {Config.AUTO_AUTH_RENEWAL_INTERVAL}s)")
    
    def stop(self):
        """Stop the background authentication service"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("INFO: Background auth service stopped")
    
    def _run_service(self):
        """Main service loop"""
        schedule.every(Config.AUTO_AUTH_RENEWAL_INTERVAL).seconds.do(self._renew_tokens)
        
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(10)
            except Exception as e:
                logger.error(f"ERROR: Auth service error: {e}")
                time.sleep(30)
    
    def _renew_tokens(self):
        """Perform token renewal"""
        try:
            logger.debug("DEBUG: Attempting background token renewal")
            
            if not self._should_renew_tokens():
                logger.debug("DEBUG: Token renewal not needed yet")
                return
            
            new_token = enhanced_refresh_token()
            
            if new_token:
                self.last_renewal = datetime.now()
                self.renewal_count += 1
                self.failure_count = 0
                logger.info(f"SUCCESS: Background token renewal successful (#{self.renewal_count})")
            else:
                self.failure_count += 1
                logger.warning(f"WARNING: Background token renewal failed (#{self.failure_count})")
                
                if self.failure_count >= Config.AUTO_AUTH_MAX_RETRIES:
                    logger.error("ERROR: Too many auth failures, pausing service for 10 minutes")
                    time.sleep(600)
                    self.failure_count = 0
                    
        except Exception as e:
            self.failure_count += 1
            logger.error(f"ERROR: Token renewal error: {e}")
    
    def _should_renew_tokens(self):
        """Check if tokens should be renewed"""
        try:
            if not validate_token_file():
                logger.debug("DEBUG: Token file invalid, renewal needed")
                return True
            
            if self.last_renewal:
                time_since_renewal = datetime.now() - self.last_renewal
                if time_since_renewal > timedelta(seconds=Config.AUTO_AUTH_RENEWAL_INTERVAL * 2):
                    logger.debug("DEBUG: Token renewal overdue")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"ERROR: Token check error: {e}")
            return True
    
    def get_status(self):
        """Get service status"""
        return {
            'running': self.running,
            'last_renewal': self.last_renewal.isoformat() if self.last_renewal else None,
            'renewal_count': self.renewal_count,
            'failure_count': self.failure_count,
            'credentials_stored': credential_manager.credentials_exist()
        }

# Global service instance
auth_service = BackgroundAuthService()
'''
    
    # Create services directory if it doesn't exist
    Path('services').mkdir(exist_ok=True)
    
    # Use UTF-8 encoding for Windows compatibility
    with open('services/auth_service.py', 'w', encoding='utf-8') as f:
        f.write(auth_service_code)
    
    # Create __init__.py for services package
    with open('services/__init__.py', 'w', encoding='utf-8') as f:
        f.write('# Services package\n')
    
    print("✅ Created services/auth_service.py")

def update_config():
    """Update config.py with auto-auth settings"""
    print_step(5, "Updating Configuration")
    
    config_additions = '''
# 🔐 Auto-authentication settings
AUTO_AUTH_ENABLED = os.environ.get('AUTO_AUTH_ENABLED', 'true').lower() == 'true'
AUTO_AUTH_ENCRYPTION_KEY = os.environ.get('AUTO_AUTH_KEY', None)
AUTO_AUTH_RENEWAL_INTERVAL = int(os.environ.get('AUTO_AUTH_INTERVAL', '180'))  # 3 minutes
AUTO_AUTH_MAX_RETRIES = int(os.environ.get('AUTO_AUTH_MAX_RETRIES', '3'))

# Credential storage paths
CREDENTIALS_FILE = os.path.join('data', 'secure_credentials.enc')

@classmethod
def get_encryption_key(cls):
    """Get or generate encryption key for credentials"""
    if cls.AUTO_AUTH_ENCRYPTION_KEY:
        return cls.AUTO_AUTH_ENCRYPTION_KEY.encode()
    
    # Generate new key if not exists
    key_file = os.path.join('data', '.auth_key')
    if os.path.exists(key_file):
        with open(key_file, 'rb') as f:
            return f.read()
    else:
        from cryptography.fernet import Fernet
        key = Fernet.generate_key()
        os.makedirs('data', exist_ok=True)
        with open(key_file, 'wb') as f:
            f.write(key)
        # Make file read-only
        os.chmod(key_file, 0o600)
        return key
'''
    
    print("📝 Configuration additions to add to your config.py:")
    print(config_additions)
    print("\n⚠️  Please manually add the above code to your Config class in config.py")

def create_env_template():
    """Create .env template"""
    print_step(6, "Creating Environment Template")
    
    env_template = '''# GUST Bot Auto-Authentication Settings
AUTO_AUTH_ENABLED=true
AUTO_AUTH_INTERVAL=180
AUTO_AUTH_MAX_RETRIES=3

# Optional: Custom encryption key (generates automatically if not set)
# AUTO_AUTH_KEY=your-secure-base64-key-here
'''
    
    with open('.env.example', 'w') as f:
        f.write(env_template)
    
    print("✅ Created .env.example")
    print("💡 Copy to .env and customize as needed")

def create_frontend_script():
    """Create enhanced frontend JavaScript"""
    print_step(7, "Creating Frontend JavaScript")
    
    js_code = '''// Auto-authentication management
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
        
        statusElement.innerHTML = `
            <div class="auto-auth-indicator ${isActive ? 'active' : 'inactive'}">
                <span class="status-dot"></span>
                <span class="status-text">
                    ${isActive ? '🔐 Auto-auth Active' : '📴 Auto-auth Inactive'}
                </span>
                ${status.service_status.renewal_count > 0 ? 
                    `<span class="renewal-count">(${status.service_status.renewal_count} renewals)</span>` : ''}
            </div>
        `;
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
        console.log(`${type.toUpperCase()}: ${message}`);
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
                showNotification('🔐 Auto-authentication enabled! You\\'ll stay logged in automatically.', 'success');
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
'''
    
    with open('static/js/auto_auth.js', 'w') as f:
        f.write(js_code)
    
    print("✅ Created static/js/auto_auth.js")

def show_next_steps():
    """Show manual steps that need to be completed"""
    print_step(8, "Manual Integration Steps")
    
    steps = [
        "1. Add configuration additions to your config.py (shown above)",
        "2. Update your routes/auth.py with enhanced login route",
        "3. Update your utils/helpers.py with enhanced functions",
        "4. Add auto-auth checkbox to your login template",
        "5. Include auto_auth.js in your templates",
        "6. Initialize auth service in your main app.py",
        "7. Test the implementation step by step"
    ]
    
    for step in steps:
        print(f"   {step}")
    
    print("\n📚 Refer to the implementation guide for detailed code changes.")
    print("🎯 Priority: Complete steps 1-3 first for core functionality.")

def main():
    """Main setup function"""
    print("🚀 GUST Bot Auto-Authentication Setup")
    print("====================================")
    
    try:
        if not install_requirements():
            print("❌ Setup failed at package installation")
            return
        
        create_directories()
        create_credential_manager()
        create_auth_service()
        update_config()
        create_env_template()
        create_frontend_script()
        show_next_steps()
        
        print("\n✅ SETUP COMPLETE!")
        print("🎯 Follow the manual steps above to complete integration.")
        print("📖 Review the implementation guide for detailed instructions.")
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        print("Please review the error and try again.")

if __name__ == "__main__":
    main()
