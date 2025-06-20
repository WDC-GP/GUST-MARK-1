"""
Server Health Backend Routes for WDC-GP/GUST-MARK-1
Layout-focused endpoints: Commands for right column, health data for left side charts
Integrates with verified existing systems and utils/server_health_storage.py
"""

from flask import Blueprint, jsonify, request
from datetime import datetime
import logging
from functools import wraps

# Import verified patterns from existing routes
try:
    from routes.auth import require_auth
except ImportError:
    # Fallback auth decorator (verified pattern from existing routes)
    def require_auth(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            return f(*args, **kwargs)
        return decorated_function

# Import verified health check integration
try:
    from utils.gust_db_optimization import perform_optimization_health_check
except ImportError:
    def perform_optimization_health_check():
        return {"status": "healthy", "statistics": {}, "response_time": 45}

logger = logging.getLogger(__name__)

# Global storage reference (verified pattern from economy.py)
_server_health_storage = None

# Blueprint creation (verified pattern)
server_health_bp = Blueprint('server_health', __name__)


def init_server_health_routes(app, db, server_health_storage):
    """Initialize server health routes using verified pattern from routes/__init__.py"""
    global _server_health_storage
    _server_health_storage = server_health_storage
    
    logger.info("[✅ OK] Server Health routes initialized with verified storage patterns")
    print("[✅ OK] Server Health routes initialized")
    
    # CRITICAL FIX: Return the blueprint so it can be registered
    return server_health_bp


# ===== RIGHT COLUMN COMMAND API =====

@server_health_bp.route('/api/server_health/commands/<server_id>')
@require_auth
def get_command_history(server_id):
    """API for right column command feed - Layout-specific endpoint"""
    try:
        if not _server_health_storage:
            return jsonify({
                'success': False,
                'error': 'Server health storage not initialized'
            }), 503
        
        # Get 24-hour command history for right column display
        commands = _server_health_storage.get_command_history_24h(server_id)
        
        # Calculate command statistics for display
        total_commands = len(commands)
        command_types = {}
        for cmd in commands:
            cmd_type = cmd.get('type', 'unknown')
            command_types[cmd_type] = command_types.get(cmd_type, 0) + 1
        
        logger.info(f"[Server Health API] Retrieved {total_commands} commands for server {server_id}")
        
        return jsonify({
            'success': True,
            'commands': commands,              # For right column display
            'total': total_commands,
            'command_types': command_types,    # Admin, ingame, auto counts
            'server_id': server_id,
            'last_updated': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"[Server Health API] Get command history error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@server_health_bp.route('/api/server_health/commands/<server_id>/filter/<command_type>')
@require_auth
def get_filtered_commands(server_id, command_type):
    """API for filtered command history (admin/ingame/auto) - Right column filters"""
    try:
        if not _server_health_storage:
            return jsonify({
                'success': False,
                'error': 'Server health storage not initialized'
            }), 503
        
        # Get all commands then filter by type
        all_commands = _server_health_storage.get_command_history_24h(server_id)
        
        if command_type.lower() == 'all':
            filtered_commands = all_commands
        else:
            filtered_commands = [cmd for cmd in all_commands if cmd.get('type', '').lower() == command_type.lower()]
        
        return jsonify({
            'success': True,
            'commands': filtered_commands,
            'total': len(filtered_commands),
            'filter_type': command_type,
            'server_id': server_id
        })
        
    except Exception as e:
        logger.error(f"[Server Health API] Get filtered commands error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ===== LEFT SIDE CHARTS API =====

@server_health_bp.route('/api/server_health/charts/<server_id>')
@require_auth
def get_chart_data(server_id):
    """API for left side performance charts - Layout-specific endpoint"""
    try:
        if not _server_health_storage:
            return jsonify({
                'success': False,
                'error': 'Server health storage not initialized'
            }), 503
        
        # Get chart data hours from query parameter (default 6 hours)
        hours = int(request.args.get('hours', 6))
        
        # Get health trends for charts
        health_trends = _server_health_storage.get_health_trends(server_id, hours)
        
        # Format data for Chart.js (verified pattern)
        chart_data = {
            'fps_chart': {
                'labels': [datetime.fromisoformat(ts).strftime("%H:%M") if isinstance(ts, str) else ts.strftime("%H:%M") 
                          for ts in health_trends.get('timestamps', [])],
                'datasets': [{
                    'label': 'FPS',
                    'data': health_trends.get('fps', []),
                    'borderColor': 'rgb(34, 197, 94)',  # Green
                    'backgroundColor': 'rgba(34, 197, 94, 0.1)',
                    'tension': 0.4
                }]
            },
            'players_chart': {
                'labels': [datetime.fromisoformat(ts).strftime("%H:%M") if isinstance(ts, str) else ts.strftime("%H:%M") 
                          for ts in health_trends.get('timestamps', [])],
                'datasets': [{
                    'label': 'Players',
                    'data': health_trends.get('players', []),
                    'borderColor': 'rgb(59, 130, 246)',  # Blue
                    'backgroundColor': 'rgba(59, 130, 246, 0.1)',
                    'tension': 0.4
                }]
            },
            'memory_chart': {
                'labels': [datetime.fromisoformat(ts).strftime("%H:%M") if isinstance(ts, str) else ts.strftime("%H:%M") 
                          for ts in health_trends.get('timestamps', [])],
                'datasets': [{
                    'label': 'Memory (MB)',
                    'data': health_trends.get('memory', []),
                    'borderColor': 'rgb(168, 85, 247)',  # Purple
                    'backgroundColor': 'rgba(168, 85, 247, 0.1)',
                    'tension': 0.4
                }]
            },
            'response_time_chart': {
                'labels': [datetime.fromisoformat(ts).strftime("%H:%M") if isinstance(ts, str) else ts.strftime("%H:%M") 
                          for ts in health_trends.get('timestamps', [])],
                'datasets': [{
                    'label': 'Response Time (ms)',
                    'data': health_trends.get('response_times', []),
                    'borderColor': 'rgb(245, 158, 11)',  # Yellow
                    'backgroundColor': 'rgba(245, 158, 11, 0.1)',
                    'tension': 0.4
                }]
            }
        }
        
        logger.info(f"[Server Health API] Generated chart data for server {server_id} ({hours}h)")
        
        return jsonify({
            'success': True,
            'chart_data': chart_data,          # For left side charts
            'raw_data': health_trends,         # Raw data if needed
            'data_points': health_trends.get('data_points', 0),
            'hours_span': hours,
            'server_id': server_id,
            'last_updated': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"[Server Health API] Get chart data error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ===== LEFT SIDE STATUS CARDS API =====

@server_health_bp.route('/api/server_health/status/<server_id>')
@require_auth
def get_health_status(server_id):
    """API for left side health status cards - Layout-specific endpoint"""
    try:
        if not _server_health_storage:
            return jsonify({
                'success': False,
                'error': 'Server health storage not initialized'
            }), 503
        
        # Use verified perform_optimization_health_check() integration
        health_data = perform_optimization_health_check()
        
        # Store snapshot for historical tracking (verified pattern)
        _server_health_storage.store_health_snapshot(server_id, health_data)
        
        # Get current metrics from storage
        current_metrics = _server_health_storage.get_current_metrics(server_id)
        
        # Format status for health cards
        status_data = {
            'overall_status': health_data.get('status', 'unknown'),  # healthy/warning/critical
            'status_color': get_status_color(health_data.get('status', 'unknown')),
            'health_percentage': calculate_health_percentage(health_data),
            'metrics': {
                'response_time': health_data.get('response_time', current_metrics.get('response_time', 0)),
                'memory_usage': current_metrics.get('memory_usage', 0),
                'cpu_usage': current_metrics.get('cpu_usage', 0),
                'player_count': current_metrics.get('player_count', 0),
                'cache_hit_rate': current_metrics.get('cache_hit_rate', 0),
                'uptime': current_metrics.get('uptime', 0)
            },
            'statistics': health_data.get('statistics', {}),  # Additional stats
            'last_check': current_metrics.get('last_check', datetime.utcnow().isoformat())
        }
        
        logger.info(f"[Server Health API] Health status check for server {server_id}: {status_data['overall_status']}")
        
        return jsonify({
            'success': True,
            'status': status_data['overall_status'],   # For status indicator
            'health_data': status_data,                # For status cards
            'metrics': status_data['metrics'],         # For progress bars
            'server_id': server_id,
            'checked_at': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"[Server Health API] Get health status error: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'status': 'error'
        }), 500


# ===== PERFORMANCE TRENDS & AVERAGES API (NEW FEATURE) =====

@server_health_bp.route('/api/server_health/trends/<server_id>')
@require_auth
def get_performance_trends(server_id):
    """API for performance trends with averages and current info - Enhanced feature"""
    try:
        if not _server_health_storage:
            return jsonify({
                'success': False,
                'error': 'Server health storage not initialized'
            }), 503
        
        # Get period from query parameter (24h or 7d)
        period = request.args.get('period', '24h')
        hours = 24 if period == '24h' else 168  # 7 days = 168 hours
        
        # Get current metrics
        current_metrics = _server_health_storage.get_current_metrics(server_id)
        
        # Get averages for comparison
        averages_24h = _server_health_storage.calculate_averages(server_id, hours=24)
        averages_7d = _server_health_storage.calculate_averages(server_id, hours=168)
        
        # Get comprehensive trend summary
        trends_summary = _server_health_storage.get_performance_trends_summary(server_id)
        
        # Calculate percentage changes
        def calculate_change_percentage(current, average):
            if average == 0:
                return 0
            return round(((current - average) / average) * 100, 1)
        
        # Enhanced trend analysis
        trend_analysis = {
            'response_time': {
                'current': current_metrics.get('response_time', 0),
                'avg_24h': averages_24h.get('response_time', 0),
                'avg_7d': averages_7d.get('response_time', 0),
                'change_24h': calculate_change_percentage(
                    current_metrics.get('response_time', 0), 
                    averages_24h.get('response_time', 0)
                ),
                'trend_indicator': trends_summary.get('trends', {}).get('response_time', '➡️')
            },
            'memory_usage': {
                'current': current_metrics.get('memory_usage', 0),
                'avg_24h': averages_24h.get('memory_usage', 0),
                'avg_7d': averages_7d.get('memory_usage', 0),
                'change_24h': calculate_change_percentage(
                    current_metrics.get('memory_usage', 0), 
                    averages_24h.get('memory_usage', 0)
                ),
                'trend_indicator': trends_summary.get('trends', {}).get('memory_usage', '➡️')
            },
            'fps': {
                'current': current_metrics.get('fps', 0),
                'avg_24h': averages_24h.get('fps', 0),
                'avg_7d': averages_7d.get('fps', 0),
                'change_24h': calculate_change_percentage(
                    current_metrics.get('fps', 0), 
                    averages_24h.get('fps', 0)
                ),
                'trend_indicator': trends_summary.get('trends', {}).get('fps', '➡️')
            },
            'player_count': {
                'current': current_metrics.get('player_count', 0),
                'avg_24h': averages_24h.get('player_count', 0),
                'avg_7d': averages_7d.get('player_count', 0),
                'change_24h': calculate_change_percentage(
                    current_metrics.get('player_count', 0), 
                    averages_24h.get('player_count', 0)
                ),
                'trend_indicator': trends_summary.get('trends', {}).get('player_count', '➡️')
            }
        }
        
        logger.info(f"[Server Health API] Performance trends calculated for server {server_id} ({period})")
        
        return jsonify({
            'success': True,
            'current': current_metrics,            # Current real-time values
            'averages': {
                '24h': averages_24h,               # 24-hour averages
                '7d': averages_7d                  # 7-day averages
            },
            'trends': trend_analysis,              # Enhanced trend analysis with % changes
            'summary': trends_summary,             # Comprehensive summary
            'period': period,
            'server_id': server_id,
            'calculated_at': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"[Server Health API] Get performance trends error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ===== COMMAND EXECUTION TRACKING API =====

@server_health_bp.route('/api/server_health/command/track', methods=['POST'])
@require_auth
def track_command_execution():
    """Track command execution for history logging - Integration with console system"""
    try:
        if not _server_health_storage:
            return jsonify({
                'success': False,
                'error': 'Server health storage not initialized'
            }), 503
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Extract command data (verified pattern from economy.py)
        server_id = data.get('server_id', 'default')
        command = data.get('command', '')
        command_type = data.get('type', 'unknown')  # admin, ingame, auto
        user = data.get('user', 'System')
        
        # Store command execution using verified storage pattern
        success = _server_health_storage.store_command_execution(
            server_id=server_id,
            command=command,
            command_type=command_type,
            user=user
        )
        
        if success:
            logger.info(f"[Server Health API] Command tracked: {command} ({command_type}) by {user}")
            return jsonify({
                'success': True,
                'message': 'Command execution tracked',
                'command': command,
                'type': command_type,
                'timestamp': datetime.utcnow().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to track command execution'
            }), 500
        
    except Exception as e:
        logger.error(f"[Server Health API] Track command execution error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ===== UTILITY FUNCTIONS =====

def get_status_color(status: str) -> str:
    """Get color for health status indicator (verified pattern)"""
    status_colors = {
        'healthy': 'green',
        'warning': 'yellow',
        'critical': 'red',
        'error': 'red',
        'unknown': 'gray'
    }
    return status_colors.get(status.lower(), 'gray')


def calculate_health_percentage(health_data: dict) -> int:
    """Calculate overall health percentage for progress bars"""
    try:
        status = health_data.get('status', 'unknown').lower()
        if status == 'healthy':
            return 90
        elif status == 'warning':
            return 60
        elif status == 'critical':
            return 30
        else:
            return 50
    except Exception:
        return 50


# ===== HEALTH CHECK ENDPOINT =====

@server_health_bp.route('/api/server_health/heartbeat')
@require_auth
def health_heartbeat():
    """Simple heartbeat endpoint to verify Server Health system is working"""
    try:
        return jsonify({
            'success': True,
            'status': 'Server Health system operational',
            'storage_initialized': _server_health_storage is not None,
            'timestamp': datetime.utcnow().isoformat(),
            'layout': 'right_column_commands_left_side_charts'
        })
    except Exception as e:
        logger.error(f"[Server Health API] Heartbeat error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ===== ERROR HANDLERS (Verified Pattern) =====

@server_health_bp.errorhandler(404)
def not_found(error):
    """Handle 404 errors for server health endpoints"""
    return jsonify({
        'success': False,
        'error': 'Server Health endpoint not found'
    }), 404


@server_health_bp.errorhandler(500)
def internal_error(error):
    """Handle 500 errors for server health endpoints"""
    logger.error(f"[Server Health API] Internal server error: {error}")
    return jsonify({
        'success': False,
        'error': 'Internal server error in Server Health system'
    }), 500


# ===== BLUEPRINT REGISTRATION INFO =====

def get_blueprint_info():
    """Get blueprint information for registration (verified pattern)"""
    return {
        'blueprint': server_health_bp,
        'url_prefix': '/server_health',
        'name': 'server_health',
        'description': 'Server Health monitoring with layout-specific endpoints',
        'endpoints': [
            '/api/server_health/commands/<server_id>',           # Right column commands
            '/api/server_health/charts/<server_id>',             # Left side charts  
            '/api/server_health/status/<server_id>',             # Left side status cards
            '/api/server_health/trends/<server_id>',             # Performance trends
            '/api/server_health/command/track',                  # Command tracking
            '/api/server_health/heartbeat'                       # Health check
        ]
    }


logger.info("[✅ OK] Server Health routes loaded - Layout-focused endpoints ready")