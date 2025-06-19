"""
GUST Bot Enhanced - Logs Management Routes (COMPLETE WITH BACKEND SCHEDULING)
=============================================================================
Routes for server log downloading + Player Count + OPTIONAL Backend Command Scheduling
✅ Frontend automatic commands (recommended)
✅ Backend scheduling option for reliability
✅ Complete logs-based player count integration
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
from flask import Blueprint, request, jsonify, send_file
import requests

# Local imports
from routes.auth import require_auth

# GUST database optimization imports
from utils.gust_db_optimization import (
    get_user_with_cache,
    get_user_balance_cached,
    update_user_balance,
    db_performance_monitor
)

# Try to import token functions - create fallbacks if not available
try:
    from utils.helpers import load_token, refresh_token
except ImportError:
    # Fallback token functions if utils.helpers doesn't exist
    def load_token():
        try:
            if os.path.exists('gp-session.json'):
                with open('gp-session.json', 'r') as f:
                    data = json.load(f)
                    return data.get('access_token')
        except Exception:
            pass
        return None
    
    def refresh_token():
        # Basic refresh - in production, implement proper token refresh
        return False

logger = logging.getLogger(__name__)

logs_bp = Blueprint('logs', __name__)

# Backend command scheduling state (OPTIONAL - prefer frontend scheduling)
backend_scheduler_state = {
    'enabled': False,  # Set to True to enable backend scheduling
    'thread': None,
    'running': False,
    'interval': 30,    # 30 seconds (less frequent than frontend)
    'last_run': None,
    'command_stats': defaultdict(int)
}

class GPortalLogAPI:
    """G-Portal API client for log management"""
    
    def __init__(self):
        self.base_url = "https://www.g-portal.com/ngpapi/"
        self.session = requests.Session()
        
    def get_server_logs(self, server_id, region="us"):
        """
        Retrieve logs using G-Portal direct endpoint
        """
        token = load_token()
        if not token:
            return {'success': False, 'error': 'No authentication token available'}
            
        # Convert region to lowercase for URL
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
                # Try to refresh token
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
                # Try to parse structured log format
                # Format: YYYY-MM-DD HH:MM:SS LEVEL CONTEXT: MESSAGE
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
                    # Handle raw string entries
                    formatted_logs.append({"raw": line})
            except Exception:
                # Handle any parsing errors by storing as raw
                formatted_logs.append({"raw": line})
                
        return formatted_logs

    def parse_player_count_from_logs(self, raw_logs, max_entries=100):
        """
        Parse player count data from server logs
        """
        if not raw_logs:
            return None
            
        lines = raw_logs.split('\n')
        recent_lines = lines[-max_entries:] if len(lines) > max_entries else lines
        
        # Enhanced patterns to match player count information
        patterns = [
            # Server info responses
            r'Players?:\s*(\d+)\s*/\s*(\d+)',
            r'Players?:\s*(\d+)\s*of\s*(\d+)',
            r'(\d+)\s*/\s*(\d+)\s*players?',
            r'Player\s*Count:\s*(\d+)\s*/\s*(\d+)',
            r'Online:\s*(\d+)\s*/\s*(\d+)',
            r'Connected:\s*(\d+)\s*/\s*(\d+)',
            # Server status logs
            r'Server\s*Info.*?(\d+)\s*/\s*(\d+)',
            r'Status.*?(\d+)\s*/\s*(\d+)',
            # Serverinfo command responses
            r'serverinfo.*?(\d+)\s*/\s*(\d+)',
            r'Server:\s*(\d+)\s*/\s*(\d+)',
        ]
        
        # Search recent entries first (most likely to have current data)
        for line in reversed(recent_lines):
            line_lower = line.lower()
            
            # Skip obviously unrelated lines
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

    def send_console_command(self, server_id, command, region="us"):
        """
        Send console command to server (for backend scheduling)
        
        Args:
            server_id (str): Server ID
            command (str): Command to send
            region (str): Server region
            
        Returns:
            dict: Command result
        """
        token = load_token()
        if not token:
            return {'success': False, 'error': 'No authentication token available'}
        
        try:
            # G-Portal GraphQL endpoint for console commands
            graphql_url = "https://www.g-portal.com/graphql"
            
            # GraphQL mutation for sending console commands
            query = """
            mutation sendConsoleMessage($sid: Int!, $region: REGION!, $message: String!) {
                sendConsoleMessage(sid: $sid, region: $region, message: $message) {
                    success
                    message
                }
            }
            """
            
            variables = {
                "sid": int(server_id),
                "region": region.upper(),
                "message": command
            }
            
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json',
                'User-Agent': 'GUST-Bot/2.0'
            }
            
            payload = {
                'query': query,
                'variables': variables
            }
            
            logger.info(f"📡 Sending command '{command}' to server {server_id}")
            
            response = self.session.post(graphql_url, json=payload, headers=headers, timeout=15)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('data', {}).get('sendConsoleMessage', {}).get('success'):
                    logger.info(f"✅ Command sent successfully to {server_id}")
                    return {'success': True, 'message': 'Command sent successfully'}
                else:
                    error_msg = result.get('errors', [{}])[0].get('message', 'Unknown error')
                    logger.error(f"❌ Command failed: {error_msg}")
                    return {'success': False, 'error': error_msg}
            else:
                logger.error(f"❌ HTTP error: {response.status_code}")
                return {'success': False, 'error': f'HTTP {response.status_code}'}
                
        except Exception as e:
            logger.error(f"❌ Error sending command: {e}")
            return {'success': False, 'error': str(e)}

def init_logs_routes(app, db, logs_storage):
    """Initialize logs routes with dependencies"""
    
    api_client = GPortalLogAPI()
    
    @logs_bp.route('/api/logs/servers')
    def get_servers():
        """Get list of servers for logs dropdown"""
        try:
            servers = []
            if hasattr(app, 'gust_bot') and hasattr(app.gust_bot, 'servers') and app.gust_bot.servers:
                # Convert server data to format expected by logs frontend
                servers = [
                    {
                        'id': server.get('serverId'),
                        'name': server.get('serverName', f"Server {server.get('serverId')}"),
                        'region': server.get('serverRegion', 'Unknown')
                    }
                    for server in app.gust_bot.servers
                    if server.get('serverId')  # Only include servers with valid IDs
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
                # Try to get default server from user's servers
                if hasattr(app, 'gust_bot') and hasattr(app.gust_bot, 'servers') and app.gust_bot.servers:
                    server_id = app.gust_bot.servers[0].get('serverId') if app.gust_bot.servers else None
                
                if not server_id:
                    return jsonify({
                        'success': False,
                        'error': 'No server ID provided and no servers configured'
                    })
            
            # Get server region if available
            region = 'us'  # default
            if hasattr(app, 'gust_bot') and hasattr(app.gust_bot, 'servers') and app.gust_bot.servers:
                for server in app.gust_bot.servers:
                    if server.get('serverId') == server_id:
                        region = server.get('serverRegion', 'us').lower()
                        break
            
            logger.info(f"📥 Downloading logs for server {server_id} in region {region}")
            
            # Get logs via API
            result = api_client.get_server_logs(server_id, region)
            
            if result['success']:
                # Format and parse logs
                formatted_logs = api_client.format_log_entries(result['data'])
                
                # Save parsed data to file
                timestamp = int(time.time())
                output_file = f"parsed_logs_{server_id}_{timestamp}.json"
                output_path = os.path.join('logs', output_file)
                
                # Ensure logs directory exists
                os.makedirs('logs', exist_ok=True)
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(formatted_logs, f, indent=2)
                
                # Create log entry
                log_entry = {
                    'id': f"log_{timestamp}",
                    'server_id': server_id,
                    'region': region,
                    'timestamp': datetime.now().isoformat(),
                    'entries_count': len(formatted_logs),
                    'file_path': output_path,
                    'download_file': output_file,
                    'recent_entries': formatted_logs[-10:] if formatted_logs else []  # Last 10 entries
                }
                
                # Store in database or memory
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
            # Find log entry
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
    # LOGS-BASED PLAYER COUNT INTEGRATION - ENHANCED API ENDPOINT
    # ============================================================================
    
    @logs_bp.route('/api/logs/player-count/<server_id>', methods=['POST'])
    @require_auth
    def get_player_count_from_logs(server_id):
        """
        Get player count from server logs (enhanced logs-based integration)
        """
        try:
            logger.info(f"📊 Getting player count from logs for server {server_id}")
            
            # Check if server exists in configuration
            server_found = False
            region = 'us'  # default
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
            
            # Get fresh logs from G-Portal
            logger.info(f"📥 Fetching fresh logs for player count analysis...")
            result = api_client.get_server_logs(server_id, region)
            
            if not result['success']:
                # Try to fall back to existing logs if fresh fetch fails
                logger.warning(f"⚠️ Fresh log fetch failed: {result['error']}, checking existing logs...")
                
                # Check if we have existing logs for this server
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
                                # Convert back to raw format for parsing
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
                
                # Update command stats
                backend_scheduler_state['command_stats']['successful_queries'] += 1
                
                return jsonify({
                    'success': True,
                    'data': player_data,
                    'server_id': server_id,
                    'server_name': server_name,
                    'message': f'Player count updated from logs: {player_data["current"]}/{player_data["max"]}'
                })
            else:
                # No player count found - could be empty server or no recent serverinfo
                logger.info(f"ℹ️ No player count found in logs for {server_id}")
                
                # Update command stats
                backend_scheduler_state['command_stats']['empty_responses'] += 1
                
                # Return a default response indicating no data found
                default_data = {
                    'current': 0,
                    'max': 100,  # reasonable default
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

    # ============================================================================
    # OPTIONAL BACKEND COMMAND SCHEDULING (USE ONLY IF FRONTEND FAILS)
    # ============================================================================
    
    @logs_bp.route('/api/logs/backend-scheduler/status')
    @require_auth
    def get_backend_scheduler_status():
        """Get backend scheduler status"""
        return jsonify({
            'success': True,
            'scheduler': {
                'enabled': backend_scheduler_state['enabled'],
                'running': backend_scheduler_state['running'],
                'interval': backend_scheduler_state['interval'],
                'last_run': backend_scheduler_state['last_run'],
                'stats': dict(backend_scheduler_state['command_stats'])
            },
            'recommendation': 'Use frontend auto-commands for better performance'
        })
    
    @logs_bp.route('/api/logs/backend-scheduler/toggle', methods=['POST'])
    @require_auth
    def toggle_backend_scheduler():
        """Toggle backend scheduler (NOT RECOMMENDED - use frontend instead)"""
        try:
            data = request.json or {}
            enable = data.get('enable', False)
            
            if enable and not backend_scheduler_state['enabled']:
                # Start backend scheduler
                start_backend_scheduler(app)
                return jsonify({
                    'success': True,
                    'message': 'Backend scheduler started (consider using frontend auto-commands instead)',
                    'status': 'started'
                })
            elif not enable and backend_scheduler_state['enabled']:
                # Stop backend scheduler
                stop_backend_scheduler()
                return jsonify({
                    'success': True,
                    'message': 'Backend scheduler stopped',
                    'status': 'stopped'
                })
            else:
                return jsonify({
                    'success': True,
                    'message': f'Backend scheduler already {"enabled" if enable else "disabled"}',
                    'status': 'no_change'
                })
                
        except Exception as e:
            logger.error(f"❌ Error toggling backend scheduler: {e}")
            return jsonify({
                'success': False,
                'error': f'Failed to toggle scheduler: {str(e)}'
            }), 500

    def start_backend_scheduler(app):
        """Start backend command scheduler (OPTIONAL)"""
        if backend_scheduler_state['running']:
            return
        
        logger.info("🔄 Starting backend command scheduler...")
        backend_scheduler_state['enabled'] = True
        backend_scheduler_state['running'] = True
        
        def scheduler_thread():
            while backend_scheduler_state['running']:
                try:
                    with app.app_context():
                        run_backend_command_round(app)
                    
                    backend_scheduler_state['last_run'] = datetime.now().isoformat()
                    
                    # Sleep for interval
                    for _ in range(backend_scheduler_state['interval']):
                        if not backend_scheduler_state['running']:
                            break
                        time.sleep(1)
                        
                except Exception as e:
                    logger.error(f"❌ Backend scheduler error: {e}")
                    time.sleep(5)  # Brief pause on error
        
        backend_scheduler_state['thread'] = threading.Thread(target=scheduler_thread, daemon=True)
        backend_scheduler_state['thread'].start()
        
        logger.info("✅ Backend scheduler started")

    def stop_backend_scheduler():
        """Stop backend command scheduler"""
        if not backend_scheduler_state['running']:
            return
        
        logger.info("⏹️ Stopping backend scheduler...")
        backend_scheduler_state['running'] = False
        backend_scheduler_state['enabled'] = False
        
        if backend_scheduler_state['thread']:
            backend_scheduler_state['thread'].join(timeout=5)
            backend_scheduler_state['thread'] = None
        
        logger.info("✅ Backend scheduler stopped")

    def run_backend_command_round(app):
        """Run a round of backend commands"""
        try:
            if not hasattr(app, 'gust_bot') or not app.gust_bot.servers:
                return
            
            logger.info("📡 Backend scheduler: Running command round...")
            
            for server in app.gust_bot.servers[:3]:  # Limit to 3 servers for backend
                server_id = server.get('serverId')
                region = server.get('serverRegion', 'us').lower()
                
                if server_id:
                    logger.info(f"📡 Backend sending serverinfo to {server_id}")
                    
                    # Send serverinfo command
                    result = api_client.send_console_command(server_id, 'serverinfo', region)
                    
                    if result['success']:
                        backend_scheduler_state['command_stats']['commands_sent'] += 1
                        logger.info(f"✅ Backend command sent to {server_id}")
                    else:
                        backend_scheduler_state['command_stats']['command_failures'] += 1
                        logger.warning(f"⚠️ Backend command failed for {server_id}: {result['error']}")
                    
                    # Small delay between servers
                    time.sleep(2)
            
            logger.info("✅ Backend command round complete")
            
        except Exception as e:
            logger.error(f"❌ Backend command round error: {e}")
    
    return logs_bp