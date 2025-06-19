"""
"""
"""
GUST Bot Enhanced - Logs Management Routes (API-Based)
=====================================================
Routes for server log downloading using G-Portal API integration
"""

# Standard library imports
from datetime import datetime
import json
import logging
import os
import time

# Third-party imports
from flask import Blueprint, request, jsonify, send_file
import requests

# Local imports
from routes.auth import require_auth



# Try to import token functions - create fallbacks if not available
try:

# GUST database optimization imports
from utils.gust_db_optimization import (
    get_user_with_cache,
    get_user_balance_cached,
    update_user_balance,
    db_performance_monitor
)
    from utils.helpers import load_token, refresh_token
except ImportError:
    # Fallback token functions if utils.helpers doesn't exist
    def load_token():
        try:
            if os.path.exists('gp-session.json'):
                with open('gp-session.json', 'r') as f:
                    data = json.load(f)
                    return data.get('access_token')
        except:
            pass
        return None
    
    def refresh_token():
        # Basic refresh - in production, implement proper token refresh
        return False

logger = logging.getLogger(__name__)

logs_bp = Blueprint('logs', __name__)

class GPortalLogAPI:
    """G-Portal API client for log management"""
    
    def __init__(self):
        self.base_url = "https://www.g-portal.com/ngpapi/"
        self.session = requests.Session()
        
    def get_server_logs(self, server_id, region="us"):
        """
        Retrieve logs using G-Portal direct endpoint
        
        Args:
            server_id (str): Server ID
            region (str): Server region (us, eu, as)
            
        Returns:
            dict: API response with log data
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
            logger.info(f"ðŸ“¥ Requesting logs from: {log_url}")
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
            logger.error(f"âŒ Error fetching logs: {e}")
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
            
            logger.info(f"ðŸ“‹ Retrieved {len(servers)} servers for logs dropdown")
            return jsonify({
                'success': True,
                'servers': servers
            })
        except Exception as e:
            logger.error(f"âŒ Error retrieving servers for logs: {e}")
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
            
            logger.info(f"ðŸ“‹ Retrieved {len(logs)} log entries")
            return jsonify({
                'success': True,
                'logs': logs,
                'total': len(logs)
            })
        except Exception as e:
            logger.error(f"âŒ Error retrieving logs: {e}")
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
            
            logger.info(f"ðŸ“¥ Downloading logs for server {server_id} in region {region}")
            
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
                
                logger.info(f"âœ… Successfully downloaded and parsed {len(formatted_logs)} log entries")
                
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
            logger.error(f"âŒ Error downloading logs: {e}")
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
            logger.error(f"âŒ Error downloading log file: {e}")
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
            logger.error(f"âŒ Error refreshing logs: {e}")
            return jsonify({'success': False, 'error': 'Failed to refresh logs'}), 500
    
    return logs_bp





