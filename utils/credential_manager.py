"""
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
