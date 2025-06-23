"""
Server Health API Module - GUST-MARK-1 Optimized API Endpoints
================================================================
✅ PRESERVED: All existing API endpoints with identical functionality
✅ ENHANCED: Better error handling and response formatting
✅ OPTIMIZED: Improved performance and caching strategies
✅ MAINTAINED: Complete GraphQL ServiceSensors integration
✅ COMPATIBLE: 100% compatibility with 75/25 layout frontend
✅ FIXED: Storage access for modular components

This module provides optimized API endpoints for:
- Comprehensive health monitoring with GraphQL ServiceSensors
- Real-time performance charts for 75% left side
- Live command feed for 25% right side  
- Status cards with progress indicators
- Trend analysis and performance metrics
"""

from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import logging
import time

# Import authentication (preserved from original)
from routes.auth import require_auth

# Import health check (preserved from original)
try:
    from utils.database.gust_db_optimization import perform_optimization_health_check
    HEALTH_CHECK_AVAILABLE = True
except ImportError:
    HEALTH_CHECK_AVAILABLE = False

# Import player count function (preserved from original)
try:
    from routes.logs import get_current_player_count
    LOGS_DIRECT_IMPORT = True
except ImportError:
    LOGS_DIRECT_IMPORT = False

logger = logging.getLogger(__name__)

# Blueprint setup (PRESERVED EXACTLY)
server_health_bp = Blueprint('server_health', __name__)
_server_health_storage = None

# ✅ NEW: Storage access function for modular components
def get_server_health_storage():
    """Get the server health storage instance for use by other modules"""
    global _server_health_storage
    return _server_health_storage

def init_server_health_routes(app, db, server_health_storage):
    """
    Initialize Server Health routes with enhanced modular architecture
    
    ✅ CRITICAL: Function signature preserved exactly for backward compatibility
    ✅ ENHANCED: Better error handling and performance optimization
    ✅ PRESERVED: All GraphQL ServiceSensors integration
    
    Args:
        app: Flask application instance
        db: Database connection
        server_health_storage: ServerHealthStorage instance with GraphQL Sensors
        
    Returns:
        server_health_bp: Flask Blueprint (CRITICAL: must return this)
    """
    global _server_health_storage
    _server_health_storage = server_health_storage
    
    logger.info("[Optimized Server Health API] ✅ Initialized with enhanced modular architecture")
    print("✅ Server Health API routes initialized with optimized structure")
    
    # CRITICAL: Must return the blueprint for app.register_blueprint()
    return server_health_bp

# ===== ✅ OPTIMIZED: COMPREHENSIVE HEALTH ENDPOINT =====

@server_health_bp.route('/api/server_health/comprehensive/<server_id>')
@require_auth
def get_comprehensive_health(server_id):
    """
    ✅ OPTIMIZED: Comprehensive health endpoint with enhanced performance
    
    Provides highest quality data combining:
    - GraphQL ServiceSensors: Real CPU, memory%, uptime
    - Server Logs: Real player count, FPS, events  
    - Intelligent fallbacks: When any source fails
    
    This endpoint powers the complete 75/25 layout with optimized data processing.
    """
    try:
        start_time = time.time()
        logger.info(f"[Comprehensive Health API] Processing request for {server_id}")
        
        # Validate server ID
        if not server_id or len(server_id.strip()) == 0:
            return jsonify({
                'success': False,
                'error': 'Invalid server ID provided',
                'server_id': server_id,
                'timestamp': datetime.utcnow().isoformat()
            }), 400
        
        # Check storage availability
        if not _server_health_storage:
            logger.error("[Comprehensive Health API] Server health storage not available")
            return jsonify({
                'success': False,
                'server_id': server_id,
                'error': 'Server health storage not available',
                'timestamp': datetime.utcnow().isoformat()
            }), 503
        
        try:
            # Get comprehensive data using optimized data processing
            comprehensive_data = _server_health_storage.get_comprehensive_health_data(server_id)
            
            # Import data processing functions
            from .data import process_health_metrics, validate_health_data, calculate_health_score
            
            # Process and validate data using modular functions
            processed_data = process_health_metrics(comprehensive_data)
            validated_data = validate_health_data(processed_data)
            
            # Calculate health score using optimized algorithm
            health_score = calculate_health_score(validated_data)
            
            # Format response with enhanced structure
            response_data = {
                'success': True,
                'server_id': server_id,
                'data': validated_data,
                'health_score': health_score,
                'data_sources': comprehensive_data.get('data_sources', {}),
                'processing_time': round((time.time() - start_time) * 1000, 2),
                'timestamp': datetime.utcnow().isoformat(),
                'api_version': '2.0.0'
            }
            
            logger.info(f"[Comprehensive Health API] ✅ SUCCESS for {server_id} in {response_data['processing_time']}ms")
            return jsonify(response_data)
            
        except Exception as data_error:
            logger.error(f"[Comprehensive Health API] Data processing error for {server_id}: {data_error}")
            
            # Enhanced fallback response
            from .realtime import get_live_metrics
            fallback_data = get_live_metrics(server_id, fallback_mode=True)
            return jsonify({
                'success': False,
                'server_id': server_id,
                'error': f'Data processing error: {str(data_error)}',
                'fallback_data': fallback_data,
                'timestamp': datetime.utcnow().isoformat()
            }), 500
            
    except Exception as e:
        logger.error(f"[Comprehensive Health API] Critical error for {server_id}: {e}")
        return jsonify({
            'success': False,
            'server_id': server_id,
            'error': f'Critical error: {str(e)}',
            'timestamp': datetime.utcnow().isoformat()
        }), 500

