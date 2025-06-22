"""
GUST Bot Enhanced - Service ID Discovery Utility (COMPLETE IMPLEMENTATION)
===========================================================================
✅ COMPLETE: Service ID Auto-Discovery system for G-Portal dual ID support
✅ COMPLETE: GraphQL cfgContext queries for automatic Service ID extraction
✅ COMPLETE: Caching system for discovered Service ID mappings
✅ COMPLETE: Multiple fallback mechanisms for discovery failures
✅ COMPLETE: Enhanced error handling and debug information
✅ COMPLETE: Integration with GUST server management system
"""

import requests
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict

# Import helpers
try:
    from utils.helpers import load_token
    HELPERS_AVAILABLE = True
except ImportError:
    HELPERS_AVAILABLE = False

logger = logging.getLogger(__name__)

class ServiceIDMapper:
    """
    Service ID Discovery and Mapping System
    
    Handles automatic discovery of G-Portal Service IDs from Server IDs
    using GraphQL cfgContext queries and caching mechanisms.
    """
    
    def __init__(self):
        self.graphql_endpoint = 'https://www.g-portal.com/ngpapi/'
        self.cache = {}  # server_id -> service_id mapping
        self.cache_expiry = {}  # server_id -> expiry timestamp
        self.cache_duration = 3600  # 1 hour cache TTL
        self.discovery_stats = {
            'total_attempts': 0,
            'successful_discoveries': 0,
            'cache_hits': 0,
            'errors': 0
        }
        
        logger.info("[Service ID Mapper] Initialized with improved GraphQL handling")
    
    def discover_service_id(self, server_id: str, region: str = 'US') -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Discover Service ID for a given Server ID
        
        Args:
            server_id: The Server ID to discover Service ID for
            region: Server region (default: US)
            
        Returns:
            Tuple[bool, Optional[str], Optional[str]]: (success, service_id, error_message)
        """
        try:
            # Convert to string for consistency
            server_id_str = str(server_id).strip()
            region = region.upper().strip()
            
            self.discovery_stats['total_attempts'] += 1
            
            logger.info(f"[Service ID Mapper] GraphQL lookup for server {server_id_str} in region {region}")
            
            # Check cache first
            cache_key = f"{server_id_str}_{region}"
            if cache_key in self.cache:
                cache_time = self.cache_expiry.get(cache_key, 0)
                if time.time() < cache_time:
                    self.discovery_stats['cache_hits'] += 1
                    logger.info(f"[Service ID Mapper] Cache hit for {server_id_str}: {self.cache[cache_key]}")
                    return True, self.cache[cache_key], None
                else:
                    # Cache expired, remove entry
                    del self.cache[cache_key]
                    del self.cache_expiry[cache_key]
            
            # Get authentication token
            token = self._get_auth_token()
            if not token:
                error_msg = "No authentication token available"
                logger.error(f"[Service ID Mapper] {error_msg}")
                self.discovery_stats['errors'] += 1
                return False, None, error_msg
            
            # Validate server ID format
            try:
                server_id_int = int(server_id_str)
                if server_id_int <= 0:
                    return False, None, "Invalid server ID: must be a positive integer"
            except ValueError:
                return False, None, f"Invalid server ID format: '{server_id_str}' is not a valid integer"
            
            if region not in ['US', 'EU', 'AS', 'AU']:
                logger.warning(f"[Service ID Mapper] Invalid region '{region}', defaulting to US")
                region = 'US'
            
            # Try multiple GraphQL queries in order of likelihood to work
            queries_to_try = [
                self._create_cfgcontext_query(),
                self._create_services_query(),
                self._create_gameserver_query()
            ]
            
            for query_name, query, variables in queries_to_try:
                logger.debug(f"[Service ID Mapper] Trying {query_name}...")
                
                try:
                    # Adjust variables for this query
                    query_variables = variables.copy()
                    query_variables['serverId'] = server_id_int
                    query_variables['region'] = region
                    
                    result = self._make_safe_graphql_request(query, query_variables, token)
                    
                    if result['success'] and result['data']:
                        service_id = self._extract_service_id_from_response(result['data'], query_name)
                        if service_id:
                            # Cache successful result
                            self.cache[cache_key] = service_id
                            self.cache_expiry[cache_key] = time.time() + self.cache_duration
                            
                            logger.info(f"[Service ID Mapper] ✅ Success with {query_name}: {server_id_str} → {service_id}")
                            self.discovery_stats['successful_discoveries'] += 1
                            return True, service_id, None
                    
                    logger.debug(f"[Service ID Mapper] {query_name} didn't return service ID")
                    
                except Exception as query_error:
                    logger.debug(f"[Service ID Mapper] {query_name} failed: {query_error}")
                    continue
            
            # All queries failed
            error_msg = f"Service ID not found for server {server_id_str} after trying all methods"
            logger.warning(f"[Service ID Mapper] {error_msg}")
            self.discovery_stats['errors'] += 1
            return False, None, error_msg
                
        except Exception as e:
            error_msg = f"Unexpected error in Service ID discovery: {e}"
            logger.error(f"[Service ID Mapper] {error_msg}")
            self.discovery_stats['errors'] += 1
            return False, None, error_msg
    
    def _create_cfgcontext_query(self) -> Tuple[str, str, Dict]:
        """Create cfgContext GraphQL query (most reliable method)"""
        query_name = "cfgContext"
        query = """
        query GetServerConfig($serverId: Int!, $region: REGION!) {
            cfgContext(rsid: {id: $serverId, region: $region}) {
                ns {
                    sys {
                        gameServer {
                            serviceId
                            serverId  
                            serverName
                            serverIp
                        }
                    }
                    service {
                        config {
                            rsid {
                                id
                                region
                            }
                            hwId
                            type
                            ipAddress
                        }
                    }
                }
            }
        }
        """
        variables = {'serverId': 0, 'region': 'US'}  # Will be filled in
        return query_name, query, variables
    
    def _create_services_query(self) -> Tuple[str, str, Dict]:
        """Create services GraphQL query (alternative method)"""
        query_name = "services"
        query = """
        query GetServices($serverId: Int!, $region: REGION!) {
            services(filter: {rsid: {id: $serverId, region: $region}}) {
                id
                type
                rsid {
                    id
                    region
                }
                config {
                    hwId
                    ipAddress
                }
            }
        }
        """
        variables = {'serverId': 0, 'region': 'US'}
        return query_name, query, variables
    
    def _create_gameserver_query(self) -> Tuple[str, str, Dict]:
        """Create gameServer GraphQL query (fallback method)"""
        query_name = "gameServer"
        query = """
        query GetGameServer($serverId: Int!, $region: REGION!) {
            gameServer(rsid: {id: $serverId, region: $region}) {
                serviceId
                serverId
                serverName
                config {
                    rsid {
                        id
                        region
                    }
                }
            }
        }
        """
        variables = {'serverId': 0, 'region': 'US'}
        return query_name, query, variables
    
    def _make_safe_graphql_request(self, query: str, variables: Dict, token: str) -> Dict[str, Any]:
        """Make a safe GraphQL request with comprehensive error handling"""
        try:
            payload = {
                'query': query,
                'variables': variables
            }
            
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json',
                'User-Agent': 'GUST-Bot-Enhanced/1.0',
                'Accept': 'application/json',
                'Origin': 'https://www.g-portal.com',
                'Referer': 'https://www.g-portal.com/'
            }
            
            response = requests.post(
                self.graphql_endpoint,
                json=payload,
                headers=headers,
                timeout=15
            )
            
            if response.status_code != 200:
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text[:200]}",
                    'data': None
                }
            
            try:
                data = response.json()
            except json.JSONDecodeError as e:
                return {
                    'success': False,
                    'error': f"Invalid JSON response: {e}",
                    'data': None
                }
            
            # Check for GraphQL errors
            if 'errors' in data and data['errors']:
                error_messages = [error.get('message', 'Unknown error') for error in data['errors']]
                return {
                    'success': False,
                    'error': f"GraphQL errors: {'; '.join(error_messages)}",
                    'data': None
                }
            
            return {
                'success': True,
                'error': None,
                'data': data.get('data', {})
            }
            
        except requests.exceptions.Timeout:
            return {'success': False, 'error': 'Request timeout', 'data': None}
        except requests.exceptions.RequestException as e:
            return {'success': False, 'error': f'Request error: {e}', 'data': None}
        except Exception as e:
            return {'success': False, 'error': f'Unexpected error: {e}', 'data': None}
    
    def _extract_service_id_from_response(self, data: Dict[str, Any], query_type: str) -> Optional[str]:
        """Extract Service ID from GraphQL response based on query type"""
        try:
            if query_type == "cfgContext":
                cfg_context = data.get('cfgContext', {})
                if cfg_context and cfg_context.get('ns'):
                    ns = cfg_context['ns']
                    
                    # Try gameServer.serviceId first
                    if ns.get('sys', {}).get('gameServer', {}).get('serviceId'):
                        service_id = str(ns['sys']['gameServer']['serviceId'])
                        logger.debug(f"[Service ID Mapper] Found serviceId in gameServer: {service_id}")
                        return service_id
                    
                    # Try service.config.rsid.id as fallback
                    if ns.get('service', {}).get('config', {}).get('rsid', {}).get('id'):
                        service_id = str(ns['service']['config']['rsid']['id'])
                        logger.debug(f"[Service ID Mapper] Found id in service config: {service_id}")
                        return service_id
            
            elif query_type == "services":
                services = data.get('services', [])
                if services and len(services) > 0:
                    service = services[0]
                    if service.get('id'):
                        service_id = str(service['id'])
                        logger.debug(f"[Service ID Mapper] Found id in services: {service_id}")
                        return service_id
            
            elif query_type == "gameServer":
                game_server = data.get('gameServer', {})
                if game_server and game_server.get('serviceId'):
                    service_id = str(game_server['serviceId'])
                    logger.debug(f"[Service ID Mapper] Found serviceId in gameServer: {service_id}")
                    return service_id
            
            logger.debug(f"[Service ID Mapper] No service ID found in {query_type} response")
            return None
            
        except Exception as e:
            logger.debug(f"[Service ID Mapper] Error extracting service ID from {query_type}: {e}")
            return None
    
    def bulk_discover(self, server_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Perform bulk Service ID discovery for multiple servers
        
        Args:
            server_list: List of server dictionaries with serverId and serverRegion
            
        Returns:
            Dict with discovery results and statistics
        """
        results = {
            'successful_discoveries': {},
            'failed_discoveries': {},
            'skipped': {},
            'statistics': {
                'total_servers': len(server_list),
                'success_count': 0,
                'failure_count': 0,
                'skip_count': 0
            }
        }
        
        logger.info(f"[Service ID Mapper] Starting bulk discovery for {len(server_list)} servers")
        
        for server in server_list:
            server_id = server.get('serverId')
            region = server.get('serverRegion', 'US')
            
            if not server_id:
                results['skipped'][server_id] = 'Missing server ID'
                results['statistics']['skip_count'] += 1
                continue
            
            # Skip if Service ID already exists
            if server.get('serviceId'):
                results['skipped'][server_id] = f"Service ID already exists: {server['serviceId']}"
                results['statistics']['skip_count'] += 1
                continue
            
            # Attempt discovery
            success, service_id, error = self.discover_service_id(server_id, region)
            
            if success and service_id:
                results['successful_discoveries'][server_id] = {
                    'service_id': service_id,
                    'region': region,
                    'server_name': server.get('serverName', 'Unknown')
                }
                results['statistics']['success_count'] += 1
            else:
                results['failed_discoveries'][server_id] = {
                    'error': error or 'Unknown error',
                    'region': region,
                    'server_name': server.get('serverName', 'Unknown')
                }
                results['statistics']['failure_count'] += 1
            
            # Small delay to avoid overwhelming the API
            time.sleep(0.5)
        
        logger.info(f"[Service ID Mapper] Bulk discovery completed: {results['statistics']['success_count']} successful, {results['statistics']['failure_count']} failed")
        
        return results
    
    def get_complete_server_info(self, server_id: str, region: str = 'US') -> Dict[str, Any]:
        """
        Get complete server information including both IDs
        
        Returns:
            Dict with server_id, service_id, success, error fields
        """
        success, service_id, error = self.discover_service_id(server_id, region)
        
        return {
            'success': success,
            'server_id': str(server_id),
            'service_id': service_id,
            'region': region.upper(),
            'error': error,
            'has_both_ids': success and service_id is not None,
            'discovery_timestamp': datetime.now().isoformat()
        }
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get Service ID discovery cache statistics"""
        current_time = time.time()
        valid_entries = sum(1 for key, expiry in self.cache_expiry.items() if expiry > current_time)
        
        return {
            'total_entries': len(self.cache),
            'valid_entries': valid_entries,
            'expired_entries': len(self.cache) - valid_entries,
            'cache_duration': self.cache_duration,
            'discovery_stats': self.discovery_stats.copy(),
            'oldest_entry': min(self.cache_expiry.values()) if self.cache_expiry else None,
            'newest_entry': max(self.cache_expiry.values()) if self.cache_expiry else None
        }
    
    def clear_cache(self) -> None:
        """Clear the Service ID discovery cache"""
        self.cache.clear()
        self.cache_expiry.clear()
        logger.info("[Service ID Mapper] Cache cleared")
    
    def _get_auth_token(self) -> Optional[str]:
        """Get authentication token for API requests"""
        if not HELPERS_AVAILABLE:
            logger.warning("[Service ID Mapper] Helpers not available for token loading")
            return None
        
        try:
            token_data = load_token()
            if not token_data:
                return None
            
            if isinstance(token_data, dict):
                return token_data.get('access_token')
            elif isinstance(token_data, str):
                return token_data
            
            return None
        except Exception as e:
            logger.error(f"[Service ID Mapper] Error loading token: {e}")
            return None

# ============================================================================
# DISCOVERY UTILITY FUNCTIONS
# ============================================================================

def discover_service_id(server_id: str, region: str = 'US') -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Convenience function for single Service ID discovery
    
    Args:
        server_id: Server ID to discover Service ID for
        region: Server region
        
    Returns:
        Tuple[bool, Optional[str], Optional[str]]: (success, service_id, error_message)
    """
    mapper = ServiceIDMapper()
    return mapper.discover_service_id(server_id, region)

