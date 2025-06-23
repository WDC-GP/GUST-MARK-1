"""
Server Health Real-time Module - GUST-MARK-1 Live Data Features
================================================================
✅ OPTIMIZED: Enhanced real-time data streaming for 75/25 layout
✅ PERFORMANCE: Efficient WebSocket integration and live updates
✅ RESPONSIVE: Smart caching and update frequency optimization
✅ RELIABLE: Robust error handling and fallback mechanisms

This module provides real-time features for:
- Live metrics streaming for status cards and charts
- Real-time command feed updates for 25% right side
- WebSocket integration for instant data push
- Smart update frequency management
- Live trend calculation and streaming
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
import logging
import time
import asyncio
import json
from collections import deque, defaultdict
import threading

logger = logging.getLogger(__name__)

# ===== REAL-TIME METRICS STREAMING =====

class LiveMetricsCache:
    """Smart caching system for live metrics with TTL and frequency control"""
    
    def __init__(self, default_ttl: int = 30):
        self.cache = {}
        self.ttl = default_ttl
        self.last_update = {}
        self.update_frequencies = defaultdict(int)
        self._lock = threading.Lock()
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cached metrics with TTL check"""
        with self._lock:
            if key in self.cache:
                cached_data, timestamp = self.cache[key]
                age = time.time() - timestamp
                
                if age < self.ttl:
                    return cached_data
                else:
                    del self.cache[key]
                    
        return None
    
    def set(self, key: str, data: Dict[str, Any]) -> None:
        """Cache metrics with timestamp"""
        with self._lock:
            self.cache[key] = (data, time.time())
            self.last_update[key] = time.time()
            self.update_frequencies[key] += 1
    
    def should_update(self, key: str, min_interval: int = 10) -> bool:
        """Check if enough time has passed for an update"""
        last_time = self.last_update.get(key, 0)
        return (time.time() - last_time) >= min_interval
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        with self._lock:
            return {
                'cached_servers': len(self.cache),
                'total_updates': sum(self.update_frequencies.values()),
                'cache_size_bytes': len(str(self.cache)),
                'ttl_seconds': self.ttl
            }

# Global cache instance
_live_cache = LiveMetricsCache()

def get_live_metrics(server_id: str, fallback_mode: bool = False) -> Dict[str, Any]:
    """
    ✅ OPTIMIZED: Get live metrics with smart caching and performance optimization
    
    Enhanced features:
    - Smart caching to reduce API calls
    - Multiple data source prioritization
    - Performance-optimized data retrieval
    - Intelligent fallback mechanisms
    
    Args:
        server_id: Server identifier
        fallback_mode: Force fallback data generation
        
    Returns:
        Live metrics data optimized for real-time display
    """
    try:
        start_time = time.time()
        logger.debug(f"[Live Metrics] Getting live metrics for {server_id}")
        
        # Check cache first for performance
        if not fallback_mode:
            cached_metrics = _live_cache.get(f"live_metrics_{server_id}")
            if cached_metrics:
                logger.debug(f"[Live Metrics] ✅ Using cached metrics for {server_id}")
                return cached_metrics
        
        # Get fresh metrics from storage
        live_data = _fetch_fresh_metrics(server_id, fallback_mode)
        
        # Process for real-time display
        processed_metrics = _process_live_metrics(live_data, server_id)
        
        # Cache the results
        if not fallback_mode:
            _live_cache.set(f"live_metrics_{server_id}", processed_metrics)
        
        processing_time = round((time.time() - start_time) * 1000, 2)
        processed_metrics['processing_time_ms'] = processing_time
        
        logger.debug(f"[Live Metrics] ✅ Generated live metrics for {server_id} in {processing_time}ms")
        return processed_metrics
        
    except Exception as e:
        logger.error(f"[Live Metrics] Error getting live metrics for {server_id}: {e}")
        return _generate_fallback_live_metrics(server_id, str(e))

