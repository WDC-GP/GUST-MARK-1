"""
GraphQL ServiceSensors Client for WDC-GP/GUST-MARK-1 (FIXED VERSION)
===================================================================
✅ FIXED: Server ID format (string, not integer)
✅ FIXED: Memory conversion (G-Portal returns MB, not bytes)
✅ FIXED: Enhanced error logging and debugging
✅ FIXED: Better authentication handling
✅ FIXED: Improved GraphQL response parsing
"""

import requests
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

# Import existing utilities
from utils.helpers import load_token
from utils.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)

class GPortalSensorsClient:
    """Fixed client for fetching real sensor data from G-Portal GraphQL ServiceSensors"""
    
    def __init__(self):
        self.rate_limiter = RateLimiter()
        self.graphql_endpoint = "https://www.g-portal.com/ngpapi"
        logger.info("[GraphQL Sensors] Fixed client initialized")
        
    def get_service_sensors(self, server_id: str, region: str = 'US') -> Dict[str, Any]:
        """
        ✅ FIXED: Fetch real CPU, memory, and uptime data from G-Portal ServiceSensors
        """
        try:
            # ✅ FIX 1: Ensure server_id is string format
            server_id_str = str(server_id).strip()
            logger.info(f"[GraphQL Sensors] Fetching ServiceSensors for server {server_id_str}")
            
            # Rate limiting using existing system
            self.rate_limiter.wait_if_needed("sensors")
            
            # Get authentication token using existing helper
            token = self._get_auth_token()
            if not token:
                logger.error("[GraphQL Sensors] No authentication token available")
                return {
                    'success': False, 
                    'error': 'No authentication token available',
                    'data': None
                }
            
            # ✅ FIX 2: Enhanced ServiceSensors GraphQL query with better field handling
            query = """
            query GetServiceSensors($serviceId: String!) {
                serviceSensors(serviceId: $serviceId) {
                    cpu
                    cpuTotal
                    memory {
                        percent
                        used
                        total
                    }
                    uptime
                    timestamp
                }
            }
            """
            
            # Request payload
            payload = {
                'query': query,
                'variables': {
                    'serviceId': server_id_str  # ✅ FIX: Use string format
                }
            }
            
            # ✅ FIX 3: Enhanced headers for better compatibility
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json',
                'User-Agent': 'GUST-Bot-Enhanced/1.0',
                'Accept': 'application/json',
                'Origin': 'https://www.g-portal.com',
                'Referer': 'https://www.g-portal.com/'
            }
            
            logger.debug(f"[GraphQL Sensors] Making request to {self.graphql_endpoint}")
            logger.debug(f"[GraphQL Sensors] Server ID: {server_id_str}")
            logger.debug(f"[GraphQL Sensors] Token preview: {token[:20]}..." if len(token) > 20 else "Token too short")
            
            # Make GraphQL request
            response = requests.post(
                self.graphql_endpoint,
                json=payload,
                headers=headers,
                timeout=15  # ✅ FIX: Increased timeout
            )
            
            logger.debug(f"[GraphQL Sensors] Response status: {response.status_code}")
            logger.debug(f"[GraphQL Sensors] Response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    logger.debug(f"[GraphQL Sensors] Raw response: {json.dumps(data, indent=2)}")
                    return self._parse_sensors_response(data, server_id_str)
                except json.JSONDecodeError as json_error:
                    logger.error(f"[GraphQL Sensors] JSON decode error: {json_error}")
                    logger.error(f"[GraphQL Sensors] Response text: {response.text[:500]}...")
                    return {
                        'success': False, 
                        'error': f'JSON decode error: {json_error}',
                        'data': None
                    }
            else:
                error_msg = f'HTTP {response.status_code}'
                try:
                    error_details = response.json()
                    if 'errors' in error_details:
                        error_msg += f": {error_details['errors']}"
                    logger.error(f"[GraphQL Sensors] API Error: {error_msg}")
                    logger.error(f"[GraphQL Sensors] Response: {error_details}")
                except:
                    logger.error(f"[GraphQL Sensors] HTTP Error: {error_msg}")
                    logger.error(f"[GraphQL Sensors] Response text: {response.text[:500]}...")
                
                return {
                    'success': False, 
                    'error': error_msg,
                    'data': None
                }
                
        except requests.RequestException as req_error:
            logger.error(f"[GraphQL Sensors] Request error: {req_error}")
            return {
                'success': False, 
                'error': f'Request error: {req_error}',
                'data': None
            }
        except Exception as e:
            logger.error(f"[GraphQL Sensors] Unexpected error: {e}")
            return {
                'success': False, 
                'error': str(e),
                'data': None
            }
    
    def _get_auth_token(self) -> Optional[str]:
        """✅ FIXED: Enhanced authentication token retrieval"""
        try:
            logger.debug("[GraphQL Sensors] Loading authentication token...")
            token_data = load_token()
            
            if not token_data:
                logger.warning("[GraphQL Sensors] No token data returned from load_token()")
                return None
                
            # Handle different token formats
            token = None
            if isinstance(token_data, dict):
                token = token_data.get('access_token')
                if not token:
                    # Try alternative field names
                    token = token_data.get('token') or token_data.get('authToken')
                logger.debug(f"[GraphQL Sensors] Extracted token from dict, length: {len(token) if token else 0}")
            elif isinstance(token_data, str):
                token = token_data
                logger.debug(f"[GraphQL Sensors] Using string token, length: {len(token)}")
            else:
                logger.error(f"[GraphQL Sensors] Unexpected token type: {type(token_data)}")
                return None
            
            # Validate token
            if not token or not isinstance(token, str) or len(token.strip()) < 10:
                logger.error("[GraphQL Sensors] Invalid or too short token")
                return None
                
            return token.strip()
            
        except Exception as e:
            logger.error(f"[GraphQL Sensors] Token loading error: {e}")
            return None
    
    def _parse_sensors_response(self, response_data: Dict, server_id: str) -> Dict[str, Any]:
        """✅ FIXED: Enhanced GraphQL ServiceSensors response parsing"""
        try:
            logger.debug(f"[GraphQL Sensors] Parsing response for server {server_id}")
            
            # Check for GraphQL errors first
            if 'errors' in response_data:
                errors = []
                for error in response_data['errors']:
                    error_msg = error.get('message', 'Unknown GraphQL error')
                    error_path = error.get('path', [])
                    errors.append(f"{error_msg} (path: {'/'.join(map(str, error_path))})")
                
                full_error = f"GraphQL errors: {'; '.join(errors)}"
                logger.error(f"[GraphQL Sensors] {full_error}")
                
                return {
                    'success': False, 
                    'error': full_error,
                    'data': None
                }
            
            # Check for data presence
            if 'data' not in response_data:
                logger.error("[GraphQL Sensors] No 'data' field in response")
                return {
                    'success': False, 
                    'error': 'No data field in GraphQL response',
                    'data': None
                }
            
            # Check for serviceSensors
            if 'serviceSensors' not in response_data['data']:
                logger.error("[GraphQL Sensors] No 'serviceSensors' field in data")
                return {
                    'success': False, 
                    'error': 'No serviceSensors field in response data',
                    'data': None
                }
            
            sensors = response_data['data']['serviceSensors']
            
            # Handle null response
            if sensors is None:
                logger.warning("[GraphQL Sensors] serviceSensors returned null - may indicate server access issues")
                return {
                    'success': False, 
                    'error': 'ServiceSensors returned null (check server access permissions)',
                    'data': None
                }
            
            # ✅ FIX 4: Enhanced data extraction with better error handling
            try:
                # CPU data extraction - try both fields
                cpu_usage = 0
                cpu_total = 0
                
                if 'cpuTotal' in sensors and sensors['cpuTotal'] is not None:
                    cpu_total = float(sensors['cpuTotal'])
                elif 'cpu' in sensors and sensors['cpu'] is not None:
                    cpu_total = float(sensors['cpu'])
                
                cpu_usage = cpu_total  # Use total CPU as primary metric
                
                # ✅ FIX 5: Memory data extraction - G-Portal likely returns MB already
                memory_data = sensors.get('memory', {})
                memory_percent = 0
                memory_used_mb = 0
                memory_total_mb = 0
                
                if memory_data and isinstance(memory_data, dict):
                    memory_percent = float(memory_data.get('percent', 0))
                    
                    # ✅ CRITICAL FIX: G-Portal likely returns memory in MB, not bytes
                    memory_used = memory_data.get('used', 0)
                    memory_total = memory_data.get('total', 0)
                    
                    # Check if values look like bytes (very large numbers) or MB (reasonable numbers)
                    if memory_used > 1000000:  # If > 1MB in bytes, convert
                        memory_used_mb = float(memory_used) / (1024 * 1024)
                        memory_total_mb = float(memory_total) / (1024 * 1024)
                        logger.debug("[GraphQL Sensors] Converted memory from bytes to MB")
                    else:  # Already in MB
                        memory_used_mb = float(memory_used)
                        memory_total_mb = float(memory_total)
                        logger.debug("[GraphQL Sensors] Using memory values as MB")
                
                # Uptime extraction
                uptime = float(sensors.get('uptime', 0))
                
                # Timestamp extraction
                timestamp = sensors.get('timestamp', datetime.now().isoformat())
                
                # ✅ FIX 6: Build parsed data with validation
                parsed_data = {
                    'cpu_usage': round(cpu_usage, 1),
                    'cpu_total': round(cpu_total, 1),
                    'memory_percent': round(memory_percent, 1),
                    'memory_used_mb': round(memory_used_mb, 1),
                    'memory_total_mb': round(memory_total_mb, 1),
                    'uptime': int(uptime),
                    'timestamp': timestamp,
                    'data_source': 'graphql_sensors'
                }
                
                logger.info(f"[GraphQL Sensors] ✅ SUCCESS for {server_id}: "
                           f"CPU={parsed_data['cpu_total']:.1f}%, "
                           f"Memory={parsed_data['memory_percent']:.1f}% "
                           f"({parsed_data['memory_used_mb']:.1f}MB/{parsed_data['memory_total_mb']:.1f}MB), "
                           f"Uptime={parsed_data['uptime']}s")
                
                return {
                    'success': True, 
                    'data': parsed_data,
                    'error': None
                }
                
            except (ValueError, TypeError) as parse_error:
                logger.error(f"[GraphQL Sensors] Data parsing error: {parse_error}")
                logger.error(f"[GraphQL Sensors] Raw sensors data: {sensors}")
                return {
                    'success': False, 
                    'error': f'Data parsing error: {parse_error}',
                    'data': None
                }
            
        except Exception as e:
            logger.error(f"[GraphQL Sensors] Response parsing error: {e}")
            logger.error(f"[GraphQL Sensors] Raw response: {response_data}")
            return {
                'success': False, 
                'error': f'Parse error: {e}',
                'data': None
            }
    
    def test_connection(self, server_id: str) -> Dict[str, Any]:
        """✅ ENHANCED: Test GraphQL ServiceSensors connection with detailed diagnostics"""
        try:
            logger.info(f"[GraphQL Sensors] Testing connection for server {server_id}")
            
            # Test token first
            token = self._get_auth_token()
            if not token:
                return {
                    'success': False,
                    'message': 'Authentication failed: No valid token available',
                    'data': None,
                    'diagnostics': {
                        'token_available': False,
                        'token_length': 0,
                        'endpoint': self.graphql_endpoint
                    }
                }
            
            result = self.get_service_sensors(server_id)
            
            diagnostics = {
                'token_available': True,
                'token_length': len(token),
                'endpoint': self.graphql_endpoint,
                'server_id': str(server_id),
                'request_successful': result['success']
            }
            
            if result['success']:
                logger.info(f"[GraphQL Sensors] ✅ Connection test PASSED for {server_id}")
                return {
                    'success': True,
                    'message': 'GraphQL ServiceSensors connection successful',
                    'data': result['data'],
                    'diagnostics': diagnostics
                }
            else:
                logger.warning(f"[GraphQL Sensors] ❌ Connection test FAILED for {server_id}: {result['error']}")
                diagnostics['error'] = result['error']
                return {
                    'success': False,
                    'message': f'Connection test failed: {result["error"]}',
                    'data': None,
                    'diagnostics': diagnostics
                }
                
        except Exception as e:
            logger.error(f"[GraphQL Sensors] Connection test error: {e}")
            return {
                'success': False,
                'message': f'Connection test error: {e}',
                'data': None,
                'diagnostics': {
                    'token_available': False,
                    'error': str(e),
                    'endpoint': self.graphql_endpoint
                }
            }
