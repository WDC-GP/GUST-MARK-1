"""
Routes/Logs API Endpoints Module for GUST-MARK-1
=================================================
✅ MODULARIZED: All Flask route decorators and API endpoints
✅ PRESERVED: Exact same functionality and responses as original
✅ OPTIMIZED: Clean separation of API logic from business logic
✅ MAINTAINED: Flask blueprint pattern and init_logs_routes signature
"""

from flask import Blueprint, request, jsonify, session, send_file
from datetime import datetime, timedelta
import logging
import os
import time

# Import authentication
from routes.auth import require_auth

# Import from specialized modules
from .logs_parser import LogsParser
from .logs_storage import LogsStorage  
from .logs_playercount import PlayerCountSystem

# Configuration and optimization
try:
    from config import Config
    from utils.gust_optimization import get_optimization_config
except ImportError:
    class Config:
        LOG_RETENTION_DAYS = 7
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

# Blueprint setup
logs_bp = Blueprint('logs', __name__)

# Global state management
backend_scheduler_state = {
    'enabled': False,
    'thread': None,
    'running': False,
    'interval': 30,
    'last_run': None,
    'command_stats': {
        'successful_queries': 0,
        'cache_hits': 0,
        'empty_responses': 0,
        'failed_queries': 0
    },
    'request_cache': {},
    'cache_ttl': 30,
    'last_api_call': 0,
    'throttle_delay': 5
}

def init_logs_routes(app, db, logs_storage):
    """
    ✅ PRESERVED: Initialize logs routes with exact same signature and functionality
    
    Args:
        app: Flask application instance
        db: Database instance (MongoDB or None)
        logs_storage: Storage instance for logs data
        
    Returns:
        Flask Blueprint instance
    """
    
    # Initialize specialized modules
    parser = LogsParser()
    storage = LogsStorage(db, logs_storage)
    player_count = PlayerCountSystem(parser, storage)
    
    # Store module references for route handlers
    logs_bp.parser = parser
    logs_bp.storage = storage
    logs_bp.player_count = player_count
    
    logger.info("✅ Logs API routes initialized with modular architecture")
    return logs_bp

@logs_bp.route('/api/logs/servers')
@require_auth
def get_servers():
    """Get list of servers with better error handling"""
    try:
        # Check demo mode
        if session.get('demo_mode', False):
            logger.info("🎭 Demo mode: Returning mock server data")
            return jsonify({
                'success': True,
                'servers': [
                    {
                        'serverId': 'demo_server_1',
                        'serverName': 'Demo Rust Server #1',
                        'serverRegion': 'us',
                        'serverGame': 'rust'
                    },
                    {
                        'serverId': 'demo_server_2', 
                        'serverName': 'Demo Rust Server #2',
                        'serverRegion': 'eu',
                        'serverGame': 'rust'
                    }
                ],
                'message': 'Demo mode - mock server data'
            })
        
        # Get servers from GUST bot integration
        servers = []
        if hasattr(request, 'app') and hasattr(request.app, 'gust_bot'):
            if hasattr(request.app.gust_bot, 'servers') and request.app.gust_bot.servers:
                servers = request.app.gust_bot.servers
                logger.info(f"📋 Found {len(servers)} configured servers")
            else:
                logger.warning("⚠️ No servers configured in GUST bot")
        else:
            logger.warning("⚠️ GUST bot instance not available")
        
        return jsonify({
            'success': True,
            'servers': servers,
            'count': len(servers),
            'message': f'Found {len(servers)} configured servers'
        })
        
    except Exception as e:
        logger.error(f"❌ Error fetching servers: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch servers',
            'details': str(e)
        }), 500

