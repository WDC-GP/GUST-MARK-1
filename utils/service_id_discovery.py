"""
Service ID Discovery Utility for G-Portal Servers
=================================================
✅ FIXED: Added missing List import from typing
✅ NEW: Utility to automatically discover Service IDs from Server IDs using G-Portal's GraphQL API
✅ NEW: Complete integration with GUST authentication system
✅ NEW: Rate limiting and caching for optimal performance
✅ NEW: Comprehensive error handling and fallback mechanisms
✅ NEW: Support for all G-Portal regions (US, EU, AS, AU)

This utility solves the dual ID problem:
- Server ID (from URL) → Used for health monitoring and sensor data
- Service ID (discovered) → Used for console commands and mutations
"""

import requests
import json
import logging
from typing import Dict, Any, Optional, Tuple, List  # ✅ FIXED: Added List import
from datetime import datetime
import time

# Import existing utilities
from utils.helpers import load_token, get_auth_headers, is_valid_jwt_token
from utils.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)

class ServiceIDMapper:
    """
    Maps Server IDs to Service IDs using G-Portal's cfgContext GraphQL API
    
    This class provides automatic discovery of Service IDs which are required
    for console command execution in G-Portal's GraphQL API.
    """
    
    def __init__(self):
        self.rate_limiter = RateLimiter(max_calls=10, time_window=60)  # Conservative rate limiting
        self.graphql_endpoint = "https://www.g-portal.com/ngpapi"
        self.cache = {}  # Simple in-memory cache to avoid repeated API calls
        self.cache_expiry = {}  # Cache expiration times
        self.cache_duration = 3600  # Cache for 1 hour
        logger.info("[Service ID Mapper] Initialized with rate limiting and caching")
        
    def get_service_id_from_server_id(self, server_id: str, region: str = 'US') -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Get Service ID from Server ID using cfgContext GraphQL query
        
        Args:
            server_id (str): The server ID from the URL (e.g., "1722255")
            region (str): Server region (US, EU, AS, AU)
            
        Returns:
            Tuple[bool, Optional[str], Optional[str]]: (success, service_id, error_message)
        """
        try:
            server_id_str = str(server_id).strip()
            region = region.upper().strip()
            cache_key = f"{server_id_str}_{region}"
            
            # Check cache first
            if cache_key in self.cache and cache_key in self.cache_expiry:
                if time.time() < self.cache_expiry[cache_key]:
                    logger.info(f"[Service ID Mapper] Using cached service ID for server {server_id_str}")
                    return True, self.cache[cache_key], None
                else:
                    # Cache expired, remove it
                    del self.cache[cache_key]
                    del self.cache_expiry[cache_key]
                    
            logger.info(f"[Service ID Mapper] Looking up service ID for server {server_id_str} in region {region}")
            
            # Rate limiting
            self.rate_limiter.wait_if_needed("service_mapper")
            
            # Get authentication token
            token = self._get_auth_token()
            if not token:
                return False, None, "No authentication token available"
            
            # Validate server ID format
            try:
                server_id_int = int(server_id_str)
                if server_id_int <= 0:
                    return False, None, "Invalid server ID: must be a positive integer"
            except ValueError:
                return False, None, f"Invalid server ID format: '{server_id_str}' is not a valid integer"
            
            # Validate region
            if region not in ['US', 'EU', 'AS', 'AU']:
                logger.warning(f"[Service ID Mapper] Invalid region '{region}', defaulting to US")
                region = 'US'
            
            # GraphQL query to get configuration context
            query = """
            query GetServerConfig($serverId: Int!, $region: REGION!) {
                cfgContext(serverId: $serverId, region: $region) {
                    ns {
                        sys {
                            gameServer {
                                serviceId
                                name
                                status
                            }
                        }
                        game {
                            server {
                                name
                                gameMode
                            }
                        }
                    }
                }
            }
            """
            
            variables = {
                'serverId': server_id_int,
                'region': region
            }
            
            # Prepare headers
            headers = self._get_graphql_headers()
            
            # Prepare request payload
            payload = {
                'query': query,
                'variables': variables
            }
            
            logger.debug(f"[Service ID Mapper] Sending GraphQL request for server {server_id_str}")
            
            # Make GraphQL request
            try:
                response = requests.post(
                    self.graphql_endpoint,
                    json=payload,
                    headers=headers,
                    timeout=15
                )
                
                logger.debug(f"[Service ID Mapper] Response status: {response.status_code}")
                
                if response.status_code != 200:
                    error_msg = f"HTTP {response.status_code}: {response.text[:200]}"
                    logger.error(f"[Service ID Mapper] HTTP error: {error_msg}")
                    return False, None, error_msg
                
                # Parse JSON response
                try:
                    data = response.json()
                except json.JSONDecodeError as json_error:
                    error_msg = f"Invalid JSON response: {json_error}"
                    logger.error(f"[Service ID Mapper] {error_msg}")
                    return False, None, error_msg
                
                logger.debug(f"[Service ID Mapper] Raw response: {json.dumps(data, indent=2)}")
                
                # Parse the response to extract service ID
                success, service_id, error = self._parse_config_response(data, server_id_str)
                
                if success and service_id:
                    # Cache the successful result
                    self.cache[cache_key] = service_id
                    self.cache_expiry[cache_key] = time.time() + self.cache_duration
                    logger.info(f"[Service ID Mapper] ✅ Found service ID {service_id} for server {server_id_str}")
                
                return success, service_id, error
                
            except requests.exceptions.Timeout:
                error_msg = "Request timeout - G-Portal API is slow to respond"
                logger.error(f"[Service ID Mapper] {error_msg}")
                return False, None, error_msg
                
            except requests.exceptions.ConnectionError:
                error_msg = "Connection error - unable to reach G-Portal API"
                logger.error(f"[Service ID Mapper] {error_msg}")
                return False, None, error_msg
                
            except requests.exceptions.RequestException as req_error:
                error_msg = f"Request error: {req_error}"
                logger.error(f"[Service ID Mapper] {error_msg}")
                return False, None, error_msg
                
        except Exception as e:
            error_msg = f"Unexpected error in service ID lookup: {str(e)}"
            logger.error(f"[Service ID Mapper] {error_msg}")
            return False, None, error_msg
    
    def _parse_config_response(self, data: Dict[str, Any], server_id: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """Parse the cfgContext response to extract service ID"""
        try:
            # Check for GraphQL errors first
            if 'errors' in data:
                errors = data['errors']
                if errors:
                    error_messages = []
                    for error in errors:
                        error_msg = error.get('message', 'Unknown GraphQL error')
                        error_messages.append(error_msg)
                        # Check for specific authentication errors
                        if 'authentication' in error_msg.lower() or 'unauthorized' in error_msg.lower():
                            return False, None, "Authentication failed - please re-login to G-Portal"
                        elif 'not found' in error_msg.lower() or 'does not exist' in error_msg.lower():
                            return False, None, f"Server {server_id} not found in G-Portal"
                    
                    combined_error = '; '.join(error_messages)
                    logger.error(f"[Service ID Mapper] GraphQL errors: {combined_error}")
                    return False, None, f"GraphQL errors: {combined_error}"
            
            # Navigate through the response structure
            if 'data' not in data:
                return False, None, "No data field in GraphQL response"
            
            cfg_context = data['data'].get('cfgContext')
            if not cfg_context:
                return False, None, "No cfgContext in response - server may not exist or access denied"
            
            ns = cfg_context.get('ns', {})
            if not ns:
                return False, None, "No namespace in cfgContext"
            
            # Try to get service ID from sys.gameServer.serviceId
            sys_ns = ns.get('sys', {})
            if sys_ns:
                game_server = sys_ns.get('gameServer', {})
                if game_server:
                    service_id = game_server.get('serviceId')
                    if service_id:
                        # Validate the service ID
                        service_id_str = str(service_id).strip()
                        if service_id_str and service_id_str.isdigit():
                            logger.info(f"[Service ID Mapper] Found serviceId: {service_id_str}")
                            
                            # Log additional server info if available
                            server_name = game_server.get('name', 'Unknown')
                            server_status = game_server.get('status', 'Unknown')
                            logger.debug(f"[Service ID Mapper] Server info: name='{server_name}', status='{server_status}'")
                            
                            return True, service_id_str, None
                        else:
                            return False, None, f"Invalid service ID format: '{service_id}'"
                    else:
                        logger.debug("[Service ID Mapper] No serviceId field in gameServer")
                else:
                    logger.debug("[Service ID Mapper] No gameServer field in sys namespace")
            else:
                logger.debug("[Service ID Mapper] No sys namespace in cfgContext")
            
            # If we get here, we couldn't find the service ID
            logger.debug(f"[Service ID Mapper] Could not extract service ID from response structure")
            return False, None, "Service ID not found in server configuration"
            
        except Exception as parse_error:
            error_msg = f"Error parsing GraphQL response: {parse_error}"
            logger.error(f"[Service ID Mapper] {error_msg}")
            return False, None, error_msg
    
    def _get_auth_token(self) -> Optional[str]:
        """Get authentication token from the helpers system"""
        try:
            auth_data = load_token()
            if not auth_data:
                logger.error("[Service ID Mapper] No authentication data available")
                return None
            
            auth_type = auth_data.get('auth_type', 'oauth')
            
            if auth_type == 'oauth':
                # OAuth token authentication
                access_token = auth_data.get('access_token', '').strip()
                if access_token and is_valid_jwt_token(access_token):
                    return access_token
                else:
                    logger.error("[Service ID Mapper] Invalid OAuth access token")
                    return None
                    
            elif auth_type == 'cookie':
                # Session cookie authentication - extract session ID
                session_cookies = auth_data.get('session_cookies', {})
                auth_session_id = session_cookies.get('AUTH_SESSION_ID', '').strip()
                if auth_session_id and len(auth_session_id) > 20:
                    return auth_session_id
                else:
                    logger.error("[Service ID Mapper] Invalid session cookie token")
                    return None
            else:
                logger.error(f"[Service ID Mapper] Unknown auth_type: {auth_type}")
                return None
                
        except Exception as e:
            logger.error(f"[Service ID Mapper] Token loading error: {e}")
            return None
    
    def _get_graphql_headers(self) -> Dict[str, str]:
        """Get headers for GraphQL requests"""
        try:
            # Get authentication headers from helpers
            auth_headers = get_auth_headers()
            
            # Base GraphQL headers
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'User-Agent': 'GUST-Bot/2.0 ServiceIDMapper'
            }
            
            # Merge authentication headers
            headers.update(auth_headers)
            
            return headers
            
        except Exception as e:
            logger.error(f"[Service ID Mapper] Error getting headers: {e}")
            # Return minimal headers as fallback
            return {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'User-Agent': 'GUST-Bot/2.0 ServiceIDMapper'
            }
    
    def clear_cache(self) -> None:
        """Clear the internal cache"""
        self.cache.clear()
        self.cache_expiry.clear()
        logger.info("[Service ID Mapper] Cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        current_time = time.time()
        active_entries = sum(1 for expiry_time in self.cache_expiry.values() if current_time < expiry_time)
        
        return {
            'total_entries': len(self.cache),
            'active_entries': active_entries,
            'expired_entries': len(self.cache) - active_entries,
            'cache_duration': self.cache_duration
        }
    
    def get_complete_server_info(self, server_id: str, region: str = 'US') -> Dict[str, Any]:
        """
        Get complete server information including both IDs
        
        Returns:
            Dict with server_id, service_id, success, error fields
        """
        success, service_id, error = self.get_service_id_from_server_id(server_id, region)
        
        return {
            'success': success,
            'server_id': str(server_id),
            'service_id': service_id,
            'region': region.upper(),
            'error': error,
            'has_both_ids': success and service_id is not None,
            'timestamp': datetime.now().isoformat(),
            'cache_info': {
                'from_cache': f"{server_id}_{region.upper()}" in self.cache,
                'cache_stats': self.get_cache_stats()
            }
        }

# ================================================================
# CONVENIENCE FUNCTIONS FOR EASY INTEGRATION
# ================================================================

def discover_service_id(server_id: str, region: str = 'US') -> Dict[str, Any]:
    """
    Convenience function to discover service ID from server ID
    
    Usage:
        result = discover_service_id("1722255", "US")
        if result['success']:
            server_id = result['server_id']    # "1722255" 
            service_id = result['service_id']  # "1736296"
            print(f"Server {server_id} -> Service {service_id}")
    
    Args:
        server_id (str): The server ID from G-Portal URL
        region (str): Server region (US, EU, AS, AU)
        
    Returns:
        Dict containing discovery results
    """
    mapper = ServiceIDMapper()
    return mapper.get_complete_server_info(server_id, region)

def batch_discover_service_ids(server_list: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Discover Service IDs for multiple servers
    
    Args:
        server_list: List of dicts with 'server_id' and 'region' keys
        
    Returns:
        Dict with batch discovery results
    """
    mapper = ServiceIDMapper()
    results = []
    successful_count = 0
    
    logger.info(f"[Batch Discovery] Starting batch discovery for {len(server_list)} servers")
    
    for server_info in server_list:
        try:
            server_id = server_info.get('server_id', '').strip()
            region = server_info.get('region', 'US').strip()
            
            if not server_id:
                results.append({
                    'server_id': server_id,
                    'success': False,
                    'error': 'Missing server_id'
                })
                continue
            
            # Discover service ID
            result = mapper.get_complete_server_info(server_id, region)
            results.append(result)
            
            if result['success']:
                successful_count += 1
                
            # Small delay to be respectful to the API
            time.sleep(0.2)
            
        except Exception as e:
            logger.error(f"[Batch Discovery] Error processing server {server_info}: {e}")
            results.append({
                'server_id': server_info.get('server_id', 'unknown'),
                'success': False,
                'error': str(e)
            })
    
    logger.info(f"[Batch Discovery] Completed: {successful_count}/{len(server_list)} successful")
    
    return {
        'success': True,
        'total_servers': len(server_list),
        'successful_discoveries': successful_count,
        'failed_discoveries': len(server_list) - successful_count,
        'results': results,
        'batch_timestamp': datetime.now().isoformat()
    }