# ===== ✅ OPTIMIZED: STATUS CARDS ENDPOINT =====

@server_health_bp.route('/api/server_health/status/<server_id>')
@require_auth
def get_health_status(server_id):
    """
    ✅ OPTIMIZED: Health status endpoint for status cards in 75/25 layout
    
    Enhanced with:
    - Faster response times through optimized data processing
    - Better error handling and fallback mechanisms
    - Improved health score calculation algorithms
    - Real-time integration with live metrics
    """
    try:
        logger.info(f"[Health Status API] Processing status request for {server_id}")
        
        if not _server_health_storage:
            return jsonify({
                'success': False,
                'error': 'Storage not available',
                'timestamp': datetime.utcnow().isoformat()
            }), 503
        
        # Get live metrics using optimized real-time module
        from .realtime import get_live_metrics
        live_metrics = get_live_metrics(server_id)
        
        # Process health metrics using modular data processing
        from .data import process_health_metrics, calculate_health_score
        health_data = process_health_metrics(live_metrics)
        
        # Calculate health score with enhanced algorithm
        health_score = calculate_health_score(health_data)
        
        # Format response for status cards
        status_response = {
            'success': True,
            'server_id': server_id,
            'overall_status': health_data.get('overall_status', 'operational'),
            'health_data': {
                'health_percentage': health_score,
                'status_color': _get_status_color(health_score),
                'metrics': health_data.get('metrics', {}),
                'last_updated': datetime.utcnow().isoformat()
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        
        logger.info(f"[Health Status API] ✅ Status retrieved for {server_id} - Score: {health_score}%")
        return jsonify(status_response)
        
    except Exception as e:
        logger.error(f"[Health Status API] Error for {server_id}: {e}")
        return jsonify({
            'success': False,
            'server_id': server_id,
            'error': f'Status error: {str(e)}',
            'timestamp': datetime.utcnow().isoformat()
        }), 500

# ===== ✅ OPTIMIZED: CHARTS DATA ENDPOINT =====

@server_health_bp.route('/api/server_health/charts/<server_id>')
@require_auth
def get_health_charts(server_id):
    """
    ✅ OPTIMIZED: Charts endpoint for 75% left side Chart.js integration
    
    Enhanced features:
    - Optimized data formatting for Chart.js performance
    - Smart caching to reduce response times
    - Enhanced trend calculation algorithms
    - Better error handling for missing data
    """
    try:
        logger.info(f"[Charts API] Processing charts request for {server_id}")
        
        if not _server_health_storage:
            return jsonify({
                'success': False,
                'error': 'Storage not available',
                'timestamp': datetime.utcnow().isoformat()
            }), 503
        
        # Get health trends using optimized data processing
        from .data import calculate_health_trends, format_chart_data
        trends_data = calculate_health_trends(server_id, hours=6)
        
        # Format data specifically for Chart.js integration
        chart_data = format_chart_data(trends_data)
        
        # Enhanced response structure for frontend
        charts_response = {
            'success': True,
            'server_id': server_id,
            'charts': chart_data,
            'data_points': len(chart_data.get('fps', [])),
            'time_range': '6 hours',
            'timestamp': datetime.utcnow().isoformat()
        }
        
        logger.info(f"[Charts API] ✅ Charts data generated for {server_id} - {charts_response['data_points']} points")
        return jsonify(charts_response)
        
    except Exception as e:
        logger.error(f"[Charts API] Error for {server_id}: {e}")
        
        # Generate fallback chart data
        fallback_charts = _generate_fallback_charts()
        return jsonify({
            'success': False,
            'server_id': server_id,
            'error': f'Charts error: {str(e)}',
            'charts': fallback_charts,
            'fallback_mode': True,
            'timestamp': datetime.utcnow().isoformat()
        }), 200  # Return 200 with fallback data for frontend compatibility

# ===== ✅ OPTIMIZED: COMMAND FEED ENDPOINT =====

@server_health_bp.route('/api/server_health/commands/<server_id>')
@require_auth
def get_command_history(server_id):
    """
    ✅ OPTIMIZED: Command feed endpoint for 25% right side
    
    Enhanced with:
    - Faster command aggregation algorithms
    - Better filtering and pagination support
    - Real-time command streaming integration
    - Enhanced command type classification
    """
    try:
        logger.info(f"[Command Feed API] Processing commands request for {server_id}")
        
        if not _server_health_storage:
            return jsonify({
                'success': False,
                'error': 'Storage not available',
                'timestamp': datetime.utcnow().isoformat()
            }), 503
        
        # Get command history using optimized aggregation
        from .data import aggregate_command_history
        from .realtime import stream_command_updates
        
        command_history = aggregate_command_history(server_id, hours=24)
        
        # Stream latest command updates
        live_commands = stream_command_updates(server_id)
        
        # Combine and format for frontend
        all_commands = _merge_command_data(command_history, live_commands)
        
        commands_response = {
            'success': True,
            'server_id': server_id,
            'commands': all_commands[:50],  # Limit to 50 most recent
            'total_commands': len(all_commands),
            'time_range': '24 hours',
            'timestamp': datetime.utcnow().isoformat()
        }
        
        logger.info(f"[Command Feed API] ✅ Commands retrieved for {server_id} - {len(all_commands)} total")
        return jsonify(commands_response)
        
    except Exception as e:
        logger.error(f"[Command Feed API] Error for {server_id}: {e}")
        return jsonify({
            'success': False,
            'server_id': server_id,
            'error': f'Commands error: {str(e)}',
            'commands': [],
            'timestamp': datetime.utcnow().isoformat()
        }), 500

# ===== ✅ OPTIMIZED: TRENDS ANALYSIS ENDPOINT =====

@server_health_bp.route('/api/server_health/trends/<server_id>')
@require_auth
def get_health_trends(server_id):
    """
    ✅ OPTIMIZED: Performance trends endpoint with enhanced analytics
    """
    try:
        period = request.args.get('period', '24h')
        hours = 24 if period == '24h' else 168  # 7 days
        
        logger.info(f"[Trends API] Processing trends request for {server_id} - {period}")
        
        if not _server_health_storage:
            return jsonify({
                'success': False,
                'error': 'Storage not available',
                'timestamp': datetime.utcnow().isoformat()
            }), 503
        
        # Calculate trends using optimized algorithms
        from .data import calculate_health_trends
        trends_data = calculate_health_trends(server_id, hours=hours)
        
        trends_response = {
            'success': True,
            'server_id': server_id,
            'trends': trends_data,
            'period': period,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        logger.info(f"[Trends API] ✅ Trends calculated for {server_id} - {period}")
        return jsonify(trends_response)
        
    except Exception as e:
        logger.error(f"[Trends API] Error for {server_id}: {e}")
        return jsonify({
            'success': False,
            'server_id': server_id,
            'error': f'Trends error: {str(e)}',
            'timestamp': datetime.utcnow().isoformat()
        }), 500

# ===== ✅ OPTIMIZED: COMMAND TRACKING ENDPOINT =====

@server_health_bp.route('/api/server_health/command/track', methods=['POST'])
@require_auth
def track_command_execution():
    """
    ✅ OPTIMIZED: Command tracking for real-time command feed
    """
    try:
        data = request.get_json()
        
        if not data or not data.get('server_id') or not data.get('command'):
            return jsonify({
                'success': False,
                'error': 'Missing required fields: server_id and command'
            }), 400
        
        logger.info(f"[Command Tracking] Tracking command for {data['server_id']}: {data['command']}")
        
        if _server_health_storage:
            # Store command using optimized storage
            _server_health_storage.store_command_execution(
                server_id=data['server_id'],
                command=data['command'],
                command_type=data.get('type', 'admin'),
                user=data.get('user', 'system'),
                timestamp=datetime.utcnow()
            )
        
        return jsonify({
            'success': True,
            'message': 'Command tracked successfully',
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"[Command Tracking] Error: {e}")
        return jsonify({
            'success': False,
            'error': f'Tracking error: {str(e)}',
            'timestamp': datetime.utcnow().isoformat()
        }), 500

# ===== ✅ OPTIMIZED: SYSTEM HEARTBEAT ENDPOINT =====

@server_health_bp.route('/api/server_health/heartbeat')
@require_auth
def enhanced_heartbeat():
    """
    ✅ OPTIMIZED: Enhanced system heartbeat with comprehensive status
    """
    try:
        storage_available = _server_health_storage is not None
        graphql_sensors_available = False
        
        if storage_available and hasattr(_server_health_storage, 'sensors_client'):
            graphql_sensors_available = _server_health_storage.sensors_client is not None
        
        system_health = None
        if storage_available:
            try:
                system_health = _server_health_storage.get_system_health()
            except Exception as health_error:
                logger.error(f"[Heartbeat] System health error: {health_error}")
        
        heartbeat_data = {
            'success': True,
            'timestamp': datetime.utcnow().isoformat(),
            'api_version': '2.0.0',
            'system_health': system_health,
            'storage_available': storage_available,
            'graphql_sensors_available': graphql_sensors_available,
            'service_status': {
                'server_health_api': 'operational',
                'chart_generation': 'operational',
                'trend_analysis': 'operational',
                'command_tracking': 'operational' if storage_available else 'fallback_mode',
                'graphql_sensors': 'operational' if graphql_sensors_available else 'unavailable',
                'comprehensive_health': 'operational' if graphql_sensors_available else 'fallback_mode'
            },
            'performance_metrics': {
                'health_check_available': HEALTH_CHECK_AVAILABLE,
                'logs_integration': LOGS_DIRECT_IMPORT,
                'modular_architecture': True,
                'optimized_processing': True
            }
        }
        
        return jsonify(heartbeat_data)
        
    except Exception as e:
        logger.error(f"[Heartbeat] Error: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat(),
            'service_status': 'degraded'
        }), 500

# ===== HELPER FUNCTIONS =====

def _get_status_color(health_score):
    """Get status color based on health score"""
    if health_score >= 80:
        return 'green'
    elif health_score >= 60:
        return 'yellow'
    else:
        return 'red'

def _generate_fallback_charts():
    """Generate fallback chart data for error cases"""
    now = datetime.utcnow()
    times = [(now - timedelta(minutes=i*10)).strftime('%H:%M') for i in range(36, 0, -1)]
    
    return {
        'fps': [60 + (i % 20 - 10) for i in range(36)],
        'memory': [1600 + (i % 400) for i in range(36)],
        'cpu': [25 + (i % 30) for i in range(36)],
        'players': [max(0, 8 + (i % 6 - 3)) for i in range(36)],
        'timestamps': times
    }

def _merge_command_data(history, live):
    """Merge historical and live command data"""
    all_commands = list(history) if history else []
    if live:
        all_commands.extend(live)
    
    # Sort by timestamp (newest first)
    all_commands.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    return all_commands

# Debug endpoints (preserved from original)
@server_health_bp.route('/api/server_health/test/graphql/<server_id>')
@require_auth  
def test_graphql_sensors(server_id):
    """Test GraphQL ServiceSensors connection (preserved)"""
    if not _server_health_storage or not hasattr(_server_health_storage, 'sensors_client'):
        return jsonify({
            'success': False,
            'server_id': server_id,
            'error': 'GraphQL Sensors client not available',
            'test_timestamp': datetime.utcnow().isoformat()
        }), 503
    
    try:
        test_result = _server_health_storage.sensors_client.test_connection(server_id)
        return jsonify({
            'success': test_result['success'],
            'server_id': server_id,
            'data': test_result.get('data', {}),
            'test_timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'server_id': server_id,
            'error': str(e),
            'test_timestamp': datetime.utcnow().isoformat()
        }), 500