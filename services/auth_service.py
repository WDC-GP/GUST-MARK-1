"""
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
