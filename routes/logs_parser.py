"""
Routes/Logs Parser & Processing Module for GUST-MARK-1
======================================================
✅ MODULARIZED: Log parsing, processing, and G-Portal API integration
✅ PRESERVED: All regex patterns and parsing logic from original
✅ OPTIMIZED: Enhanced G-Portal API client with caching and rate limiting
✅ MAINTAINED: Exact same parsing output format and behavior
"""

import requests
import re
import json
import time
import logging
from datetime import datetime, timedelta
from flask import session
from collections import defaultdict

# Import utilities
try:
    from utils.helpers import load_token, get_auth_headers
    from utils.rate_limiter import RateLimiter
    from config import Config
    from utils.gust_optimization import get_optimization_config
except ImportError:
    # Fallback implementations
    def load_token():
        return None
    
    def get_auth_headers():
        return {}
    
    class RateLimiter:
        def __init__(self, max_calls, time_window):
            self.max_calls = max_calls
            self.time_window = time_window
        
        def wait_if_needed(self, key):
            pass
    
    class Config:
        RATE_LIMIT_MAX_CALLS = 60
        RATE_LIMIT_TIME_WINDOW = 60
        MAX_CONCURRENT_API_CALLS = 2
        REQUEST_BATCH_SIZE = 2
        REQUEST_BATCH_DELAY = 5000
        DEFAULT_CACHE_TTL = 30000
    
    def get_optimization_config():
        return {
            'logs_polling_interval': 30000,
            'default_cache_ttl': 30000,
            'request_batch_delay': 5000,
            'debounce_logs': 2000
        }

logger = logging.getLogger(__name__)

