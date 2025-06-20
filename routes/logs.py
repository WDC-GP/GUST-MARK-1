"""
GUST Bot Enhanced - Logs Management Routes (OPTIMIZED + 30s BUFFER FIX)
========================================================================
✅ FIXED: Reduced buffer time to 30 seconds for maximum G-Portal compatibility  
✅ ENHANCED: Integration with optimized config.py settings
✅ ENHANCED: Request throttling and batching based on config
✅ ENHANCED: Rate limiting integration to prevent token conflicts
✅ ENHANCED: Improved error handling for authentication failures
✅ ENHANCED: Better caching and debouncing for reduced API load
✅ PRESERVED: All existing functionality and features
"""

# Standard library imports
from datetime import datetime
import json
import logging
import os
import time
import re
import threading
from collections import defaultdict

# Third-party imports
from flask import Blueprint, request, jsonify, send_file, session
import requests

# Local imports
from routes.auth import require_auth, require_live_mode

# ✅ OPTIMIZED: Use centralized token management with enhanced validation
from utils.helpers import load_token, refresh_token, monitor_token_health, validate_token_file

# ✅ NEW: Import optimized configuration and rate limiter
from config import Config, get_optimization_config
from utils.rate_limiter import RateLimiter

# GUST database optimization imports (graceful fallback)
try:
    from utils.gust_db_optimization import (
        get_user_with_cache,
        get_user_balance_cached,
        update_user_balance,
        db_performance_monitor
    )
except ImportError:
    pass

logger = logging.getLogger(__name__)

logs_bp = Blueprint('logs', __name__)

# ✅ OPTIMIZED: Enhanced state management with config integration
optimization_config = get_optimization_config()

backend_scheduler_state = {
    'enabled': False,
    'thread': None,
    'running': False,
    'interval': optimization_config['logs_polling_interval'] // 1000,  # Convert to seconds
    'last_run': None,
    'command_stats': defaultdict(int),
    'request_cache': {},
    'cache_ttl': optimization_config['default_cache_ttl'] // 1000,
    'last_api_call': 0,
    'throttle_delay': optimization_config['request_batch_delay'] // 1000
}

# ✅ NEW: Rate limiter for API calls
api_rate_limiter = RateLimiter(
    max_calls=Config.RATE_LIMIT_MAX_CALLS,
    time_window=Config.RATE_LIMIT_TIME_WINDOW
)

