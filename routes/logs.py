"""
GUST Bot Enhanced - Logs Management Routes (FIXED AUTHENTICATION VERSION)
=============================================================================
✅ FIXED: Corrected session-based authentication to use proper file token loading
✅ FIXED: Consistent authentication with working console commands
✅ FIXED: Proper token access for API calls
✅ FIXED: Added missing requests import
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
import requests  # ✅ FIXED: Added missing requests import

# Local imports
from routes.auth import require_auth

# GUST database optimization imports
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

# ✅ FIXED: Use the original working load_token and refresh_token functions
try:
    from utils.helpers import load_token, refresh_token
except ImportError:
    # ✅ FIXED: Fallback that matches the working pattern from other modules
    def load_token():
        """Load token from file - matches working console command pattern"""
        try:
            token_file = 'gp-session.json'
            if os.path.exists(token_file):
                with open(token_file, 'r') as f:
                    data = json.load(f)
                    return data.get('access_token')
            return None
        except Exception as e:
            logging.error(f"Error loading token: {e}")
            return None
    
    def refresh_token():
        return False

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
    """G-Portal API client for log management with corrected auth"""
    
    def __init__(self):
        self.base_url = "https://www.g-portal.com/ngpapi/"
        self.session = requests.Session()
        
    def get_server_logs(self, server_id, region="us"):
        """Retrieve logs using G-Portal direct endpoint with corrected auth"""
        # ✅ FIXED: Check session authentication properly
        if session.get('demo_mode', False):  # Default to False, not True
            return {'success': False, 'error': 'Demo mode - no real logs available'}
            
        token = load_token()
        if not token:
            return {'success': False, 'error': 'No authentication token available'}
            
        region_code = region.lower()
        log_url = f"https://{region_code}-{server_id}.g-portal.services/{server_id}/server/my_server_identity/logs/public.log"
        
        headers = {
            'Authorization': f'Bearer {token}',
            'User-Agent': 'GUST-Bot/2.0',
            'Accept': 'text/plain, */*',
            'Referer': f'https://www.g-portal.com/int/server/rust-console/{server_id}/logs'
        }
        
        try:
            logger.info(f"📥 Requesting logs from: {log_url}")
            response = self.session.get(log_url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'data': response.text,
                    'server_id': server_id,
                    'timestamp': datetime.now().isoformat()
                }
            elif response.status_code == 401:
                if refresh_token():
                    token = load_token()
                    headers['Authorization'] = f'Bearer {token}'
                    response = self.session.get(log_url, headers=headers, timeout=30)
                    if response.status_code == 200:
                        return {
                            'success': True,
                            'data': response.text,
                            'server_id': server_id,
                            'timestamp': datetime.now().isoformat()
                        }
                
                return {'success': False, 'error': 'Authentication failed'}
            else:
                return {'success': False, 'error': f'HTTP {response.status_code}: {response.text}'}
                
        except Exception as e:
            logger.error(f"❌ Error fetching logs: {e}")
            return {'success': False, 'error': str(e)}
    
    def format_log_entries(self, raw_logs):
        """Format raw log text into structured entries"""
        formatted_logs = []
        
        if not raw_logs:
            return formatted_logs
            
        lines = raw_logs.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            try:
                parts = line.split(':', 4)
                if len(parts) >= 4:
                    date_time = parts[0].strip()
                    level = parts[1].strip()
                    context = parts[2].strip()
                    message = ':'.join(parts[3:]).strip()
                    
                    formatted_logs.append({
                        'timestamp': date_time,
                        'level': level,
                        'context': context,
                        'message': message
                    })
                else:
                    formatted_logs.append({"raw": line})
            except Exception:
                formatted_logs.append({"raw": line})
                
        return formatted_logs

    def parse_player_count_from_logs(self, raw_logs, max_entries=100):
        """Parse player count data from server logs"""
        if not raw_logs:
            return None
            
        lines = raw_logs.split('\n')
        recent_lines = lines[-max_entries:] if len(lines) > max_entries else lines
        
        patterns = [
            r'Players?:\s*(\d+)\s*/\s*(\d+)',
            r'Players?:\s*(\d+)\s*of\s*(\d+)',
            r'(\d+)\s*/\s*(\d+)\s*players?',
            r'Player\s*Count:\s*(\d+)\s*/\s*(\d+)',
            r'Online:\s*(\d+)\s*/\s*(\d+)',
            r'Connected:\s*(\d+)\s*/\s*(\d+)',
            r'Server\s*Info.*?(\d+)\s*/\s*(\d+)',
            r'Status.*?(\d+)\s*/\s*(\d+)',
            r'serverinfo.*?(\d+)\s*/\s*(\d+)',
            r'Server:\s*(\d+)\s*/\s*(\d+)',
        ]
        
        for line in reversed(recent_lines):
            line_lower = line.lower()
            
            if not any(keyword in line_lower for keyword in ['player', 'online', 'connected', 'server', 'info', 'status']):
                continue
                
            for pattern in patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match and len(match.groups()) >= 2:
                    try:
                        current = int(match.group(1))
                        max_players = int(match.group(2))
                        
                        if 0 <= current <= max_players and max_players > 0:
                            percentage = round((current / max_players) * 100, 1)
                            
                            logger.info(f"📊 Found player count in logs: {current}/{max_players} ({percentage}%)")
                            
                            return {
                                'current': current,
                                'max': max_players,
                                'percentage': percentage,
                                'timestamp': datetime.now().isoformat(),
                                'source': 'server_logs',
                                'raw_line': line.strip()
                            }
                    except (ValueError, ZeroDivisionError) as e:
                        logger.debug(f"Error parsing player count: {e}")
                        continue
        
        logger.debug("No player count found in recent log entries")
        return None

def init_logs_routes(app, db, logs_storage):
    """Initialize logs routes with dependencies"""
    
    api_client = GPortalLogAPI()
    
    @logs_bp.route('/api/logs/servers')
    def get_servers():
        """Get list of servers for logs dropdown"""
        try:
            servers = []
            if hasattr(app, 'gust_bot') and hasattr(app.gust_bot, 'servers') and app.gust_bot.servers:
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
                'servers': servers
            })
        except Exception as e:
            logger.error(f"❌ Error retrieving servers for logs: {e}")
            return jsonify({'success': False, 'error': 'Failed to retrieve servers'}), 500
    
    @logs_bp.route('/api/logs')
    @require_auth
    def get_logs():
        """Get list of downloaded logs"""
        try:
            if db and hasattr(db, 'logs'):
                logs = list(db.logs.find({}, {'_id': 0}))
            else:
                logs = logs_storage if logs_storage else []
            
            logger.info(f"📋 Retrieved {len(logs)} log entries")
            return jsonify({
                'success': True,
                'logs': logs,
                'total': len(logs)
            })
        except Exception as e:
            logger.error(f"❌ Error retrieving logs: {e}")
            return jsonify({'success': False, 'error': 'Failed to retrieve logs'}), 500
    
    @logs_bp.route('/api/logs/download', methods=['POST'])
    @require_auth
    def download_logs():
        """Download logs using G-Portal API"""
        try:
            data = request.json or {}
            server_id = data.get('server_id')
            
            if not server_id:
                if hasattr(app, 'gust_bot') and hasattr(app.gust_bot, 'servers') and app.gust_bot.servers:
                    server_id = app.gust_bot.servers[0].get('serverId') if app.gust_bot.servers else None
                
                if not server_id:
                    return jsonify({
                        'success': False,
                        'error': 'No server ID provided and no servers configured'
                    })
            
            region = 'us'
            if hasattr(app, 'gust_bot') and hasattr(app.gust_bot, 'servers') and app.gust_bot.servers:
                for server in app.gust_bot.servers:
                    if server.get('serverId') == server_id:
                        region = server.get('serverRegion', 'us').lower()
                        break
            
            logger.info(f"📥 Downloading logs for server {server_id} in region {region}")
            
            result = api_client.get_server_logs(server_id, region)
            
            if result['success']:
                formatted_logs = api_client.format_log_entries(result['data'])
                
                timestamp = int(time.time())
                output_file = f"parsed_logs_{server_id}_{timestamp}.json"
                output_path = os.path.join('logs', output_file)
                
                os.makedirs('logs', exist_ok=True)
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(formatted_logs, f, indent=2)
                
                log_entry = {
                    'id': f"log_{timestamp}",
                    'server_id': server_id,
                    'region': region,
                    'timestamp': datetime.now().isoformat(),
                    'entries_count': len(formatted_logs),
                    'file_path': output_path,
                    'download_file': output_file,
                    'recent_entries': formatted_logs[-10:] if formatted_logs else []
                }
                
                if db and hasattr(db, 'logs'):
                    db.logs.insert_one(log_entry)
                else:
                    if logs_storage is not None:
                        logs_storage.append(log_entry)
                
                logger.info(f"✅ Successfully downloaded and parsed {len(formatted_logs)} log entries")
                
                return jsonify({
                    'success': True,
                    'message': f'Downloaded {len(formatted_logs)} log entries',
                    'log_id': log_entry['id'],
                    'entries_count': len(formatted_logs),
                    'download_file': output_file
                })
            else:
                return jsonify({
                    'success': False,
                    'error': result['error']
                }), 400
                
        except Exception as e:
            logger.error(f"❌ Error downloading logs: {e}")
            return jsonify({'success': False, 'error': 'Failed to download logs'}), 500
    
    @logs_bp.route('/api/logs/<log_id>/download')
    @require_auth
    def download_log_file(log_id):
        """Download parsed log file"""
        try:
            log_entry = None
            if db and hasattr(db, 'logs'):
                log_entry = db.logs.find_one({'id': log_id}, {'_id': 0})
            else:
                if logs_storage:
                    log_entry = next((log for log in logs_storage if log.get('id') == log_id), None)
            
            if not log_entry:
                return jsonify({'error': 'Log not found'}), 404
            
            file_path = log_entry.get('file_path')
            if not file_path or not os.path.exists(file_path):
                return jsonify({'error': 'Log file not found'}), 404
            
            return send_file(file_path, as_attachment=True, download_name=log_entry.get('download_file'))
            
        except Exception as e:
            logger.error(f"❌ Error downloading log file: {e}")
            return jsonify({'error': 'Failed to download log file'}), 500
    
    @logs_bp.route('/api/logs/refresh', methods=['POST'])
    @require_auth
    def refresh_logs():
        """Refresh logs list"""
        try:
            if db and hasattr(db, 'logs'):
                logs = list(db.logs.find({}, {'_id': 0}))
            else:
                logs = logs_storage if logs_storage else []
            
            return jsonify({
                'success': True,
                'logs': logs,
                'total': len(logs)
            })
        except Exception as e:
            logger.error(f"❌ Error refreshing logs: {e}")
            return jsonify({'success': False, 'error': 'Failed to refresh logs'}), 500

    # ============================================================================
    # ✅ FIXED: CORRECTED PLAYER COUNT API ENDPOINT
    # ============================================================================
    
    @logs_bp.route('/api/logs/player-count/<server_id>', methods=['POST'])
    @require_auth
    def get_player_count_from_logs(server_id):
        """
        ✅ FIXED: Get player count from server logs using corrected authentication
        """
        try:
            logger.info(f"📊 Getting player count from logs for server {server_id}")
            
            # ✅ FIXED: Check session authentication properly
            if not session.get('logged_in'):
                return jsonify({
                    'success': False,
                    'error': 'Authentication required',
                    'server_id': server_id
                }), 401
            
            # ✅ FIXED: Handle demo mode properly (default to False)
            if session.get('demo_mode', False):
                logger.info(f"🎭 Demo mode: Generating mock player data for {server_id}")
                
                # Generate realistic demo data
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
                    'message': f'Demo player count: {current}/{max_players}'
                })
            
            # Check if server exists in configuration
            server_found = False
            region = 'us'
            server_name = f"Server {server_id}"
            
            if hasattr(app, 'gust_bot') and hasattr(app.gust_bot, 'servers') and app.gust_bot.servers:
                for server in app.gust_bot.servers:
                    if server.get('serverId') == server_id:
                        server_found = True
                        region = server.get('serverRegion', 'us').lower()
                        server_name = server.get('serverName', server_name)
                        break
            
            if not server_found:
                logger.warning(f"⚠️ Server {server_id} not found in configuration, using defaults")
            
            # ✅ FIXED: Use corrected API client
            logger.info(f"📥 Fetching fresh logs for player count analysis...")
            result = api_client.get_server_logs(server_id, region)
            
            if not result['success']:
                logger.warning(f"⚠️ Fresh log fetch failed: {result['error']}, checking existing logs...")
                
                # Check existing logs as fallback
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
                                    entry.get('raw', entry.get('message', '')) 
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
                        'server_id': server_id
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
                    'message': f'Player count updated from logs: {player_data["current"]}/{player_data["max"]}'
                })
            else:
                logger.info(f"ℹ️ No player count found in logs for {server_id}")
                
                backend_scheduler_state['command_stats']['empty_responses'] += 1
                
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
                    'warning': 'Consider running "serverinfo" command to populate logs with current data'
                })
                
        except Exception as e:
            logger.error(f"❌ Error getting player count from logs for {server_id}: {e}")
            backend_scheduler_state['command_stats']['errors'] += 1
            return jsonify({
                'success': False,
                'error': f'Failed to get player count from logs: {str(e)}',
                'server_id': server_id
            }), 500

    return logs_bp