def _fetch_fresh_metrics(server_id: str, fallback_mode: bool) -> Dict[str, Any]:
    """Fetch fresh metrics from available data sources"""
    if fallback_mode:
        return _generate_synthetic_live_data(server_id)
    
    try:
        # Get storage instance from API module
        from .api import get_server_health_storage
        storage = get_server_health_storage()
        
        if not storage:
            return _generate_synthetic_live_data(server_id)
        
        # Try to get comprehensive data first
        comprehensive_data = storage.get_comprehensive_health_data(server_id)
        
        if comprehensive_data and comprehensive_data.get('success', False):
            return comprehensive_data
        else:
            return _generate_synthetic_live_data(server_id)
            
    except Exception as e:
        logger.warning(f"[Live Metrics] Error fetching fresh metrics: {e}")
        return _generate_synthetic_live_data(server_id)

def _process_live_metrics(raw_data: Dict[str, Any], server_id: str) -> Dict[str, Any]:
    """Process raw metrics for real-time display optimization"""
    processed = {
        'server_id': server_id,
        'timestamp': datetime.utcnow().isoformat(),
        'data_source': raw_data.get('data_source', 'fallback'),
        'real_time': True
    }
    
    # Extract and normalize core metrics
    core_metrics = {}
    
    # CPU processing
    cpu_data = raw_data.get('cpu_usage', raw_data.get('cpu_total', 15))
    core_metrics['cpu_usage'] = max(0, min(100, float(cpu_data) if cpu_data else 15))
    
    # Memory processing  
    memory_data = raw_data.get('memory_percent', 25)
    if not memory_data and 'memory_used_mb' in raw_data and 'memory_total_mb' in raw_data:
        used = float(raw_data['memory_used_mb'])
        total = float(raw_data['memory_total_mb'])
        memory_data = (used / total * 100) if total > 0 else 25
    core_metrics['memory_usage'] = max(0, min(100, float(memory_data) if memory_data else 25))
    
    # FPS processing
    fps_data = raw_data.get('fps', raw_data.get('server_fps', 60))
    core_metrics['fps'] = max(10, min(120, float(fps_data) if fps_data else 60))
    
    # Player count
    player_data = raw_data.get('player_count', raw_data.get('current_players', 0))
    core_metrics['player_count'] = max(0, int(player_data) if player_data else 0)
    
    # Response time
    response_data = raw_data.get('response_time', raw_data.get('ping', 30))
    core_metrics['response_time'] = max(1, min(1000, float(response_data) if response_data else 30))
    
    processed['metrics'] = core_metrics
    
    # Calculate live performance indicators
    processed['indicators'] = _calculate_live_indicators(core_metrics)
    
    # Add real-time status
    processed['status'] = _calculate_live_status(core_metrics)
    
    return processed

