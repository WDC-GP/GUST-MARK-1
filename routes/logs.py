"""
GUST Bot Enhanced - Logs Management Routes (FINAL AUTHENTICATION FIX)
=============================================================================
✅ FIXED: Proper OAuth/JWT token validation matching helpers.py
✅ FIXED: Consistent authentication using centralized token management
✅ FIXED: Proper error handling for token refresh failures
✅ FIXED: Enhanced API client with robust authentication retry logic
✅ FIXED: Consistent session handling across all endpoints
✅ ENHANCED: Better logging and error messages for debugging
✅ ENHANCED: Improved player count parsing with multiple patterns
✅ ENHANCED: Atomic file operations for log storage
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

# Local imports - Use centralized authentication
from routes.auth import require_auth

# ✅ FIXED: Use only the centralized token management functions
from utils.helpers import load_token, refresh_token, monitor_token_health, validate_token_file

# GUST database optimization imports (graceful fallback)
try:
    from utils.gust_db_optimization import (
        get_user_with_cache,
        get_user_balance_cached,
        update_user_balance,
        db_performance_monitor
    )
except ImportError:
    # Graceful fallback if optimization module not available
    pass

logger = logging.getLogger(__name__)

logs_bp = Blueprint('logs', __name__)

# Backend command scheduling state
backend_scheduler_state = {
    'enabled': False,
    'thread': None,
    'running': False,
    'interval': 30,
    'last_run': None,
    'command_stats': defaultdict(int)
}

class GPortalLogAPI:
    """
    ✅ ENHANCED: G-Portal API client with comprehensive authentication handling
    """
    
    def __init__(self):
        self.base_url = "https://www.g-portal.com/ngpapi/"
        self.session = requests.Session()
        self.max_retries = 2
        self.retry_delay = 2
        
    def get_server_logs(self, server_id, region="us"):
        """
        ✅ ENHANCED: Retrieve logs with robust authentication and retry logic
        
        Args:
            server_id (str): Server ID
            region (str): Server region
            
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
        
        # Get token with enhanced validation
        token = load_token()
        if not token:
            logger.warning(f"❌ No authentication token available for server {server_id}")
            return {
                'success': False, 
                'error': 'No authentication token available. Please re-login to G-Portal.'
            }
        
        # ✅ FINAL FIX: Proper OAuth/JWT token validation (matching helpers.py)
        def is_valid_token(token):
            if not token or len(token.strip()) < 10:
                return False
            # Allow alphanumeric plus common OAuth/JWT characters: . - _ + / =
            allowed_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-_+/=')
            return all(c in allowed_chars for c in token.strip())
        
        if not is_valid_token(token):
            logger.error(f"❌ Invalid token format for server {server_id}: length={len(token)}")
            logger.debug(f"❌ Token sample: {token[:20]}...")
            return {
                'success': False,
                'error': 'Invalid authentication token. Please re-login.'
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
                    return {
                        'success': True,
                        'data': response.text,
                        'server_id': server_id,
                        'timestamp': datetime.now().isoformat(),
                        'content_length': len(response.text),
                        'attempt': attempt + 1
                    }
                    
                elif response.status_code == 401:
                    logger.warning(f"🔐 Authentication failed for server {server_id}, attempting token refresh")
                    
                    # Attempt token refresh
                    if refresh_token():
                        logger.info("✅ Token refresh successful, retrying request")
                        new_token = load_token()
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
                        continue  # Retry with delay
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
        return {
            'success': False,
            'error': f'Failed to retrieve logs after {self.max_retries + 1} attempts'
        }
    
    def format_log_entries(self, raw_logs):
        """
        ✅ ENHANCED: Format raw log text into structured entries with better parsing
        
        Args:
            raw_logs (str): Raw log content
            
        Returns:
            list: Formatted log entries
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
        
        Args:
            raw_logs (str): Raw log content
            max_entries (int): Maximum entries to scan
            
        Returns:
            dict or None: Player count data if found
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
                            max_players <= 1000):  # Reasonable max limit
                            
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
    ✅ ENHANCED: Initialize logs routes with comprehensive error handling
    
    Args:
        app: Flask application instance
        db: Database connection (optional)
        logs_storage: Storage system for logs
        
    Returns:
        Blueprint: Configured logs blueprint
    """
    
    api_client = GPortalLogAPI()
    
    @logs_bp.route('/api/logs/servers')
    @require_auth
    def get_servers():
        """
        ✅ ENHANCED: Get list of servers with better error handling
        """
        try:
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
            
            logger.info(f"📋 Retrieved {len(servers)} servers for logs dropdown")
            return jsonify({
                'success': True,
                'servers': servers,
                'count': len(servers)
            })
            
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
        """
        ✅ ENHANCED: Get list of downloaded logs with pagination support
        """
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
                }
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
    def download_logs():
        """
        ✅ ENHANCED: Download logs with comprehensive error handling and validation
        """
        try:
            data = request.json or {}
            server_id = data.get('server_id')
            
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
            
            # Download logs using enhanced API client
            result = api_client.get_server_logs(server_id, region)
            
            if result['success']:
                # Format logs
                formatted_logs = api_client.format_log_entries(result['data'])
                
                # Create output file with timestamp
                timestamp = int(time.time())
                output_file = f"parsed_logs_{server_id}_{timestamp}.json"
                
                # Ensure logs directory exists
                logs_dir = 'data/logs'
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
                    'content_length': result.get('content_length', 0)
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
                    'server_name': server_name
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
        """
        ✅ ENHANCED: Download parsed log file with validation
        """
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
        """
        ✅ ENHANCED: Refresh logs list with optional cleanup
        """
        try:
            # Optional cleanup of old files
            cleanup = request.json.get('cleanup', False) if request.json else False
            
            if cleanup:
                cleanup_count = 0
                logs_dir = 'data/logs'
                if os.path.exists(logs_dir):
                    try:
                        # Remove files older than 7 days
                        cutoff_time = time.time() - (7 * 24 * 60 * 60)
                        
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
                'cleanup_count': cleanup_count if cleanup else 0,
                'refreshed_at': datetime.now().isoformat()
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
        ✅ COMPREHENSIVE FIX: Get player count with robust authentication and error handling
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
            
            # Try to get fresh logs for analysis
            logger.info(f"📥 Fetching fresh logs for player count analysis...")
            result = api_client.get_server_logs(server_id, region)
            
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
                    return jsonify({
                        'success': False,
                        'error': f'Unable to fetch logs for server {server_id}: {result["error"]}',
                        'server_id': server_id,
                        'server_name': server_name
                    }), 400
            
            # Parse player count from logs
            player_data = api_client.parse_player_count_from_logs(result['data'])
            
            if player_data:
                logger.info(f"✅ Successfully parsed player count: {player_data['current']}/{player_data['max']} ({player_data['percentage']}%)")
                
                backend_scheduler_state['command_stats']['successful_queries'] += 1
                
                return jsonify({
                    'success': True,
                    'data': player_data,
                    'server_id': server_id,
                    'server_name': server_name,
                    'message': f'Player count: {player_data["current"]}/{player_data["max"]} ({player_data["percentage"]}%)'
                })
                
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
                
                return jsonify({
                    'success': True,
                    'data': default_data,
                    'server_id': server_id,
                    'server_name': server_name,
                    'message': 'No recent player count data found in server logs',
                    'recommendation': 'Run "serverinfo" command to populate logs with current data'
                })
                
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
        """
        ✅ NEW: Health check endpoint for logs system
        """
        try:
            health_status = {
                'healthy': True,
                'timestamp': datetime.now().isoformat(),
                'components': {}
            }
            
            # Check token health
            token_health = monitor_token_health()
            health_status['components']['authentication'] = {
                'healthy': token_health['healthy'],
                'status': token_health['status'],
                'message': token_health['message']
            }
            
            # Check logs directory
            logs_dir = 'data/logs'
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
            
            # Check API client
            health_status['components']['api_client'] = {
                'healthy': True,
                'max_retries': api_client.max_retries,
                'retry_delay': api_client.retry_delay
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
            
            return jsonify(health_status)
            
        except Exception as e:
            logger.error(f"❌ Error in logs health check: {e}")
            return jsonify({
                'healthy': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }), 500

    return logs_bp