class OptimizedGPortalLogAPI:
    """
    ✅ OPTIMIZED: G-Portal API client with 30s buffer time and enhanced optimization
    """
    
    def __init__(self):
        self.base_url = "https://www.g-portal.com/ngpapi/"
        self.session = requests.Session()
        self.max_retries = 2
        self.retry_delay = 2
        
        # ✅ OPTIMIZED: Integration with config settings
        self.max_concurrent = Config.MAX_CONCURRENT_API_CALLS
        self.batch_size = Config.REQUEST_BATCH_SIZE
        self.batch_delay = Config.REQUEST_BATCH_DELAY / 1000
        
        # ✅ OPTIMIZED: Request caching
        self.cache = {}
        self.cache_ttl = Config.DEFAULT_CACHE_TTL / 1000
        
    def _is_cache_valid(self, cache_key):
        """Check if cached data is still valid"""
        if cache_key not in self.cache:
            return False
        
        cache_data = self.cache[cache_key]
        return (time.time() - cache_data['timestamp']) < self.cache_ttl
    
    def _get_from_cache(self, cache_key):
        """Get data from cache if valid"""
        if self._is_cache_valid(cache_key):
            logger.debug(f"📋 Using cached data for {cache_key}")
            return self.cache[cache_key]['data']
        return None
    
    def _store_in_cache(self, cache_key, data):
        """Store data in cache"""
        self.cache[cache_key] = {
            'data': data,
            'timestamp': time.time()
        }
        logger.debug(f"💾 Cached data for {cache_key}")
    
    def _wait_for_rate_limit(self):
        """Wait if necessary to respect rate limits"""
        api_rate_limiter.wait_if_needed('logs_api')
        
        # ✅ OPTIMIZED: Additional throttling based on config
        current_time = time.time()
        time_since_last = current_time - backend_scheduler_state.get('last_api_call', 0)
        min_interval = optimization_config.get('debounce_logs', 2000) / 1000
        
        if time_since_last < min_interval:
            sleep_time = min_interval - time_since_last
            logger.debug(f"⏳ Throttling API call for {sleep_time:.1f}s")
            time.sleep(sleep_time)
        
        backend_scheduler_state['last_api_call'] = time.time()
        
    def get_server_logs(self, server_id, region="us", use_cache=True):
        """
        ✅ OPTIMIZED: Retrieve logs with caching, throttling, and 30s buffer time
        
        Args:
            server_id (str): Server ID
            region (str): Server region
            use_cache (bool): Whether to use caching
            
        Returns:
            dict: API response with success status and data
        """
        # Check demo mode first
        if session.get('demo_mode', False):
            logger.info(f"🎭 Demo mode: Cannot fetch real logs for server {server_id}")
            return {
                'success': False, 
                'error': 'Demo mode - no real logs available. Login with G-Portal credentials for live features.'
            }
        
        # Ensure user is authenticated
        if not session.get('logged_in', False):
            return {
                'success': False,
                'error': 'Authentication required - please login first'
            }
        
        # ✅ OPTIMIZED: Check cache first
        cache_key = f"logs_{server_id}_{region}"
        if use_cache:
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                backend_scheduler_state['command_stats']['cache_hits'] += 1
                return cached_data
        
        # ✅ OPTIMIZED: Rate limiting and throttling
        self._wait_for_rate_limit()
        
        # ✅ CRITICAL FIX: Use load_token with 30s buffer enhancement
        token = self._get_optimized_token()
        if not token:
            logger.warning(f"❌ No authentication token available for server {server_id}")
            return {
                'success': False, 
                'error': 'No authentication token available. Please re-login to G-Portal.'
            }
        
        # ✅ ENHANCED: JWT token validation
        if len(token) < 20 or not self._is_valid_jwt_token(token):
            logger.error(f"❌ Invalid JWT token format for server {server_id}")
            return {
                'success': False,
                'error': 'Invalid authentication token format. Please re-login.'
            }
        
        region_code = region.lower()
        log_url = f"https://{region_code}-{server_id}.g-portal.services/{server_id}/server/my_server_identity/logs/public.log"
        
        # Enhanced headers for better compatibility
        headers = {
            'Authorization': f'Bearer {token}',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Referer': f'https://www.g-portal.com/int/server/rust-console/{server_id}/logs'
        }
        
        # Retry logic for robust authentication
        for attempt in range(self.max_retries + 1):
            try:
                if attempt > 0:
                    logger.info(f"🔄 Retry attempt {attempt} for server {server_id}")
                    time.sleep(self.retry_delay * attempt)
                
                logger.info(f"📥 Requesting logs from: {log_url}")
                response = self.session.get(log_url, headers=headers, timeout=30)
                
                if response.status_code == 200:
                    logger.info(f"✅ Successfully retrieved logs for server {server_id}")
                    
                    result = {
                        'success': True,
                        'data': response.text,
                        'server_id': server_id,
                        'timestamp': datetime.now().isoformat(),
                        'content_length': len(response.text),
                        'attempt': attempt + 1,
                        'cached': False
                    }
                    
                    # ✅ OPTIMIZED: Store in cache
                    if use_cache:
                        self._store_in_cache(cache_key, result)
                    
                    backend_scheduler_state['command_stats']['successful_requests'] += 1
                    return result
                    
                elif response.status_code == 401:
                    logger.warning(f"🔐 Authentication failed for server {server_id}, attempting token refresh")
                    
                    # ✅ OPTIMIZED: Use enhanced token refresh with 30s buffer
                    if self._refresh_token_with_optimization():
                        logger.info("✅ Token refresh successful, retrying request")
                        new_token = self._get_optimized_token()
                        if new_token and new_token != token:
                            headers['Authorization'] = f'Bearer {new_token}'
                            token = new_token
                            continue  # Retry with new token
                    
                    logger.error(f"❌ Token refresh failed for server {server_id}")
                    return {
                        'success': False, 
                        'error': 'Authentication failed. Please re-login to G-Portal.'
                    }
                    
                elif response.status_code == 403:
                    logger.error(f"❌ Access forbidden for server {server_id}")
                    return {
                        'success': False,
                        'error': 'Access forbidden. Check server permissions or re-login.'
                    }
                    
                elif response.status_code == 404:
                    logger.error(f"❌ Server {server_id} not found or logs not available")
                    return {
                        'success': False,
                        'error': f'Server {server_id} not found or logs not available'
                    }
                    
                elif response.status_code == 429:
                    logger.warning(f"⚠️ Rate limited for server {server_id}")
                    if attempt < self.max_retries:
                        # ✅ OPTIMIZED: Exponential backoff for rate limiting
                        sleep_time = self.retry_delay * (2 ** attempt)
                        time.sleep(sleep_time)
                        continue
                    return {
                        'success': False,
                        'error': 'Rate limited. Please wait before trying again.'
                    }
                    
                else:
                    logger.error(f"❌ HTTP {response.status_code} for server {server_id}: {response.text[:200]}")
                    if attempt < self.max_retries:
                        continue  # Retry on server errors
                    return {
                        'success': False, 
                        'error': f'HTTP {response.status_code}: {response.text[:100]}'
                    }
                    
            except requests.exceptions.Timeout:
                logger.warning(f"⏰ Request timeout for server {server_id} (attempt {attempt + 1})")
                if attempt < self.max_retries:
                    continue
                return {
                    'success': False,
                    'error': 'Request timeout. Server may be busy.'
                }
                
            except requests.exceptions.ConnectionError:
                logger.warning(f"🌐 Connection error for server {server_id} (attempt {attempt + 1})")
                if attempt < self.max_retries:
                    continue
                return {
                    'success': False,
                    'error': 'Connection error. Check internet connection.'
                }
                
            except Exception as e:
                logger.error(f"❌ Unexpected error for server {server_id}: {e}")
                if attempt < self.max_retries:
                    continue
                return {
                    'success': False,
                    'error': f'Unexpected error: {str(e)}'
                }
        
        # If we get here, all retries failed
        backend_scheduler_state['command_stats']['failed_requests'] += 1
        return {
            'success': False,
            'error': f'Failed to retrieve logs after {self.max_retries + 1} attempts'
        }
    
    def _get_optimized_token(self):
        """
        ✅ CRITICAL OPTIMIZATION: Enhanced token loading with 30s buffer time
        """
        try:
            # Check token health first
            token_health = monitor_token_health()
            
            if not token_health['healthy']:
                logger.warning(f"⚠️ Token health check failed: {token_health['message']}")
                
                # Try refresh if possible
                if token_health['action'] == 'refresh_now':
                    if self._refresh_token_with_optimization():
                        logger.info("✅ Token refreshed successfully during health check")
                    else:
                        logger.error("❌ Token refresh failed during health check")
                        return ''
                elif token_health['action'] == 'login_required':
                    logger.error("❌ Login required - token cannot be refreshed")
                    return ''
            
            # Get token using centralized function
            token = load_token()
            
            # ✅ ENHANCED: Additional validation with 30s buffer check
            if token:
                validation = validate_token_file()
                if validation['time_left'] < 30:  # 30 second buffer
                    logger.info(f"🔄 Token expires in {validation['time_left']}s, proactive refresh...")
                    if self._refresh_token_with_optimization():
                        token = load_token()  # Get refreshed token
                        logger.info("✅ Proactive token refresh successful")
                    else:
                        logger.warning("❌ Proactive token refresh failed")
            
            return token
            
        except Exception as e:
            logger.error(f"❌ Error in optimized token loading: {e}")
            return ''
    
    def _refresh_token_with_optimization(self):
        """
        ✅ OPTIMIZED: Enhanced token refresh with rate limiting
        """
        try:
            # Rate limit token refresh attempts
            if not api_rate_limiter.is_allowed('token_refresh'):
                logger.warning("⚠️ Token refresh rate limited")
                time.sleep(1)
                return False
            
            success = refresh_token()
            
            if success:
                backend_scheduler_state['command_stats']['successful_refreshes'] += 1
                # Clear relevant caches after token refresh
                self._clear_auth_related_cache()
            else:
                backend_scheduler_state['command_stats']['failed_refreshes'] += 1
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error in optimized token refresh: {e}")
            backend_scheduler_state['command_stats']['failed_refreshes'] += 1
            return False
    
    def _clear_auth_related_cache(self):
        """Clear cache entries that might be affected by token refresh"""
        keys_to_remove = []
        for key in self.cache:
            if 'logs_' in key:  # Clear all logs cache after auth refresh
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.cache[key]
        
        logger.debug(f"🧹 Cleared {len(keys_to_remove)} cache entries after token refresh")
    
    def _is_valid_jwt_token(self, token):
        """
        ✅ ENHANCED: JWT-compatible token validation for logs API
        """
        if not token or not isinstance(token, str):
            return False
        
        token = token.strip()
        
        # Minimum length check
        if len(token) < 20:
            return False
        
        # JWT tokens can contain: letters, numbers, dots, hyphens, underscores, plus, slash, equals
        allowed_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-_+/=')
        
        # Check if all characters are allowed
        return all(c in allowed_chars for c in token)
    
    def format_log_entries(self, raw_logs):
        """
        ✅ ENHANCED: Format raw log text into structured entries with better parsing
        """
        formatted_logs = []
        
        if not raw_logs:
            return formatted_logs
            
        lines = raw_logs.split('\n')
        for line_num, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
                
            try:
                # Enhanced log parsing patterns
                patterns = [
                    # Standard format: timestamp:level:context:message
                    r'^(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}):([^:]+):([^:]+):(.+)$',
                    # Alternative format: [timestamp] level context message
                    r'^\[(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\]\s+([^\s]+)\s+([^\s]+)\s+(.+)$',
                    # Simple format: timestamp level message
                    r'^(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s+([^\s]+)\s+(.+)$'
                ]
                
                parsed = False
                for pattern in patterns:
                    match = re.match(pattern, line)
                    if match:
                        groups = match.groups()
                        if len(groups) == 4:
                            timestamp, level, context, message = groups
                            formatted_logs.append({
                                'line_number': line_num + 1,
                                'timestamp': timestamp.strip(),
                                'level': level.strip(),
                                'context': context.strip(),
                                'message': message.strip(),
                                'raw_line': line
                            })
                        elif len(groups) == 3:
                            timestamp, level, message = groups
                            formatted_logs.append({
                                'line_number': line_num + 1,
                                'timestamp': timestamp.strip(),
                                'level': level.strip(),
                                'context': 'server',
                                'message': message.strip(),
                                'raw_line': line
                            })
                        parsed = True
                        break
                
                if not parsed:
                    # If no pattern matches, store as raw entry
                    formatted_logs.append({
                        'line_number': line_num + 1,
                        'raw': line,
                        'timestamp': None,
                        'level': 'unknown',
                        'context': 'raw',
                        'message': line
                    })
                    
            except Exception as e:
                logger.debug(f"Error parsing log line {line_num + 1}: {e}")
                formatted_logs.append({
                    'line_number': line_num + 1,
                    'raw': line,
                    'error': str(e),
                    'timestamp': None,
                    'level': 'error',
                    'context': 'parse_error',
                    'message': line
                })
                
        return formatted_logs

    def parse_player_count_from_logs(self, raw_logs, max_entries=100):
        """
        ✅ ENHANCED: Parse player count with comprehensive pattern matching
        """
        if not raw_logs:
            return None
            
        lines = raw_logs.split('\n')
        recent_lines = lines[-max_entries:] if len(lines) > max_entries else lines
        
        # Enhanced patterns for player count detection
        patterns = [
            # Standard patterns
            r'Players?:\s*(\d+)\s*/\s*(\d+)',
            r'Players?:\s*(\d+)\s*of\s*(\d+)',
            r'(\d+)\s*/\s*(\d+)\s*players?',
            r'Player\s*Count:\s*(\d+)\s*/\s*(\d+)',
            r'Online:\s*(\d+)\s*/\s*(\d+)',
            r'Connected:\s*(\d+)\s*/\s*(\d+)',
            
            # Enhanced patterns
            r'Server\s*Info.*?(\d+)\s*/\s*(\d+)',
            r'Status.*?(\d+)\s*/\s*(\d+)',
            r'serverinfo.*?(\d+)\s*/\s*(\d+)',
            r'Server:\s*(\d+)\s*/\s*(\d+)',
            r'Current\s*Players?:\s*(\d+)\s*/\s*(\d+)',
            r'Active\s*Players?:\s*(\d+)\s*/\s*(\d+)',
            
            # Rust-specific patterns
            r'player\.list.*?(\d+)\s*/\s*(\d+)',
            r'global\.playerlist.*?(\d+)\s*/\s*(\d+)',
            r'admin\.playerlist.*?(\d+)\s*/\s*(\d+)',
            
            # Alternative formats
            r'\[(\d+)/(\d+)\]',
            r'<(\d+)/(\d+)>',
            r'\((\d+)/(\d+)\)'
        ]
        
        for line in reversed(recent_lines):
            line_lower = line.lower()
            
            # Enhanced keyword filtering
            relevant_keywords = [
                'player', 'online', 'connected', 'server', 'info', 'status',
                'list', 'count', 'users', 'clients', 'active'
            ]
            
            if not any(keyword in line_lower for keyword in relevant_keywords):
                continue
                
            for pattern in patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match and len(match.groups()) >= 2:
                    try:
                        current = int(match.group(1))
                        max_players = int(match.group(2))
                        
                        # Enhanced validation
                        if (0 <= current <= max_players and 
                            max_players > 0 and 
                            max_players <= 1000):
                            
                            percentage = round((current / max_players) * 100, 1)
                            
                            logger.info(f"📊 Found player count in logs: {current}/{max_players} ({percentage}%)")
                            
                            return {
                                'current': current,
                                'max': max_players,
                                'percentage': percentage,
                                'timestamp': datetime.now().isoformat(),
                                'source': 'server_logs',
                                'raw_line': line.strip(),
                                'pattern_used': pattern
                            }
                            
                    except (ValueError, ZeroDivisionError) as e:
                        logger.debug(f"Error parsing player count from line '{line}': {e}")
                        continue
        
        logger.debug("No player count found in recent log entries")
        return None