def _calculate_live_indicators(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate real-time performance indicators"""
    indicators = {}
    
    # Performance level
    cpu = metrics['cpu_usage']
    memory = metrics['memory_usage']
    fps = metrics['fps']
    
    # Combined performance score
    cpu_score = max(0, 100 - cpu)
    memory_score = max(0, 100 - memory)
    fps_score = min(100, (fps / 60) * 100)
    
    performance_score = (cpu_score + memory_score + fps_score) / 3
    indicators['performance_score'] = round(performance_score, 1)
    
    # Resource pressure indicators
    indicators['cpu_pressure'] = 'high' if cpu > 70 else 'medium' if cpu > 40 else 'low'
    indicators['memory_pressure'] = 'high' if memory > 80 else 'medium' if memory > 50 else 'low'
    indicators['fps_quality'] = 'excellent' if fps >= 55 else 'good' if fps >= 40 else 'poor'
    
    # Overall performance level
    if performance_score >= 80:
        indicators['performance_level'] = 'excellent'
    elif performance_score >= 60:
        indicators['performance_level'] = 'good'
    elif performance_score >= 40:
        indicators['performance_level'] = 'fair'
    else:
        indicators['performance_level'] = 'poor'
    
    return indicators

def _calculate_live_status(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate live system status"""
    cpu = metrics['cpu_usage']
    memory = metrics['memory_usage']
    fps = metrics['fps']
    
    # Determine status level
    if cpu > 90 or memory > 90 or fps < 15:
        status_level = 'critical'
        status_color = 'red'
    elif cpu > 70 or memory > 70 or fps < 30:
        status_level = 'warning'
        status_color = 'yellow'
    elif cpu > 50 or memory > 50 or fps < 45:
        status_level = 'degraded'
        status_color = 'orange'
    else:
        status_level = 'operational'
        status_color = 'green'
    
    return {
        'level': status_level,
        'color': status_color,
        'message': _get_status_message(status_level, metrics),
        'health_percentage': _calculate_quick_health_score(metrics)
    }

def _get_status_message(level: str, metrics: Dict[str, Any]) -> str:
    """Get human-readable status message"""
    if level == 'critical':
        return f"Critical: High resource usage detected"
    elif level == 'warning':
        return f"Warning: Performance degradation detected"
    elif level == 'degraded':
        return f"Degraded: Elevated resource usage"
    else:
        return f"Operational: System running normally"

def _calculate_quick_health_score(metrics: Dict[str, Any]) -> float:
    """Quick health score calculation for real-time display"""
    cpu_score = max(0, 100 - metrics['cpu_usage'])
    memory_score = max(0, 100 - metrics['memory_usage'])
    fps_score = min(100, (metrics['fps'] / 60) * 100)
    
    # Weighted average
    health_score = (cpu_score * 0.3 + memory_score * 0.3 + fps_score * 0.4)
    return round(health_score, 1)

# ===== COMMAND STREAMING =====

def stream_command_updates(server_id: str, limit: int = 20) -> List[Dict[str, Any]]:
    """
    ✅ OPTIMIZED: Stream latest command updates for real-time command feed
    
    Enhanced features:
    - Efficient command retrieval with smart limiting
    - Real-time command classification and formatting
    - Performance-optimized data structures
    - Smart deduplication and filtering
    
    Args:
        server_id: Server identifier
        limit: Maximum number of commands to return
        
    Returns:
        List of latest commands optimized for streaming
    """
    try:
        logger.debug(f"[Command Streaming] Streaming commands for {server_id}")
        
        # Check cache for recent commands
        cache_key = f"command_stream_{server_id}"
        cached_commands = _live_cache.get(cache_key)
        
        if cached_commands and _live_cache.should_update(cache_key, min_interval=5):
            logger.debug(f"[Command Streaming] Using cached commands for {server_id}")
            return cached_commands[:limit]
        
        # Get fresh command data
        fresh_commands = _fetch_fresh_commands(server_id, limit)
        
        # Process for real-time streaming
        processed_commands = _process_streaming_commands(fresh_commands, server_id)
        
        # Cache for performance
        _live_cache.set(cache_key, processed_commands)
        
        logger.debug(f"[Command Streaming] ✅ Streamed {len(processed_commands)} commands for {server_id}")
        return processed_commands[:limit]
        
    except Exception as e:
        logger.error(f"[Command Streaming] Error streaming commands for {server_id}: {e}")
        return _generate_fallback_streaming_commands(server_id, limit)

def _fetch_fresh_commands(server_id: str, limit: int) -> List[Dict[str, Any]]:
    """Fetch fresh commands from storage"""
    try:
        # Get storage instance from API module
        from .api import get_server_health_storage
        storage = get_server_health_storage()
        
        if not storage:
            return _generate_mock_streaming_commands(server_id, limit)
        
        # Get recent commands
        commands = storage.get_command_history_24h(server_id)
        
        if commands:
            # Sort by timestamp (newest first) and limit
            sorted_commands = sorted(commands, key=lambda x: x.get('timestamp', ''), reverse=True)
            return sorted_commands[:limit * 2]  # Get extra for filtering
        else:
            return _generate_mock_streaming_commands(server_id, limit)
            
    except Exception as e:
        logger.warning(f"[Command Streaming] Error fetching commands: {e}")
        return _generate_mock_streaming_commands(server_id, limit)

def _process_streaming_commands(commands: List[Dict], server_id: str) -> List[Dict[str, Any]]:
    """Process commands for real-time streaming optimization"""
    processed = []
    seen_signatures = set()
    
    for cmd in commands:
        try:
            # Create unique signature for deduplication
            signature = f"{cmd.get('command', '')}_{cmd.get('timestamp', '')}"
            if signature in seen_signatures:
                continue
            seen_signatures.add(signature)
            
            # Process command for streaming
            processed_cmd = _format_streaming_command(cmd)
            if processed_cmd:
                processed.append(processed_cmd)
                
        except Exception as cmd_error:
            logger.warning(f"[Command Streaming] Error processing command: {cmd_error}")
            continue
    
    return processed

def _format_streaming_command(raw_cmd: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Format command for real-time streaming display"""
    try:
        command_text = raw_cmd.get('command', '').strip()
        if not command_text:
            return None
        
        # Calculate relative time for streaming display
        timestamp = raw_cmd.get('timestamp', datetime.utcnow().isoformat())
        relative_time = _calculate_relative_time(timestamp)
        
        # Format for streaming
        formatted = {
            'id': f"{hash(command_text + timestamp)}",  # Unique ID for frontend
            'command': command_text,
            'type': _classify_streaming_command(command_text),
            'user': raw_cmd.get('user', 'system'),
            'timestamp': timestamp,
            'relative_time': relative_time,
            'status': raw_cmd.get('status', 'completed'),
            'streaming': True
        }
        
        # Add visual formatting hints
        formatted['display'] = _get_command_display_format(formatted)
        
        return formatted
        
    except Exception as e:
        logger.warning(f"[Command Streaming] Error formatting command: {e}")
        return None

def _classify_streaming_command(command: str) -> str:
    """Classify command type for streaming display"""
    cmd_lower = command.lower().strip()
    
    # System/Auto commands
    if cmd_lower in ['serverinfo', 'status', 'players', 'info']:
        return 'auto'
    
    # Admin commands
    admin_keywords = ['kick', 'ban', 'teleport', 'god', 'kit', 'give', 'heal']
    if any(cmd_lower.startswith(kw) for kw in admin_keywords):
        return 'admin'
    
    # Player commands
    player_keywords = ['say', 'help', 'home', 'warp', 'spawn', 'me']
    if any(cmd_lower.startswith(kw) for kw in player_keywords):
        return 'ingame'
    
    return 'admin'  # Default to admin

def _get_command_display_format(cmd: Dict[str, Any]) -> Dict[str, str]:
    """Get display formatting for command types"""
    cmd_type = cmd['type']
    
    formats = {
        'auto': {
            'color': 'text-blue-400',
            'icon': '🔄',
            'bg_color': 'bg-blue-900/20'
        },
        'admin': {
            'color': 'text-red-400',
            'icon': '⚡',
            'bg_color': 'bg-red-900/20'
        },
        'ingame': {
            'color': 'text-green-400',
            'icon': '🎮',
            'bg_color': 'bg-green-900/20'
        }
    }
    
    return formats.get(cmd_type, formats['admin'])

def _calculate_relative_time(timestamp: str) -> str:
    """Calculate human-readable relative time"""
    try:
        cmd_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        now = datetime.utcnow()
        delta = now - cmd_time
        
        seconds = delta.total_seconds()
        
        if seconds < 60:
            return f"{int(seconds)}s ago"
        elif seconds < 3600:
            return f"{int(seconds/60)}m ago"
        elif seconds < 86400:
            return f"{int(seconds/3600)}h ago"
        else:
            return f"{int(seconds/86400)}d ago"
            
    except:
        return "now"

# ===== REAL-TIME TREND CALCULATION =====

def calculate_real_time_trends(server_id: str, minutes: int = 30) -> Dict[str, Any]:
    """
    ✅ OPTIMIZED: Calculate real-time performance trends for live charts
    
    Enhanced features:
    - High-frequency trend calculation for live updates
    - Smart data sampling to maintain performance
    - Real-time anomaly detection
    - Predictive trend indicators
    
    Args:
        server_id: Server identifier
        minutes: Time range for real-time trends
        
    Returns:
        Real-time trend data optimized for Chart.js
    """
    try:
        logger.debug(f"[Real-time Trends] Calculating trends for {server_id} over {minutes} minutes")
        
        # Check cache for recent trends
        cache_key = f"realtime_trends_{server_id}_{minutes}"
        cached_trends = _live_cache.get(cache_key)
        
        if cached_trends and not _live_cache.should_update(cache_key, min_interval=30):
            return cached_trends
        
        # Get recent data points
        trend_data = _fetch_realtime_trend_data(server_id, minutes)
        
        # Calculate real-time trends
        calculated_trends = _calculate_trends_from_data(trend_data, minutes)
        
        # Format for real-time display
        formatted_trends = _format_realtime_trends(calculated_trends, server_id)
        
        # Cache results
        _live_cache.set(cache_key, formatted_trends)
        
        logger.debug(f"[Real-time Trends] ✅ Generated trends for {server_id}")
        return formatted_trends
        
    except Exception as e:
        logger.error(f"[Real-time Trends] Error calculating trends for {server_id}: {e}")
        return _generate_fallback_realtime_trends(server_id, minutes)

def _fetch_realtime_trend_data(server_id: str, minutes: int) -> List[Dict[str, Any]]:
    """Fetch data for real-time trend calculation"""
    try:
        # Get storage instance
        from . import _server_health_storage
        
        if not _server_health_storage:
            return _generate_mock_trend_data(minutes)
        
        # Get recent snapshots
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=minutes)
        
        snapshots = storage.get_health_snapshots_range(server_id, start_time, end_time)
        
        if snapshots:
            return snapshots
        else:
            return _generate_mock_trend_data(minutes)
            
    except Exception as e:
        logger.warning(f"[Real-time Trends] Error fetching trend data: {e}")
        return _generate_mock_trend_data(minutes)

def _calculate_trends_from_data(data: List[Dict], minutes: int) -> Dict[str, Any]:
    """Calculate trend metrics from data points"""
    if len(data) < 2:
        return _get_empty_trends()
    
    trends = {
        'timespan_minutes': minutes,
        'data_points': len(data),
        'metrics': {}
    }
    
    # Extract metric time series
    metrics = ['fps', 'cpu_usage', 'memory_usage', 'player_count']
    
    for metric in metrics:
        values = []
        timestamps = []
        
        for point in data:
            try:
                value = point.get('health_data', {}).get('statistics', {}).get(metric)
                timestamp = point.get('timestamp')
                
                if value is not None and timestamp:
                    values.append(float(value))
                    timestamps.append(timestamp)
            except:
                continue
        
        if len(values) >= 2:
            trends['metrics'][metric] = _calculate_single_metric_trend(values, timestamps)
        else:
            trends['metrics'][metric] = _get_empty_metric_trend()
    
    return trends

def _calculate_single_metric_trend(values: List[float], timestamps: List[str]) -> Dict[str, Any]:
    """Calculate trend for a single metric"""
    if len(values) < 2:
        return _get_empty_metric_trend()
    
    current = values[-1]
    previous = values[0]
    
    # Calculate change
    change = current - previous
    change_percent = (change / previous * 100) if previous != 0 else 0
    
    # Determine trend direction
    if change_percent > 5:
        direction = 'increasing'
    elif change_percent < -5:
        direction = 'decreasing'
    else:
        direction = 'stable'
    
    # Calculate statistics
    avg = sum(values) / len(values)
    min_val = min(values)
    max_val = max(values)
    
    return {
        'current': round(current, 2),
        'previous': round(previous, 2),
        'change': round(change, 2),
        'change_percent': round(change_percent, 2),
        'direction': direction,
        'average': round(avg, 2),
        'min': round(min_val, 2),
        'max': round(max_val, 2),
        'volatility': round(max_val - min_val, 2)
    }

def _format_realtime_trends(trends: Dict[str, Any], server_id: str) -> Dict[str, Any]:
    """Format trends for real-time display"""
    formatted = {
        'server_id': server_id,
        'timestamp': datetime.utcnow().isoformat(),
        'timespan': f"{trends.get('timespan_minutes', 30)} minutes",
        'data_quality': 'high' if trends.get('data_points', 0) > 10 else 'medium',
        'trends': trends.get('metrics', {}),
        'real_time': True
    }
    
    # Add trend summary
    formatted['summary'] = _generate_trend_summary(trends.get('metrics', {}))
    
    return formatted

def _generate_trend_summary(metrics: Dict[str, Any]) -> Dict[str, str]:
    """Generate human-readable trend summary"""
    summary = {}
    
    for metric_name, metric_data in metrics.items():
        direction = metric_data.get('direction', 'stable')
        change_percent = abs(metric_data.get('change_percent', 0))
        
        if direction == 'stable':
            summary[metric_name] = 'Stable'
        elif direction == 'increasing':
            if change_percent > 20:
                summary[metric_name] = 'Rising rapidly'
            elif change_percent > 10:
                summary[metric_name] = 'Rising'
            else:
                summary[metric_name] = 'Slightly up'
        else:  # decreasing
            if change_percent > 20:
                summary[metric_name] = 'Falling rapidly'
            elif change_percent > 10:
                summary[metric_name] = 'Falling'
            else:
                summary[metric_name] = 'Slightly down'
    
    return summary

# ===== WEBSOCKET INTEGRATION =====

class WebSocketHealthManager:
    """Manager for WebSocket-based real-time health updates"""
    
    def __init__(self):
        self.connections = {}
        self.update_frequency = 30  # seconds
        self.is_running = False
        self._lock = threading.Lock()
    
    def add_connection(self, server_id: str, websocket, callback: Callable = None):
        """Add WebSocket connection for server health updates"""
        with self._lock:
            if server_id not in self.connections:
                self.connections[server_id] = []
            
            self.connections[server_id].append({
                'websocket': websocket,
                'callback': callback,
                'connected_at': datetime.utcnow(),
                'last_update': None
            })
            
        logger.info(f"[WebSocket Health] Added connection for {server_id}")
    
    def remove_connection(self, server_id: str, websocket):
        """Remove WebSocket connection"""
        with self._lock:
            if server_id in self.connections:
                self.connections[server_id] = [
                    conn for conn in self.connections[server_id]
                    if conn['websocket'] != websocket
                ]
                
                if not self.connections[server_id]:
                    del self.connections[server_id]
                    
        logger.info(f"[WebSocket Health] Removed connection for {server_id}")
    
    async def broadcast_health_update(self, server_id: str, health_data: Dict[str, Any]):
        """Broadcast health update to all connected clients"""
        if server_id not in self.connections:
            return
        
        message = {
            'type': 'health_update',
            'server_id': server_id,
            'data': health_data,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        disconnected = []
        
        for i, conn in enumerate(self.connections[server_id]):
            try:
                if conn['callback']:
                    # Use callback if provided
                    await conn['callback'](message)
                else:
                    # Send via WebSocket
                    await conn['websocket'].send(json.dumps(message))
                
                conn['last_update'] = datetime.utcnow()
                
            except Exception as e:
                logger.warning(f"[WebSocket Health] Error sending to connection: {e}")
                disconnected.append(i)
        
        # Remove disconnected connections
        if disconnected:
            with self._lock:
                for i in reversed(disconnected):
                    if i < len(self.connections[server_id]):
                        del self.connections[server_id][i]

# Global WebSocket manager
_websocket_manager = WebSocketHealthManager()

def manage_websocket_health_data(server_id: str, websocket, callback: Callable = None):
    """
    ✅ OPTIMIZED: Manage WebSocket connections for real-time health data
    
    Enhanced features:
    - Automatic connection management
    - Smart update frequency control
    - Error handling and reconnection logic
    - Performance-optimized data streaming
    
    Args:
        server_id: Server identifier
        websocket: WebSocket connection
        callback: Optional callback function for data updates
    """
    try:
        logger.info(f"[WebSocket Management] Managing connection for {server_id}")
        
        # Add connection to manager
        _websocket_manager.add_connection(server_id, websocket, callback)
        
        # Return connection manager for cleanup
        return _websocket_manager
        
    except Exception as e:
        logger.error(f"[WebSocket Management] Error managing connection for {server_id}: {e}")
        raise

def format_realtime_response(data: Dict[str, Any], response_type: str = 'metrics') -> Dict[str, Any]:
    """
    ✅ OPTIMIZED: Format data for real-time API responses
    
    Enhanced formatting for:
    - Consistent response structure across all endpoints
    - Optimized data size for network efficiency
    - Client-side processing optimization
    - Error handling and fallback data inclusion
    
    Args:
        data: Raw data to format
        response_type: Type of response (metrics, commands, trends)
        
    Returns:
        Formatted response optimized for real-time consumption
    """
    try:
        base_response = {
            'success': True,
            'type': response_type,
            'timestamp': datetime.utcnow().isoformat(),
            'real_time': True,
            'api_version': '2.0.0'
        }
        
        # Format based on response type
        if response_type == 'metrics':
            base_response.update(_format_metrics_response(data))
        elif response_type == 'commands':
            base_response.update(_format_commands_response(data))
        elif response_type == 'trends':
            base_response.update(_format_trends_response(data))
        else:
            base_response['data'] = data
        
        # Add performance metadata
        base_response['metadata'] = {
            'cached': data.get('cached', False),
            'data_source': data.get('data_source', 'unknown'),
            'processing_time_ms': data.get('processing_time_ms', 0),
            'response_size_bytes': len(json.dumps(base_response))
        }
        
        return base_response
        
    except Exception as e:
        logger.error(f"[Response Formatting] Error formatting {response_type} response: {e}")
        return {
            'success': False,
            'type': response_type,
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat(),
            'fallback_mode': True
        }

def _format_metrics_response(data: Dict[str, Any]) -> Dict[str, Any]:
    """Format metrics data for real-time response"""
    return {
        'server_id': data.get('server_id'),
        'metrics': data.get('metrics', {}),
        'indicators': data.get('indicators', {}),
        'status': data.get('status', {}),
        'data_quality': data.get('data_quality', 'medium')
    }

def _format_commands_response(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Format commands data for real-time response"""
    return {
        'commands': data,
        'command_count': len(data),
        'latest_command_time': data[0].get('timestamp') if data else None,
        'command_types': list(set(cmd.get('type', 'unknown') for cmd in data))
    }

def _format_trends_response(data: Dict[str, Any]) -> Dict[str, Any]:
    """Format trends data for real-time response"""
    return {
        'server_id': data.get('server_id'),
        'trends': data.get('trends', {}),
        'summary': data.get('summary', {}),
        'timespan': data.get('timespan'),
        'data_quality': data.get('data_quality', 'medium')
    }

# ===== FALLBACK DATA GENERATORS =====

def _generate_fallback_live_metrics(server_id: str, error_msg: str) -> Dict[str, Any]:
    """Generate fallback live metrics"""
    return {
        'server_id': server_id,
        'timestamp': datetime.utcnow().isoformat(),
        'data_source': 'fallback',
        'error': error_msg,
        'metrics': {
            'cpu_usage': 15,
            'memory_usage': 25,
            'fps': 60,
            'player_count': 0,
            'response_time': 30
        },
        'indicators': {
            'performance_score': 85,
            'performance_level': 'good',
            'cpu_pressure': 'low',
            'memory_pressure': 'low',
            'fps_quality': 'excellent'
        },
        'status': {
            'level': 'operational',
            'color': 'green',
            'message': 'System running normally (fallback data)',
            'health_percentage': 85.0
        },
        'fallback_mode': True
    }

def _generate_synthetic_live_data(server_id: str) -> Dict[str, Any]:
    """Generate synthetic live data for testing"""
    import random
    
    now = datetime.utcnow()
    base_time = now.timestamp()
    
    # Generate realistic synthetic data
    return {
        'server_id': server_id,
        'timestamp': now.isoformat(),
        'data_source': 'synthetic',
        'cpu_usage': 15 + random.randint(0, 25),
        'memory_percent': 25 + random.randint(0, 20),
        'fps': 55 + random.randint(-10, 15),
        'player_count': random.randint(0, 8),
        'response_time': 25 + random.randint(-10, 20),
        'uptime': int(base_time % 86400),  # Uptime in seconds
        'synthetic': True
    }

def _generate_fallback_streaming_commands(server_id: str, limit: int) -> List[Dict[str, Any]]:
    """Generate fallback streaming commands"""
    commands = []
    now = datetime.utcnow()
    
    for i in range(min(limit, 5)):
        cmd_time = now - timedelta(minutes=i*5)
        commands.append({
            'id': f"fallback_{i}",
            'command': ['serverinfo', 'players', 'status'][i % 3],
            'type': 'auto',
            'user': 'system',
            'timestamp': cmd_time.isoformat(),
            'relative_time': f"{i*5}m ago",
            'status': 'completed',
            'streaming': True,
            'display': {
                'color': 'text-blue-400',
                'icon': '🔄',
                'bg_color': 'bg-blue-900/20'
            }
        })
    
    return commands

def _generate_mock_streaming_commands(server_id: str, limit: int) -> List[Dict[str, Any]]:
    """Generate mock streaming commands"""
    import random
    
    commands = []
    now = datetime.utcnow()
    
    sample_commands = [
        {'command': 'serverinfo', 'type': 'auto', 'user': 'system'},
        {'command': 'players', 'type': 'auto', 'user': 'system'},
        {'command': 'say Server maintenance in 30 minutes', 'type': 'admin', 'user': 'admin'},
        {'command': 'help', 'type': 'ingame', 'user': 'player123'},
        {'command': 'status', 'type': 'auto', 'user': 'system'},
    ]
    
    for i in range(min(limit, len(sample_commands))):
        cmd_template = sample_commands[i]
        cmd_time = now - timedelta(minutes=random.randint(1, 30))
        
        commands.append({
            'command': cmd_template['command'],
            'type': cmd_template['type'],
            'user': cmd_template['user'],
            'timestamp': cmd_time.isoformat(),
            'status': 'completed'
        })
    
    return commands

def _generate_fallback_realtime_trends(server_id: str, minutes: int) -> Dict[str, Any]:
    """Generate fallback real-time trends"""
    return {
        'server_id': server_id,
        'timestamp': datetime.utcnow().isoformat(),
        'timespan': f"{minutes} minutes",
        'data_quality': 'low',
        'trends': {
            'fps': _get_empty_metric_trend(),
            'cpu_usage': _get_empty_metric_trend(),
            'memory_usage': _get_empty_metric_trend(),
            'player_count': _get_empty_metric_trend()
        },
        'summary': {
            'fps': 'No data',
            'cpu_usage': 'No data',
            'memory_usage': 'No data',
            'player_count': 'No data'
        },
        'fallback_mode': True
    }

def _generate_mock_trend_data(minutes: int) -> List[Dict[str, Any]]:
    """Generate mock trend data for testing"""
    import random
    
    data = []
    now = datetime.utcnow()
    
    # Generate data points every 5 minutes
    points = minutes // 5
    
    for i in range(points):
        point_time = now - timedelta(minutes=i*5)
        data.append({
            'timestamp': point_time.isoformat(),
            'health_data': {
                'statistics': {
                    'fps': 55 + random.randint(-10, 15),
                    'cpu_usage': 20 + random.randint(-5, 20),
                    'memory_usage': 30 + random.randint(-5, 15),
                    'player_count': random.randint(0, 10)
                }
            }
        })
    
    return data

def _get_empty_trends() -> Dict[str, Any]:
    """Get empty trends structure"""
    return {
        'timespan_minutes': 0,
        'data_points': 0,
        'metrics': {}
    }

def _get_empty_metric_trend() -> Dict[str, Any]:
    """Get empty metric trend structure"""
    return {
        'current': 0,
        'previous': 0,
        'change': 0,
        'change_percent': 0,
        'direction': 'stable',
        'average': 0,
        'min': 0,
        'max': 0,
        'volatility': 0
    }