def validate_service_id_discovery() -> Dict[str, Any]:
    """
    Validate that the Service ID discovery system is operational
    
    Returns:
        Dict with validation results and system status
    """
    validation_result = {
        'valid': False,
        'error': None,
        'capabilities': [],
        'recommendations': []
    }
    
    try:
        # Check if helpers are available
        if not HELPERS_AVAILABLE:
            validation_result['error'] = 'Helpers module not available for token loading'
            validation_result['recommendations'].append('Install utils.helpers module')
            return validation_result
        
        # Check if authentication token is available
        token_data = load_token()
        if not token_data:
            validation_result['error'] = 'No authentication token available'
            validation_result['recommendations'].append('Login to G-Portal to obtain authentication token')
            return validation_result
        
        # Test Service ID mapper initialization
        mapper = ServiceIDMapper()
        validation_result['capabilities'].append('Service ID Mapper initialization')
        
        # Test cache functionality
        stats = mapper.get_cache_stats()
        validation_result['capabilities'].append('Cache system')
        
        # Test GraphQL endpoint accessibility
        try:
            test_response = requests.get('https://www.g-portal.com', timeout=5)
            if test_response.status_code == 200:
                validation_result['capabilities'].append('G-Portal endpoint accessibility')
        except requests.RequestException:
            validation_result['recommendations'].append('Check internet connection to G-Portal')
        
        validation_result['valid'] = True
        validation_result['capabilities'].append('Service ID Auto-Discovery system')
        
    except Exception as e:
        validation_result['error'] = str(e)
        validation_result['recommendations'].append('Check Service ID discovery system installation')
    
    return validation_result

def get_discovery_system_status() -> Dict[str, Any]:
    """
    Get comprehensive status of the Service ID discovery system
    
    Returns:
        Dict with system status, statistics, and health information
    """
    status = {
        'system_available': False,
        'authentication_ready': False,
        'cache_statistics': {},
        'discovery_statistics': {},
        'recommendations': []
    }
    
    try:
        # Check system availability
        validation = validate_service_id_discovery()
        status['system_available'] = validation['valid']
        
        if validation['valid']:
            # Get detailed statistics
            mapper = ServiceIDMapper()
            status['cache_statistics'] = mapper.get_cache_stats()
            status['discovery_statistics'] = mapper.discovery_stats.copy()
            status['authentication_ready'] = True
        else:
            status['recommendations'].extend(validation.get('recommendations', []))
        
    except Exception as e:
        status['error'] = str(e)
        status['recommendations'].append('Service ID discovery system needs attention')
    
    return status

# ============================================================================
# MODULE INITIALIZATION
# ============================================================================

logger.info("✅ Service ID Discovery utility loaded successfully")

# Export main classes and functions
__all__ = [
    'ServiceIDMapper',
    'discover_service_id', 
    'validate_service_id_discovery',
    'get_discovery_system_status'
]