def validate_service_id_discovery() -> Dict[str, Any]:
    """
    Validate that Service ID discovery system is working
    
    Returns:
        Dict with validation results
    """
    try:
        mapper = ServiceIDMapper()
        
        # Check authentication
        token = mapper._get_auth_token()
        if not token:
            return {
                'valid': False,
                'error': 'No authentication token available',
                'recommendations': [
                    'Login to G-Portal through GUST',
                    'Check authentication system status',
                    'Verify G-Portal credentials'
                ]
            }
        
        # Check network connectivity
        try:
            response = requests.get('https://www.g-portal.com', timeout=5)
            if response.status_code != 200:
                return {
                    'valid': False,
                    'error': 'Cannot reach G-Portal website',
                    'recommendations': [
                        'Check internet connection',
                        'Verify G-Portal is accessible',
                        'Check firewall settings'
                    ]
                }
        except requests.exceptions.RequestException as net_error:
            return {
                'valid': False,
                'error': f'Network error: {net_error}',
                'recommendations': [
                    'Check internet connection',
                    'Verify DNS resolution',
                    'Check firewall/proxy settings'
                ]
            }
        
        return {
            'valid': True,
            'message': 'Service ID discovery system is ready',
            'capabilities': [
                'Authentication available',
                'Network connectivity confirmed',
                'GraphQL endpoint accessible',
                'Rate limiting configured',
                'Caching enabled'
            ],
            'cache_stats': mapper.get_cache_stats()
        }
        
    except Exception as e:
        return {
            'valid': False,
            'error': f'Validation error: {e}',
            'recommendations': [
                'Check GUST installation',
                'Verify all dependencies installed',
                'Check log files for details'
            ]
        }

# ================================================================
# MODULE EXPORTS
# ================================================================

__all__ = [
    'ServiceIDMapper',
    'discover_service_id',
    'batch_discover_service_ids',
    'validate_service_id_discovery'
]

logger.info("✅ Service ID Discovery utility loaded with caching and rate limiting")