def init_logs_routes(app, db, logs_storage):
    """
    ✅ OPTIMIZED: Initialize logs routes with comprehensive optimization and 30s buffer
    """
    
    api_client = OptimizedGPortalLogAPI()
    
    @logs_bp.route('/api/logs/servers')
    @require_auth
    def get_servers():
        """Get list of servers with better error handling"""
        try:
            # ✅ OPTIMIZED: Add caching for server list
            cache_key = 'servers_list'
            cached_servers = api_client._get_from_cache(cache_key)
            if cached_servers:
                return jsonify(cached_servers)
            
            servers = []
            if (hasattr(app, 'gust_bot') and 
                hasattr(app.gust_bot, 'servers') and 
                app.gust_bot.servers):
                
                servers = [
                    {
                        'id': server.get('serverId'),
                        'name': server.get('serverName', f"Server {server.get('serverId')}"),
                        'region': server.get('serverRegion', 'Unknown')
                    }
                    for server in app.gust_bot.servers
                    if server.get('serverId')
                ]
            
            result = {
                'success': True,
                'servers': servers,
                'count': len(servers),
                'timestamp': datetime.now().isoformat()
            }
            
            # Cache the result
            api_client._store_in_cache(cache_key, result)
            
            logger.info(f"📋 Retrieved {len(servers)} servers for logs dropdown")
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"❌ Error retrieving servers for logs: {e}")
            return jsonify({
                'success': False, 
                'error': 'Failed to retrieve servers',
                'details': str(e)
            }), 500
    
    @logs_bp.route('/api/logs')
    @require_auth
    def get_logs():
        """Get list of downloaded logs with pagination support"""
        try:
            # Get pagination parameters
            page = max(1, int(request.args.get('page', 1)))
            per_page = min(100, max(10, int(request.args.get('per_page', 20))))
            
            if db and hasattr(db, 'logs'):
                # Database storage with pagination
                total_logs = db.logs.count_documents({})
                skip = (page - 1) * per_page
                
                logs = list(db.logs.find(
                    {}, 
                    {'_id': 0}
                ).sort('timestamp', -1).skip(skip).limit(per_page))
                
                total_pages = (total_logs + per_page - 1) // per_page
                
            else:
                # In-memory storage with pagination
                all_logs = logs_storage if logs_storage else []
                total_logs = len(all_logs)
                
                # Sort by timestamp (newest first)
                sorted_logs = sorted(
                    all_logs, 
                    key=lambda x: x.get('timestamp', ''), 
                    reverse=True
                )
                
                start_idx = (page - 1) * per_page
                end_idx = start_idx + per_page
                logs = sorted_logs[start_idx:end_idx]
                
                total_pages = (total_logs + per_page - 1) // per_page
            
            logger.info(f"📋 Retrieved {len(logs)} logs (page {page}/{total_pages})")
            
            return jsonify({
                'success': True,
                'logs': logs,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total_logs,
                    'total_pages': total_pages,
                    'has_next': page < total_pages,
                    'has_prev': page > 1
                },
                'optimization_stats': backend_scheduler_state['command_stats']
            })
            
        except Exception as e:
            logger.error(f"❌ Error retrieving logs: {e}")
            return jsonify({
                'success': False, 
                'error': 'Failed to retrieve logs',
                'details': str(e)
            }), 500
    
    @logs_bp.route('/api/logs/download', methods=['POST'])
    @require_auth
    @require_live_mode  # ✅ OPTIMIZED: Require live mode for log downloads
    def download_logs():
        """✅ OPTIMIZED: Download logs with 30s buffer time and comprehensive optimization"""
        try:
            data = request.json or {}
            server_id = data.get('server_id')
            use_cache = data.get('use_cache', True)
            
            # Auto-select first server if none provided
            if not server_id:
                if (hasattr(app, 'gust_bot') and 
                    hasattr(app.gust_bot, 'servers') and 
                    app.gust_bot.servers):
                    server_id = app.gust_bot.servers[0].get('serverId')
                
                if not server_id:
                    return jsonify({
                        'success': False,
                        'error': 'No server ID provided and no servers configured'
                    }), 400
            
            # Get server region
            region = 'us'
            server_name = f"Server {server_id}"
            
            if (hasattr(app, 'gust_bot') and 
                hasattr(app.gust_bot, 'servers') and 
                app.gust_bot.servers):
                
                for server in app.gust_bot.servers:
                    if server.get('serverId') == server_id:
                        region = server.get('serverRegion', 'us').lower()
                        server_name = server.get('serverName', server_name)
                        break
            
            logger.info(f"📥 Downloading logs for {server_name} ({server_id}) in region {region}")
            
            # ✅ OPTIMIZED: Download logs using enhanced API client with 30s buffer
            result = api_client.get_server_logs(server_id, region, use_cache)
            
            if result['success']:
                # Format logs
                formatted_logs = api_client.format_log_entries(result['data'])
                
                # Create output file with timestamp
                timestamp = int(time.time())
                output_file = f"parsed_logs_{server_id}_{timestamp}.json"
                
                # Ensure logs directory exists
                logs_dir = 'logs'  # Use relative path as per config
                os.makedirs(logs_dir, exist_ok=True)
                output_path = os.path.join(logs_dir, output_file)
                
                # Save formatted logs atomically
                temp_path = output_path + '.tmp'
                try:
                    with open(temp_path, 'w', encoding='utf-8') as f:
                        json.dump(formatted_logs, f, indent=2, ensure_ascii=False)
                    
                    # Atomic move
                    if os.path.exists(output_path):
                        os.remove(output_path)
                    os.rename(temp_path, output_path)
                    
                except Exception as save_error:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                    raise save_error
                
                # Create log entry
                log_entry = {
                    'id': f"log_{timestamp}",
                    'server_id': server_id,
                    'server_name': server_name,
                    'region': region,
                    'timestamp': datetime.now().isoformat(),
                    'entries_count': len(formatted_logs),
                    'file_path': output_path,
                    'download_file': output_file,
                    'file_size': os.path.getsize(output_path),
                    'recent_entries': formatted_logs[-10:] if formatted_logs else [],
                    'download_attempt': result.get('attempt', 1),
                    'content_length': result.get('content_length', 0),
                    'cached': result.get('cached', False)
                }
                
                # Store log entry
                try:
                    if db and hasattr(db, 'logs'):
                        db.logs.insert_one(log_entry.copy())
                    else:
                        if logs_storage is not None:
                            logs_storage.append(log_entry)
                except Exception as storage_error:
                    logger.warning(f"⚠️ Failed to store log entry: {storage_error}")
                
                logger.info(f"✅ Successfully downloaded and parsed {len(formatted_logs)} log entries")
                
                return jsonify({
                    'success': True,
                    'message': f'Downloaded {len(formatted_logs)} log entries from {server_name}',
                    'log_id': log_entry['id'],
                    'entries_count': len(formatted_logs),
                    'download_file': output_file,
                    'file_size': log_entry['file_size'],
                    'server_name': server_name,
                    'cached': log_entry['cached'],
                    'optimization_stats': backend_scheduler_state['command_stats']
                })
                
            else:
                logger.warning(f"⚠️ Log download failed for {server_id}: {result['error']}")
                return jsonify({
                    'success': False,
                    'error': result['error'],
                    'server_id': server_id,
                    'server_name': server_name
                }), 400
                
        except Exception as e:
            logger.error(f"❌ Error downloading logs: {e}")
            return jsonify({
                'success': False, 
                'error': 'Failed to download logs',
                'details': str(e)
            }), 500
    
    @logs_bp.route('/api/logs/<log_id>/download')
    @require_auth
    def download_log_file(log_id):
        """Download parsed log file with validation"""
        try:
            log_entry = None
            
            # Find log entry
            if db and hasattr(db, 'logs'):
                log_entry = db.logs.find_one({'id': log_id}, {'_id': 0})
            else:
                if logs_storage:
                    log_entry = next((log for log in logs_storage if log.get('id') == log_id), None)
            
            if not log_entry:
                logger.warning(f"⚠️ Log entry not found: {log_id}")
                return jsonify({'error': 'Log not found'}), 404
            
            file_path = log_entry.get('file_path')
            if not file_path or not os.path.exists(file_path):
                logger.warning(f"⚠️ Log file not found: {file_path}")
                return jsonify({'error': 'Log file not found on disk'}), 404
            
            download_name = log_entry.get('download_file', f'{log_id}.json')
            
            logger.info(f"📤 Sending log file: {download_name}")
            return send_file(
                file_path, 
                as_attachment=True, 
                download_name=download_name,
                mimetype='application/json'
            )
            
        except Exception as e:
            logger.error(f"❌ Error downloading log file {log_id}: {e}")
            return jsonify({
                'error': 'Failed to download log file',
                'details': str(e)
            }), 500
    
    @logs_bp.route('/api/logs/refresh', methods=['POST'])
    @require_auth
    def refresh_logs():
        """Refresh logs list with optional cleanup"""
        try:
            # Optional cleanup of old files
            cleanup = request.json.get('cleanup', False) if request.json else False
            
            cleanup_count = 0
            if cleanup:
                logs_dir = 'logs'
                if os.path.exists(logs_dir):
                    try:
                        # Remove files older than retention period
                        cutoff_time = time.time() - (Config.LOG_RETENTION_DAYS * 24 * 60 * 60)
                        
                        for filename in os.listdir(logs_dir):
                            file_path = os.path.join(logs_dir, filename)
                            if (os.path.isfile(file_path) and 
                                os.path.getmtime(file_path) < cutoff_time):
                                os.remove(file_path)
                                cleanup_count += 1
                                
                        if cleanup_count > 0:
                            logger.info(f"🧹 Cleaned up {cleanup_count} old log files")
                            
                    except Exception as cleanup_error:
                        logger.warning(f"⚠️ Cleanup error: {cleanup_error}")
            
            # Clear API cache
            api_client.cache.clear()
            logger.info("🧹 Cleared API cache")
            
            # Get updated logs list
            if db and hasattr(db, 'logs'):
                logs = list(db.logs.find({}, {'_id': 0}).sort('timestamp', -1))
            else:
                logs = logs_storage if logs_storage else []
                logs = sorted(logs, key=lambda x: x.get('timestamp', ''), reverse=True)
            
            return jsonify({
                'success': True,
                'logs': logs,
                'total': len(logs),
                'cleanup_count': cleanup_count,
                'cache_cleared': True,
                'refreshed_at': datetime.now().isoformat(),
                'optimization_stats': backend_scheduler_state['command_stats']
            })
            
        except Exception as e:
            logger.error(f"❌ Error refreshing logs: {e}")
            return jsonify({
                'success': False, 
                'error': 'Failed to refresh logs',
                'details': str(e)
            }), 500

    @logs_bp.route('/api/logs/player-count/<server_id>', methods=['POST'])
    @require_auth
    def get_player_count_from_logs(server_id):
        """
        ✅ OPTIMIZED: Get player count with 30s buffer time and comprehensive optimization
        """
        try:
            logger.info(f"📊 Getting player count from logs for server {server_id}")
            
            # Check authentication status
            if not session.get('logged_in'):
                return jsonify({
                    'success': False,
                    'error': 'Authentication required',
                    'server_id': server_id
                }), 401
            
            # Handle demo mode
            if session.get('demo_mode', False):
                logger.info(f"🎭 Demo mode: Generating mock player data for {server_id}")
                
                import random
                current = random.randint(0, 50)
                max_players = random.choice([50, 100, 150, 200])
                percentage = round((current / max_players) * 100, 1) if max_players > 0 else 0
                
                demo_data = {
                    'current': current,
                    'max': max_players,
                    'percentage': percentage,
                    'timestamp': datetime.now().isoformat(),
                    'source': 'demo_data',
                    'note': 'Demo mode - simulated data'
                }
                
                return jsonify({
                    'success': True,
                    'data': demo_data,
                    'server_id': server_id,
                    'message': f'Demo player count: {current}/{max_players} ({percentage}%)'
                })
            
            # ✅ OPTIMIZED: Check cache first for player count
            cache_key = f"player_count_{server_id}"
            cached_data = api_client._get_from_cache(cache_key)
            if cached_data:
                backend_scheduler_state['command_stats']['player_count_cache_hits'] += 1
                return jsonify(cached_data)
            
            # Find server configuration
            server_found = False
            region = 'us'
            server_name = f"Server {server_id}"
            
            if (hasattr(app, 'gust_bot') and 
                hasattr(app.gust_bot, 'servers') and 
                app.gust_bot.servers):
                
                for server in app.gust_bot.servers:
                    if server.get('serverId') == server_id:
                        server_found = True
                        region = server.get('serverRegion', 'us').lower()
                        server_name = server.get('serverName', server_name)
                        break
            
            if not server_found:
                logger.warning(f"⚠️ Server {server_id} not found in configuration, using defaults")
            
            # ✅ OPTIMIZED: Try to get fresh logs for analysis using 30s buffer
            logger.info(f"📥 Fetching fresh logs for player count analysis...")
            result = api_client.get_server_logs(server_id, region, use_cache=True)
            
            if not result['success']:
                logger.warning(f"⚠️ Fresh log fetch failed: {result['error']}")
                
                # Fallback to existing logs
                existing_logs = None
                if db and hasattr(db, 'logs'):
                    recent_log = db.logs.find_one(
                        {'server_id': server_id},
                        sort=[('timestamp', -1)]
                    )
                    if recent_log and recent_log.get('file_path') and os.path.exists(recent_log['file_path']):
                        try:
                            with open(recent_log['file_path'], 'r', encoding='utf-8') as f:
                                log_data = json.load(f)
                                existing_logs = '\n'.join([
                                    entry.get('raw_line', entry.get('message', '')) 
                                    for entry in log_data 
                                    if isinstance(entry, dict)
                                ])
                        except Exception as e:
                            logger.error(f"❌ Error reading existing log file: {e}")
                
                if existing_logs:
                    logger.info("📋 Using existing logs for player count analysis")
                    result = {'success': True, 'data': existing_logs}
                else:
                    error_response = {
                        'success': False,
                        'error': f'Unable to fetch logs for server {server_id}: {result["error"]}',
                        'server_id': server_id,
                        'server_name': server_name
                    }
                    return jsonify(error_response), 400
            
            # Parse player count from logs
            player_data = api_client.parse_player_count_from_logs(result['data'])
            
            if player_data:
                logger.info(f"✅ Successfully parsed player count: {player_data['current']}/{player_data['max']} ({player_data['percentage']}%)")
                
                backend_scheduler_state['command_stats']['successful_queries'] += 1
                
                response_data = {
                    'success': True,
                    'data': player_data,
                    'server_id': server_id,
                    'server_name': server_name,
                    'message': f'Player count: {player_data["current"]}/{player_data["max"]} ({player_data["percentage"]}%)',
                    'cached': result.get('cached', False)
                }
                
                # ✅ OPTIMIZED: Cache player count result
                api_client._store_in_cache(cache_key, response_data)
                
                return jsonify(response_data)
                
            else:
                logger.info(f"ℹ️ No player count found in logs for {server_id}")
                
                backend_scheduler_state['command_stats']['empty_responses'] += 1
                
                # Return default data with recommendation
                default_data = {
                    'current': 0,
                    'max': 100,
                    'percentage': 0,
                    'timestamp': datetime.now().isoformat(),
                    'source': 'logs_fallback',
                    'note': 'No recent player count data found in logs'
                }
                
                response_data = {
                    'success': True,
                    'data': default_data,
                    'server_id': server_id,
                    'server_name': server_name,
                    'message': 'No recent player count data found in server logs',
                    'recommendation': 'Run "serverinfo" command to populate logs with current data',
                    'cached': False
                }
                
                # ✅ OPTIMIZED: Cache default result with shorter TTL
                api_client.cache[cache_key] = {
                    'data': response_data,
                    'timestamp': time.time() - (api_client.cache_ttl * 0.5)  # Half TTL for empty results
                }
                
                return jsonify(response_data)
                
        except Exception as e:
            logger.error(f"❌ Error getting player count from logs for {server_id}: {e}")
            backend_scheduler_state['command_stats']['errors'] += 1
            
            return jsonify({
                'success': False,
                'error': f'Failed to get player count from logs: {str(e)}',
                'server_id': server_id,
                'details': str(e)
            }), 500

    @logs_bp.route('/api/logs/health')
    @require_auth
    def logs_health_check():
        """✅ OPTIMIZED: Health check endpoint with comprehensive monitoring"""
        try:
            health_status = {
                'healthy': True,
                'timestamp': datetime.now().isoformat(),
                'components': {},
                'optimization_stats': backend_scheduler_state['command_stats'],
                'buffer_time': '30_seconds'  # Indicate the buffer time being used
            }
            
            # Check token health using centralized function
            token_health = monitor_token_health()
            health_status['components']['authentication'] = {
                'healthy': token_health['healthy'],
                'status': token_health['status'],
                'message': token_health['message'],
                'buffer_optimization': '30s_proactive_refresh'
            }
            
            # Check logs directory
            logs_dir = 'logs'
            if os.path.exists(logs_dir):
                log_files = [f for f in os.listdir(logs_dir) if f.endswith('.json')]
                health_status['components']['storage'] = {
                    'healthy': True,
                    'log_files_count': len(log_files),
                    'directory_exists': True
                }
            else:
                health_status['components']['storage'] = {
                    'healthy': False,
                    'log_files_count': 0,
                    'directory_exists': False
                }
                health_status['healthy'] = False
            
            # Check API client with optimization status
            health_status['components']['api_client'] = {
                'healthy': True,
                'max_retries': api_client.max_retries,
                'retry_delay': api_client.retry_delay,
                'cache_size': len(api_client.cache),
                'rate_limiter_status': api_rate_limiter.get_status('logs_api')
            }
            
            # Check database/storage
            if db and hasattr(db, 'logs'):
                try:
                    log_count = db.logs.count_documents({})
                    health_status['components']['database'] = {
                        'healthy': True,
                        'type': 'mongodb',
                        'log_count': log_count
                    }
                except Exception as db_error:
                    health_status['components']['database'] = {
                        'healthy': False,
                        'type': 'mongodb',
                        'error': str(db_error)
                    }
                    health_status['healthy'] = False
            else:
                health_status['components']['database'] = {
                    'healthy': True,
                    'type': 'in_memory',
                    'log_count': len(logs_storage) if logs_storage else 0
                }
            
            # ✅ NEW: Add optimization metrics
            health_status['optimization'] = {
                'config_integration': True,
                'buffer_time_optimization': '30_seconds',
                'caching_enabled': True,
                'rate_limiting_enabled': True,
                'request_throttling': True,
                'cache_hit_rate': _calculate_cache_hit_rate(),
                'target_reduction': optimization_config.get('target_reduction_percent', 75)
            }
            
            return jsonify(health_status)
            
        except Exception as e:
            logger.error(f"❌ Error in logs health check: {e}")
            return jsonify({
                'healthy': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
                'buffer_time': '30_seconds'
            }), 500

    @logs_bp.route('/api/logs/optimization/stats')
    @require_auth
    def get_optimization_stats():
        """✅ NEW: Get detailed optimization statistics"""
        try:
            stats = backend_scheduler_state['command_stats'].copy()
            
            # Calculate additional metrics
            total_requests = stats.get('successful_requests', 0) + stats.get('failed_requests', 0)
            success_rate = (stats.get('successful_requests', 0) / max(total_requests, 1)) * 100
            
            cache_requests = stats.get('cache_hits', 0) + stats.get('successful_requests', 0)
            cache_hit_rate = (stats.get('cache_hits', 0) / max(cache_requests, 1)) * 100
            
            return jsonify({
                'success': True,
                'stats': stats,
                'metrics': {
                    'total_requests': total_requests,
                    'success_rate': round(success_rate, 2),
                    'cache_hit_rate': round(cache_hit_rate, 2),
                    'buffer_time': '30_seconds',
                    'optimization_level': 'enhanced'
                },
                'rate_limiter': {
                    'logs_api': api_rate_limiter.get_status('logs_api'),
                    'token_refresh': api_rate_limiter.get_status('token_refresh')
                },
                'api_client_cache_size': len(api_client.cache),
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"❌ Error getting optimization stats: {e}")
            return jsonify({
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }), 500

    def _calculate_cache_hit_rate():
        """Calculate cache hit rate from stats"""
        stats = backend_scheduler_state['command_stats']
        cache_hits = stats.get('cache_hits', 0) + stats.get('player_count_cache_hits', 0)
        total_requests = stats.get('successful_requests', 0) + cache_hits
        
        if total_requests == 0:
            return 0.0
        
        return round((cache_hits / total_requests) * 100, 2)

    return logs_bp
