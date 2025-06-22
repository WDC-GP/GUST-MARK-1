"""
Fixed GraphQL Service ID Discovery - Better Response Handling
============================================================

Since HTML scraping is hitting 404 errors, let's fix the GraphQL approach
with better response handling and authentication.

Replace your utils/service_id_discovery.py with this version.
"""

import requests
import json
import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
import time

# Import existing GUST utilities
from utils.helpers import load_token, get_auth_headers
from utils.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)

class ServiceIDMapper:
    """
    FIXED: Maps Server IDs to Service IDs using G-Portal's GraphQL API with better error handling
    """
    
    def __init__(self):
        self.rate_limiter = RateLimiter(max_calls=10, time_window=60)
        self.graphql_endpoint = "https://www.g-portal.com/ngpapi"
        self.cache = {}
        self.cache_expiry = {}
        self.cache_duration = 3600
        logger.info("[Service ID Mapper] Initialized with improved GraphQL handling")
        
    def get_service_id_from_server_id(self, server_id: str, region: str = 'US') -> Tuple[bool, Optional[str], Optional[str]]:
        """
        FIXED: Get Service ID using improved GraphQL with better response handling
        """
        try:
            server_id_str = str(server_id).strip()
            region = region.upper().strip()
            cache_key = f"{server_id_str}_{region}"
            
            # Check cache
            if cache_key in self.cache and cache_key in self.cache_expiry:
                if time.time() < self.cache_expiry[cache_key]:
                    logger.info(f"[Service ID Mapper] Using cached service ID for server {server_id_str}")
                    return True, self.cache[cache_key], None
                else:
                    del self.cache[cache_key]
                    del self.cache_expiry[cache_key]
                    
            logger.info(f"[Service ID Mapper] GraphQL lookup for server {server_id_str} in region {region}")
            
            # Rate limiting
            self.rate_limiter.wait_if_needed("service_mapper")
            
            # Get authentication
            token = self._get_auth_token()
            if not token:
                return False, None, "No authentication token available"
            
            # Validate inputs
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
                            return True, service_id, None
                    
                    logger.debug(f"[Service ID Mapper] {query_name} didn't return service ID")
                    
                except Exception as query_error:
                    logger.debug(f"[Service ID Mapper] {query_name} failed: {query_error}")
                    continue
            
            # If all queries failed
            return False, None, f"Server {server_id_str} not found or endpoint not available"
            
        except Exception as e:
            logger.error(f"[Service ID Mapper] Discovery error: {e}")
            return False, None, f"Service ID discovery error: {e}"
    
    def _get_auth_token(self) -> Optional[str]:
        """Get authentication token from GUST system"""
        try:
            token_data = load_token()
            if not token_data:
                return None
            
            if isinstance(token_data, dict):
                token = token_data.get('access_token')
                if token and len(token) > 20:
                    return token
            elif isinstance(token_data, str) and len(token_data) > 20:
                return token_data
            
            return None
        except Exception as e:
            logger.error(f"[Service ID Mapper] Token extraction error: {e}")
            return None
    
    def _make_safe_graphql_request(self, query: str, variables: Dict, token: str) -> Dict[str, Any]:
        """Make a safe GraphQL request with comprehensive error handling"""
        try:
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'User-Agent': 'GUST-Bot/2.0',
                'Origin': 'https://www.g-portal.com',
                'Referer': 'https://www.g-portal.com/'
            }
            
            payload = {
                'query': query,
                'variables': variables
            }
            
            logger.debug(f"[Service ID Mapper] Making GraphQL request...")
            
            response = requests.post(
                self.graphql_endpoint,
                json=payload,
                headers=headers,
                timeout=15
            )
            
            # Check HTTP status
            if response.status_code != 200:
                return {
                    'success': False,
                    'data': None,
                    'error': f"HTTP {response.status_code}: {response.text[:200]}"
                }
            
            # Parse JSON
            try:
                data = response.json()
            except json.JSONDecodeError:
                return {
                    'success': False,
                    'data': None,
                    'error': 'Invalid JSON response from GraphQL'
                }
            
            # Check if response is None or empty
            if data is None:
                return {
                    'success': False,
                    'data': None,
                    'error': 'GraphQL response is None'
                }
            
            # Check for GraphQL errors
            if isinstance(data, dict) and 'errors' in data and data['errors']:
                error_messages = []
                for error in data['errors']:
                    if isinstance(error, dict):
                        error_messages.append(error.get('message', 'Unknown GraphQL error'))
                    else:
                        error_messages.append(str(error))
                
                return {
                    'success': False,
                    'data': data.get('data'),
                    'error': f"GraphQL errors: {'; '.join(error_messages)}"
                }
            
            # Return successful response
            return {
                'success': True,
                'data': data.get('data') if isinstance(data, dict) else data,
                'error': None
            }
            
        except requests.exceptions.Timeout:
            return {'success': False, 'data': None, 'error': 'Request timeout'}
        except requests.exceptions.ConnectionError:
            return {'success': False, 'data': None, 'error': 'Connection error'}
        except Exception as e:
            return {'success': False, 'data': None, 'error': f'Request failed: {str(e)}'}
    
    def _create_cfgcontext_query(self) -> Tuple[str, str, Dict]:
        """Create cfgContext query (most likely to work)"""
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
                    service {
                        config {
                            hwId
                            type
                            ipAddress
                        }
                    }
                }
            }
        }
        """
        return ("cfgContext", query, {})
    
    def _create_services_query(self) -> Tuple[str, str, Dict]:
        """Create services query (alternative approach)"""
        query = """
        query GetServices {
            services {
                id
                name
                status
                gameserver {
                    id
                    serviceId
                }
            }
        }
        """
        return ("services", query, {})
    
    def _create_gameserver_query(self) -> Tuple[str, str, Dict]:
        """Create direct gameserver query (fallback)"""
        query = """
        query GetGameServer($serverId: Int!) {
            gameserver(id: $serverId) {
                id
                serviceId
                name
                status
            }
        }
        """
        return ("gameserver", query, {})
    
    def _extract_service_id_from_response(self, data: Any, query_name: str) -> Optional[str]:
        """Extract service ID from different response structures"""
        try:
            if not data or not isinstance(data, dict):
                return None
            
            if query_name == "cfgContext":
                # Extract from cfgContext response
                cfg_context = data.get('cfgContext')
                if cfg_context and isinstance(cfg_context, dict):
                    ns = cfg_context.get('ns', {})
                    if isinstance(ns, dict):
                        sys_data = ns.get('sys', {})
                        if isinstance(sys_data, dict):
                            game_server = sys_data.get('gameServer', {})
                            if isinstance(game_server, dict):
                                service_id = game_server.get('serviceId')
                                if service_id:
                                    return str(service_id).strip()
            
            elif query_name == "services":
                # Extract from services response
                services = data.get('services', [])
                if isinstance(services, list):
                    for service in services:
                        if isinstance(service, dict):
                            gameserver = service.get('gameserver', {})
                            if isinstance(gameserver, dict):
                                service_id = gameserver.get('serviceId')
                                if service_id:
                                    return str(service_id).strip()
            
            elif query_name == "gameserver":
                # Extract from gameserver response
                gameserver = data.get('gameserver', {})
                if isinstance(gameserver, dict):
                    service_id = gameserver.get('serviceId')
                    if service_id:
                        return str(service_id).strip()
            
            return None
            
        except Exception as e:
            logger.error(f"[Service ID Mapper] Response extraction error: {e}")
            return None
    
    def get_complete_server_info(self, server_id: str, region: str = 'US') -> Dict[str, Any]:
        """Get complete server information including Service ID discovery"""
        try:
            success, service_id, error = self.get_service_id_from_server_id(server_id, region)
            
            return {
                'success': success,
                'server_id': str(server_id),
                'service_id': service_id,
                'region': region.upper(),
                'error': error,
                'discovery_method': 'GraphQL (Fixed)',
                'discovery_timestamp': datetime.now().isoformat(),
                'cache_stats': self.get_cache_stats()
            }
            
        except Exception as e:
            return {
                'success': False,
                'server_id': str(server_id),
                'service_id': None,
                'region': region.upper(),
                'error': f"Discovery error: {e}",
                'discovery_method': 'GraphQL (Fixed)',
                'discovery_timestamp': datetime.now().isoformat()
            }
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        current_time = time.time()
        valid_entries = sum(1 for key, expiry in self.cache_expiry.items() if expiry > current_time)
        
        return {
            'total_entries': len(self.cache),
            'valid_entries': valid_entries,
            'expired_entries': len(self.cache) - valid_entries,
            'cache_duration': self.cache_duration
        }

    def clear_cache(self):
        """Clear cache"""
        self.cache.clear()
        self.cache_expiry.clear()
        logger.info("[Service ID Mapper] Cache cleared")


def discover_service_id(server_id: str, region: str = 'US') -> Dict[str, Any]:
    """Main discovery function using fixed GraphQL approach"""
    mapper = ServiceIDMapper()
    return mapper.get_complete_server_info(server_id, region)


def validate_service_id_discovery() -> Dict[str, Any]:
    """Validate the fixed GraphQL Service ID discovery system"""
    try:
        mapper = ServiceIDMapper()
        token = mapper._get_auth_token()
        
        if not token:
            return {
                'valid': False,
                'error': 'No authentication token available',
                'recommendations': [
                    'Check GUST authentication system',
                    'Verify G-Portal login is working',
                    'Check token storage and loading'
                ]
            }
        
        # Test GraphQL endpoint connectivity
        try:
            test_result = mapper._make_safe_graphql_request(
                "query { __typename }",
                {},
                token
            )
            endpoint_accessible = test_result['success']
        except Exception:
            endpoint_accessible = False
        
        if not endpoint_accessible:
            return {
                'valid': False,
                'error': 'GraphQL endpoint not accessible',
                'recommendations': [
                    'Check network connectivity to G-Portal',
                    'Verify GraphQL endpoint is online',
                    'Check authentication token validity'
                ]
            }
        
        return {
            'valid': True,
            'message': 'Fixed GraphQL Service ID discovery system validated',
            'capabilities': [
                'Authentication available',
                'Enhanced headers configured', 
                'Network connectivity confirmed',
                'GraphQL endpoint accessible',
                'Multiple query strategies',
                'Improved response handling',
                'Rate limiting configured',
                'Caching enabled with expiry'
            ],
            'method': 'GraphQL (Fixed Response Handling)'
        }
        
    except Exception as e:
        return {
            'valid': False,
            'error': f'Validation error: {e}',
            'recommendations': [
                'Check all dependencies are available',
                'Verify GUST system status',
                'Check logs for detailed error information'
            ]
        }


# For testing
if __name__ == "__main__":
    result = discover_service_id("1722255", "US")
    print(f"Fixed GraphQL Discovery test: {json.dumps(result, indent=2)}")
