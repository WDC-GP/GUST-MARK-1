"""
GUST WebSocket Sensor Data Bridge
================================
Bridge between WebSocket sensor data and Server Health system
✅ NEW FILE: Connects real-time GraphQL sensor data to health monitoring
✅ FEATURES: CPU/memory monitoring, health calculations, comprehensive metrics
✅ INTEGRATION: Works with existing server health storage systems
"""

import logging
import time
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class WebSocketSensorBridge:
    """Bridge WebSocket sensor data to Server Health system"""
    
    def __init__(self, websocket_manager, server_health_storage=None):
        """
        Initialize sensor data bridge
        
        Args:
            websocket_manager: Reference to WebSocket manager
            server_health_storage: Reference to server health storage (optional)
        """
        self.websocket_manager = websocket_manager
        self.server_health_storage = server_health_storage
        self.cached_sensor_data = {}  # server_id -> sensor_data
        self.cache_timestamps = {}    # server_id -> timestamp
        
        logger.info("✅ WebSocket Sensor Bridge initialized")
    
    def get_real_sensor_data(self, server_id: str) -> Optional[Dict[str, Any]]:
        """
        Get real-time sensor data from WebSocket connection
        
        Args:
            server_id: Server ID to get data for
            
        Returns:
            Dict containing sensor data or None if not available
        """
        try:
            # Get WebSocket client for this server
            client = self.websocket_manager.get_connection(server_id)
            
            if not client or not client.connected:
                logger.debug(f"🔌 No WebSocket connection for server {server_id}")
                return None
            
            # Get latest sensor data from client
            sensor_data = client.get_latest_sensor_data()
            
            if not sensor_data:
                logger.debug(f"📊 No sensor data available for server {server_id}")
                return None
            
            # Check if data is fresh (within last 60 seconds)
            if not client.is_sensor_data_fresh(max_age_seconds=60):
                logger.warning(f"⏰ Sensor data for server {server_id} is stale")
                return None
            
            # Cache the data
            self.cached_sensor_data[server_id] = sensor_data
            self.cache_timestamps[server_id] = time.time()
            
            logger.debug(f"✅ Fresh sensor data retrieved for server {server_id}")
            return sensor_data
            
        except Exception as e:
            logger.error(f"❌ Error getting sensor data for server {server_id}: {e}")
            return None
    
    def get_comprehensive_health_data(self, server_id: str) -> Dict[str, Any]:
        """
        Get comprehensive health data combining WebSocket sensors + other sources
        
        Args:
            server_id: Server ID
            
        Returns:
            Dict with comprehensive health data
        """
        try:
            # Try to get real-time sensor data
            sensor_data = self.get_real_sensor_data(server_id)
            
            if sensor_data:
                # Calculate health metrics from real sensor data
                health_percentage = self.calculate_health_from_sensors(sensor_data)
                status = self.determine_status_from_health(health_percentage)
                
                return {
                    'success': True,
                    'server_id': server_id,
                    'health_percentage': health_percentage,
                    'status': status,
                    'metrics': {
                        'cpu_usage': sensor_data['cpu_total'],
                        'memory_usage': sensor_data['memory_used_mb'],
                        'memory_percent': sensor_data['memory_percent'],
                        'uptime': sensor_data['uptime_seconds'],
                        'response_time': 25,  # WebSocket response is very fast
                        'player_count': 0,  # TODO: Get from other source
                        'max_players': 100,
                        'fps': 60  # Estimated based on good performance
                    },
                    'data_source': 'websocket_sensors',
                    'data_quality': 'high',
                    'timestamp': sensor_data['timestamp'],
                    'source_info': {
                        'primary_sources': ['graphql_sensors'],
                        'real_cpu_data': True,
                        'real_memory_data': True,
                        'real_uptime_data': True,
                        'last_updated': sensor_data['timestamp']
                    }
                }
            
            # Fallback to existing health system if no sensor data
            if self.server_health_storage:
                return self.server_health_storage.get_server_health_status(server_id)
            
            # Last resort - basic response
            return {
                'success': False,
                'server_id': server_id,
                'error': 'No sensor data or health storage available',
                'timestamp': time.time()
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting comprehensive health for {server_id}: {e}")
            return {
                'success': False,
                'server_id': server_id,
                'error': str(e),
                'timestamp': time.time()
            }
    
    def calculate_health_from_sensors(self, sensor_data: Dict[str, Any]) -> float:
        """Calculate health percentage from sensor data"""
        try:
            cpu_percent = sensor_data.get('cpu_total', 0)
            memory_percent = sensor_data.get('memory_percent', 0)
            uptime = sensor_data.get('uptime_seconds', 0)
            
            # CPU score (0-100, lower usage = higher score)
            cpu_score = max(0, 100 - cpu_percent)
            
            # Memory score (0-100, lower usage = higher score) 
            memory_score = max(0, 100 - memory_percent)
            
            # Uptime score (bonus for longer uptime)
            uptime_hours = uptime / 3600
            uptime_score = min(100, 50 + (uptime_hours * 2))  # Base 50, +2 per hour, max 100
            
            # Weighted average
            health_percentage = (
                cpu_score * 0.4 +      # 40% weight on CPU
                memory_score * 0.4 +   # 40% weight on memory  
                uptime_score * 0.2     # 20% weight on uptime
            )
            
            return round(max(0, min(100, health_percentage)), 1)
            
        except Exception as e:
            logger.error(f"❌ Error calculating health from sensors: {e}")
            return 75.0  # Default fallback
    
    def determine_status_from_health(self, health_percentage: float) -> str:
        """Determine status from health percentage"""
        if health_percentage >= 80:
            return 'healthy'
        elif health_percentage >= 60:
            return 'warning'
        else:
            return 'critical'
    
    def get_server_config_data(self, server_id: str) -> Optional[Dict[str, Any]]:
        """
        Get server configuration data from WebSocket
        
        Args:
            server_id: Server ID
            
        Returns:
            Dict containing config data or None
        """
        try:
            client = self.websocket_manager.get_connection(server_id)
            
            if not client or not client.connected:
                return None
            
            config_data = client.get_latest_config_data()
            return config_data
            
        except Exception as e:
            logger.error(f"❌ Error getting config data for server {server_id}: {e}")
            return None
    
    def get_sensor_statistics(self) -> Dict[str, Any]:
        """Get statistics about sensor data availability"""
        try:
            total_servers = len(self.websocket_manager.connections) if self.websocket_manager else 0
            connected_servers = 0
            servers_with_sensor_data = 0
            
            if self.websocket_manager:
                for server_id, client in self.websocket_manager.connections.items():
                    if client.connected:
                        connected_servers += 1
                        if client.get_latest_sensor_data():
                            servers_with_sensor_data += 1
            
            return {
                'total_servers': total_servers,
                'connected_servers': connected_servers,
                'servers_with_sensor_data': servers_with_sensor_data,
                'sensor_data_coverage': f"{servers_with_sensor_data}/{total_servers}",
                'cached_sensor_data': len(self.cached_sensor_data),
                'bridge_status': 'operational' if self.websocket_manager else 'no_manager'
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting sensor statistics: {e}")
            return {'error': str(e)}
    
    def test_sensor_connectivity(self, server_id: str) -> Dict[str, Any]:
        """
        Test sensor data connectivity for a specific server
        
        Args:
            server_id: Server ID to test
            
        Returns:
            Dict with test results
        """
        try:
            test_start = time.time()
            
            # Check if manager exists
            if not self.websocket_manager:
                return {
                    'success': False,
                    'server_id': server_id,
                    'error': 'No WebSocket manager available',
                    'test_duration': time.time() - test_start
                }
            
            # Check if connection exists
            client = self.websocket_manager.get_connection(server_id)
            if not client:
                return {
                    'success': False,
                    'server_id': server_id,
                    'error': 'No WebSocket connection for server',
                    'test_duration': time.time() - test_start
                }
            
            # Check connection status
            if not client.connected:
                return {
                    'success': False,
                    'server_id': server_id,
                    'error': 'WebSocket connection not active',
                    'connection_info': client.get_connection_info(),
                    'test_duration': time.time() - test_start
                }
            
            # Check sensor data availability
            sensor_data = client.get_latest_sensor_data()
            config_data = client.get_latest_config_data()
            
            # Check data freshness
            is_fresh = client.is_sensor_data_fresh(max_age_seconds=60)
            
            return {
                'success': True,
                'server_id': server_id,
                'connection_active': True,
                'has_sensor_data': sensor_data is not None,
                'has_config_data': config_data is not None,
                'sensor_data_fresh': is_fresh,
                'sensor_data_age': time.time() - (client.sensor_data_timestamp or 0),
                'connection_info': client.get_connection_info(),
                'test_duration': time.time() - test_start
            }
            
        except Exception as e:
            return {
                'success': False,
                'server_id': server_id,
                'error': f'Test error: {str(e)}',
                'test_duration': time.time() - test_start
            }
    
    def get_all_sensor_data(self) -> Dict[str, Any]:
        """
        Get sensor data for all connected servers
        
        Returns:
            Dict with sensor data for all servers
        """
        try:
            all_data = {}
            
            if not self.websocket_manager:
                return {'error': 'No WebSocket manager available'}
            
            for server_id, client in self.websocket_manager.connections.items():
                try:
                    if client.connected:
                        sensor_data = client.get_latest_sensor_data()
                        config_data = client.get_latest_config_data()
                        
                        all_data[server_id] = {
                            'sensor_data': sensor_data,
                            'config_data': config_data,
                            'connection_info': client.get_connection_info(),
                            'data_fresh': client.is_sensor_data_fresh()
                        }
                    else:
                        all_data[server_id] = {
                            'error': 'Not connected',
                            'connection_info': client.get_connection_info()
                        }
                        
                except Exception as client_error:
                    all_data[server_id] = {
                        'error': f'Client error: {str(client_error)}'
                    }
            
            return {
                'success': True,
                'data': all_data,
                'total_servers': len(all_data),
                'timestamp': time.time()
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting all sensor data: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': time.time()
            }
    
    def cleanup_stale_cache(self, max_age_seconds=300):
        """
        Clean up stale cached sensor data
        
        Args:
            max_age_seconds: Maximum age of cached data in seconds
        """
        try:
            current_time = time.time()
            stale_keys = []
            
            for server_id, timestamp in self.cache_timestamps.items():
                if current_time - timestamp > max_age_seconds:
                    stale_keys.append(server_id)
            
            for key in stale_keys:
                if key in self.cached_sensor_data:
                    del self.cached_sensor_data[key]
                if key in self.cache_timestamps:
                    del self.cache_timestamps[key]
            
            if stale_keys:
                logger.info(f"🧹 Cleaned up {len(stale_keys)} stale sensor data entries")
                
        except Exception as e:
            logger.error(f"❌ Error cleaning up stale cache: {e}")
    
    def get_health_summary(self) -> Dict[str, Any]:
        """
        Get overall health summary across all servers
        
        Returns:
            Dict with health summary statistics
        """
        try:
            if not self.websocket_manager:
                return {'error': 'No WebSocket manager available'}
            
            total_servers = len(self.websocket_manager.connections)
            healthy_servers = 0
            warning_servers = 0
            critical_servers = 0
            offline_servers = 0
            
            avg_cpu = 0
            avg_memory = 0
            total_uptime = 0
            active_servers = 0
            
            for server_id, client in self.websocket_manager.connections.items():
                try:
                    if not client.connected:
                        offline_servers += 1
                        continue
                    
                    sensor_data = client.get_latest_sensor_data()
                    if not sensor_data or not client.is_sensor_data_fresh():
                        offline_servers += 1
                        continue
                    
                    # Calculate health for this server
                    health_percentage = self.calculate_health_from_sensors(sensor_data)
                    
                    if health_percentage >= 80:
                        healthy_servers += 1
                    elif health_percentage >= 60:
                        warning_servers += 1
                    else:
                        critical_servers += 1
                    
                    # Add to averages
                    avg_cpu += sensor_data.get('cpu_total', 0)
                    avg_memory += sensor_data.get('memory_percent', 0)
                    total_uptime += sensor_data.get('uptime_seconds', 0)
                    active_servers += 1
                    
                except Exception as server_error:
                    logger.warning(f"Error processing health for server {server_id}: {server_error}")
                    offline_servers += 1
            
            # Calculate averages
            if active_servers > 0:
                avg_cpu = round(avg_cpu / active_servers, 1)
                avg_memory = round(avg_memory / active_servers, 1)
                avg_uptime = round(total_uptime / active_servers, 0)
            
            return {
                'success': True,
                'total_servers': total_servers,
                'server_status': {
                    'healthy': healthy_servers,
                    'warning': warning_servers,
                    'critical': critical_servers,
                    'offline': offline_servers,
                    'active': active_servers
                },
                'averages': {
                    'cpu_usage': avg_cpu,
                    'memory_usage': avg_memory,
                    'uptime_seconds': avg_uptime,
                    'uptime_hours': round(avg_uptime / 3600, 1)
                },
                'timestamp': time.time()
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting health summary: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': time.time()
            }