class LogsParser:
    """
    ✅ PRESERVED: G-Portal API client with dual auth support and comprehensive log parsing
    """
    
    def __init__(self):
        self.base_url = "https://www.g-portal.com/ngpapi/"
        self.session = requests.Session()
        self.max_retries = 2
        self.retry_delay = 2
        
        # Integration with config settings
        optimization_config = get_optimization_config()
        self.max_concurrent = Config.MAX_CONCURRENT_API_CALLS
        self.batch_size = Config.REQUEST_BATCH_SIZE
        self.batch_delay = Config.REQUEST_BATCH_DELAY / 1000
        
        # Request caching
        self.cache = {}
        self.cache_ttl = Config.DEFAULT_CACHE_TTL / 1000
        
        # Rate limiting
        self.rate_limiter = RateLimiter(
            max_calls=Config.RATE_LIMIT_MAX_CALLS,
            time_window=Config.RATE_LIMIT_TIME_WINDOW
        )
        
        # Optimization state
        self.last_api_call = 0
        self.min_interval = optimization_config.get('debounce_logs', 2000) / 1000
        
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
    
    def clear_cache(self):
        """Clear all cached data"""
        self.cache.clear()
        logger.info("🧹 Cleared parser cache")
    
    def _wait_for_rate_limit(self):
        """Wait if necessary to respect rate limits"""
        self.rate_limiter.wait_if_needed('logs_api')
        
        # Additional throttling based on config
        current_time = time.time()
        time_since_last = current_time - self.last_api_call
        
        if time_since_last < self.min_interval:
            sleep_time = self.min_interval - time_since_last
            logger.debug(f"⏳ Throttling API call for {sleep_time:.1f}s")
            time.sleep(sleep_time)
        
        self.last_api_call = time.time()
    
    def _get_optimized_token(self):
        """
        ✅ PRESERVED: Get authentication token with dual auth support
        """
        try:
            # Try to load token using helpers
            token = load_token()
            if token and isinstance(token, str) and len(token) > 10:
                logger.debug("✅ Retrieved authentication token from helpers")
                return token.strip()
            
            logger.debug("⚠️ No valid token from helpers, trying alternative methods")
            
            # Fallback: try to get from session or other sources
            if hasattr(session, 'get'):
                session_token = session.get('auth_token') or session.get('access_token')
                if session_token:
                    logger.debug("✅ Retrieved token from session")
                    return session_token
            
            logger.warning("❌ No authentication token available from any source")
            return None
            
        except Exception as e:
            logger.error(f"❌ Error retrieving authentication token: {e}")
            return None
    
    def download_server_logs(self, server_id, region="us", use_cache=True):
        """
        ✅ PRESERVED: Retrieve logs with dual auth support, caching, and throttling
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
        
        # Check cache first
        cache_key = f"logs_{server_id}_{region}"
        if use_cache:
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                logger.debug(f"📋 Using cached logs for {server_id}")
                return cached_data
        
        # Rate limiting and throttling
        self._wait_for_rate_limit()
        
        # Get authentication token
        token = self._get_optimized_token()
        if not token:
            logger.warning(f"❌ No authentication token available for server {server_id}")
            return {
                'success': False, 
                'error': 'No authentication token available. Please re-login to G-Portal.'
            }
        
        # Prepare API request
        url = f"{self.base_url}logs/{server_id}"
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'GUST-Bot/1.0'
        }
        
        # Add additional headers from helpers if available
        try:
            additional_headers = get_auth_headers()
            if additional_headers and isinstance(additional_headers, dict):
                headers.update(additional_headers)
        except Exception as e:
            logger.debug(f"Could not get additional auth headers: {e}")
        
        # Make API request with retries
        for attempt in range(self.max_retries + 1):
            try:
                logger.info(f"📡 Fetching logs for server {server_id} (attempt {attempt + 1})")
                
                response = self.session.get(
                    url,
                    headers=headers,
                    timeout=30,
                    params={'region': region}
                )
                
                if response.status_code == 200:
                    log_data = response.text
                    content_length = len(log_data)
                    
                    result = {
                        'success': True,
                        'data': log_data,
                        'attempt': attempt + 1,
                        'content_length': content_length,
                        'cached': False,
                        'metadata': {
                            'server_id': server_id,
                            'region': region,
                            'download_time': datetime.now().isoformat(),
                            'content_length': content_length
                        }
                    }
                    
                    # Cache successful result
                    if use_cache:
                        self._store_in_cache(cache_key, result)
                    
                    logger.info(f"✅ Successfully downloaded {content_length} bytes of logs for {server_id}")
                    return result
                
                elif response.status_code == 401:
                    logger.warning(f"🔐 Authentication failed for server {server_id}")
                    return {
                        'success': False,
                        'error': 'Authentication failed. Please re-login to G-Portal.',
                        'status_code': 401
                    }
                
                elif response.status_code == 404:
                    logger.warning(f"📭 No logs found for server {server_id}")
                    return {
                        'success': False,
                        'error': f'No logs available for server {server_id}. Server may be offline or logs may not be enabled.',
                        'status_code': 404
                    }
                
                else:
                    logger.warning(f"⚠️ API returned status {response.status_code} for server {server_id}")
                    if attempt < self.max_retries:
                        time.sleep(self.retry_delay * (attempt + 1))
                        continue
                    
                    return {
                        'success': False,
                        'error': f'G-Portal API returned status {response.status_code}',
                        'status_code': response.status_code
                    }
                    
            except requests.exceptions.Timeout:
                logger.warning(f"⏰ Timeout fetching logs for server {server_id}")
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay * (attempt + 1))
                    continue
                
                return {
                    'success': False,
                    'error': 'Request timeout. Please try again later.'
                }
                
            except requests.exceptions.RequestException as e:
                logger.error(f"🌐 Network error fetching logs for server {server_id}: {e}")
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay * (attempt + 1))
                    continue
                
                return {
                    'success': False,
                    'error': f'Network error: {str(e)}'
                }
        
        return {
            'success': False,
            'error': 'Failed to download logs after multiple attempts'
        }
    
    def format_log_entries(self, raw_logs):
        """
        ✅ PRESERVED: Parse raw logs into structured format with comprehensive patterns
        """
        if not raw_logs or not isinstance(raw_logs, str):
            return []
        
        lines = raw_logs.strip().split('\n')
        formatted_logs = []
        
        # Enhanced log parsing patterns (preserved from original)
        patterns = [
            # Standard log formats
            (r'^\[(\d{2}:\d{2}:\d{2})\]\s*\[(\w+)\]\s*\[([^\]]+)\]\s*(.*)', 
             ['time', 'level', 'context', 'message']),
            (r'^\[(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\]\s*\[(\w+)\]\s*(.*)', 
             ['timestamp', 'level', 'message']),
            (r'^(\d{2}:\d{2}:\d{2})\s+(\w+):\s*(.*)', 
             ['time', 'level', 'message']),
            (r'^(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s+(.*)', 
             ['timestamp', 'message']),
            
            # Rust-specific patterns
            (r'^\[(\d{2}:\d{2}:\d{2})\]\s*(\w+):\s*(.*)', 
             ['time', 'level', 'message']),
            (r'^(\w+)\s*\|\s*(\d{2}:\d{2}:\d{2})\s*\|\s*(.*)', 
             ['level', 'time', 'message']),
            
            # G-Portal specific patterns
            (r'^\[(\d{2}-\d{2}-\d{4}\s+\d{2}:\d{2}:\d{2})\]\s*(.*)', 
             ['timestamp', 'message']),
            (r'^(\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2})\s+(.*)', 
             ['timestamp', 'message'])
        ]
        
        for line_num, line in enumerate(lines):
            if not line.strip():
                continue
                
            try:
                parsed = False
                
                for pattern, fields in patterns:
                    match = re.match(pattern, line.strip())
                    if match:
                        groups = match.groups()
                        
                        # Create entry with matched fields
                        entry = {
                            'line_number': line_num + 1,
                            'raw': line
                        }
                        
                        # Map matched groups to fields
                        for i, field in enumerate(fields):
                            if i < len(groups):
                                entry[field] = groups[i]
                        
                        # Standardize timestamp format
                        timestamp = None
                        if 'timestamp' in entry:
                            timestamp = entry['timestamp']
                        elif 'time' in entry:
                            # Assume today's date for time-only entries
                            today = datetime.now().strftime('%Y-%m-%d')
                            timestamp = f"{today} {entry['time']}"
                        
                        if timestamp:
                            try:
                                # Try to parse and standardize timestamp
                                for fmt in ['%Y-%m-%d %H:%M:%S', '%d-%m-%Y %H:%M:%S', '%m/%d/%Y %H:%M:%S']:
                                    try:
                                        dt = datetime.strptime(timestamp, fmt)
                                        entry['timestamp'] = dt.isoformat()
                                        break
                                    except ValueError:
                                        continue
                                else:
                                    entry['timestamp'] = timestamp
                            except Exception:
                                entry['timestamp'] = timestamp
                        
                        # Set defaults for missing fields
                        entry.setdefault('level', 'info')
                        entry.setdefault('context', 'server')
                        entry.setdefault('message', entry.get('message', line.strip()))
                        
                        formatted_logs.append(entry)
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
                        'message': line.strip()
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
                    'message': line.strip()
                })
        
        logger.info(f"📊 Parsed {len(formatted_logs)} log entries from {len(lines)} raw lines")
        return formatted_logs
    
    def parse_player_count_from_logs(self, raw_logs, max_entries=100):
        """
        ✅ PRESERVED: Parse player count with comprehensive pattern matching
        """
        if not raw_logs:
            return None
            
        lines = raw_logs.split('\n')
        recent_lines = lines[-max_entries:] if len(lines) > max_entries else lines
        
        # Enhanced patterns for player count detection (preserved from original)
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

# Export the main class
__all__ = ['LogsParser']