@logs_bp.route('/api/logs')
@require_auth  
def get_logs():
    """Get list of downloaded logs with metadata"""
    try:
        logs = logs_bp.storage.get_all_logs()
        
        # Sort by timestamp (newest first)
        logs = sorted(logs, key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return jsonify({
            'success': True,
            'logs': logs,
            'total': len(logs),
            'retrieved_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ Error fetching logs: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch logs',
            'details': str(e)
        }), 500

@logs_bp.route('/api/logs/<log_id>')
@require_auth
def get_log_entries(log_id):
    """Get specific log entries with pagination"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        # Limit per_page to reasonable values
        per_page = min(max(per_page, 1), 500)
        
        log_data = logs_bp.storage.get_log_entries(log_id, page, per_page)
        
        if not log_data:
            return jsonify({'error': 'Log not found'}), 404
        
        return jsonify(log_data)
        
    except Exception as e:
        logger.error(f"❌ Error fetching log entries for {log_id}: {e}")
        return jsonify({
            'error': 'Failed to fetch log entries',
            'details': str(e)
        }), 500

@logs_bp.route('/api/logs/download', methods=['POST'])
@require_auth
def download_logs():
    """Download logs for a specific server with comprehensive optimization"""
    try:
        data = request.get_json()
        if not data or 'server_id' not in data:
            return jsonify({
                'success': False,
                'error': 'Server ID is required'
            }), 400
        
        server_id = data['server_id']
        use_cache = data.get('use_cache', True)
        
        # Validate server ID
        if not server_id or len(server_id) > 50:
            return jsonify({
                'success': False,
                'error': 'Invalid server ID format'
            }), 400
        
        # Get server information
        server_name = f"Server {server_id}"
        region = "us"
        
        # Check for server details in GUST bot
        if hasattr(request, 'app') and hasattr(request.app, 'gust_bot'):
            if hasattr(request.app.gust_bot, 'servers'):
                for server in request.app.gust_bot.servers:
                    if server.get('serverId') == server_id:
                        region = server.get('serverRegion', 'us').lower()
                        server_name = server.get('serverName', server_name)
                        break
        
        logger.info(f"📥 Downloading logs for {server_name} ({server_id}) in region {region}")
        
        # Download logs using parser's API client
        result = logs_bp.parser.download_server_logs(server_id, region, use_cache)
        
        if result['success']:
            # Format and store logs
            formatted_logs = logs_bp.parser.format_log_entries(result['data'])
            
            # Save to storage
            log_entry = logs_bp.storage.save_log_data(
                server_id=server_id,
                server_name=server_name,
                region=region,
                formatted_logs=formatted_logs,
                metadata=result.get('metadata', {})
            )
            
            logger.info(f"✅ Successfully downloaded and parsed {len(formatted_logs)} log entries")
            
            return jsonify({
                'success': True,
                'message': f'Downloaded {len(formatted_logs)} log entries from {server_name}',
                'log_id': log_entry['id'],
                'entries_count': len(formatted_logs),
                'download_file': log_entry.get('download_file'),
                'file_size': log_entry.get('file_size', 0),
                'server_name': server_name,
                'cached': result.get('cached', False),
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
        log_entry = logs_bp.storage.get_log_metadata(log_id)
        
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
            cleanup_count = logs_bp.storage.cleanup_old_logs(Config.LOG_RETENTION_DAYS)
            if cleanup_count > 0:
                logger.info(f"🧹 Cleaned up {cleanup_count} old log files")
        
        # Clear parser cache
        logs_bp.parser.clear_cache()
        logger.info("🧹 Cleared API cache")
        
        # Get updated logs list
        logs = logs_bp.storage.get_all_logs()
        
        # Sort by timestamp (newest first)
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
    ✅ PRESERVED: Get player count with dual auth support and 30s buffer time
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
            return logs_bp.player_count.get_demo_player_count(server_id)
        
        # Get player count from logs
        result = logs_bp.player_count.get_player_count_from_logs(server_id)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"❌ Error getting player count from logs for {server_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get player count from logs',
            'details': str(e),
            'server_id': server_id
        }), 500

# Export blueprint and initialization function
__all__ = ['logs_bp', 'init_logs_routes']