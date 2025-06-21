"""
GUST Bot Enhanced - Enhanced WebSocket Manager (EXTENDED FOR SENSOR BRIDGE)
==========================================================================
✅ ENHANCED: Pre-connection token validation and timeout handling
✅ ENHANCED: Exponential backoff reconnection with maximum attempts
✅ ENHANCED: Connection health monitoring and status tracking
✅ ENHANCED: Automatic cleanup of disconnected connections
✅ ENHANCED: Enhanced message handling with proper JSON parsing
✅ ENHANCED: Comprehensive error handling and logging
✅ EXTENDED: Sensor bridge integration for real-time health monitoring
✅ EXTENDED: Sensor data retrieval and management methods
✅ FIXED: Removed missing client import dependency
"""

# Standard library imports
import logging
import threading
import asyncio
import time
import json
from datetime import datetime

# Local imports
from config import WEBSOCKETS_AVAILABLE

# Conditional WebSocket imports
if WEBSOCKETS_AVAILABLE:
    import websockets

logger = logging.getLogger(__name__)

class EnhancedWebSocketManager:
    """Enhanced WebSocket manager with stability improvements and sensor bridge integration"""
    
    def __init__(self, gust_bot):
        """
        Initialize Enhanced WebSocket manager
        
        Args:
            gust_bot: Reference to main GUST bot instance
        """
        self.gust_bot = gust_bot
        self.connections = {}
        self.connection_health = {}
        self.loop = None
        self.running = False
        
        # ✅ ENHANCED: Connection management settings
        self.max_reconnect_attempts = 5
        self.reconnect_delays = [2, 4, 8, 16, 32, 60]  # Exponential backoff + max 60s
        self.connection_timeout = 30  # seconds
        self.health_check_interval = 120  # 2 minutes
        
        # ✅ NEW: Sensor bridge integration
        self.sensor_bridge = None
        
        logger.info("✅ Enhanced WebSocket Manager initialized with sensor bridge support")
    
    def initialize_sensor_bridge(self, server_health_storage=None):
        """✅ NEW: Initialize the sensor data bridge"""
        try:
            from websocket.sensor_bridge import WebSocketSensorBridge
            self.sensor_bridge = WebSocketSensorBridge(self, server_health_storage)
            logger.info("✅ Sensor bridge initialized and integrated")
            return self.sensor_bridge
        except Exception as e:
            logger.error(f"❌ Failed to initialize sensor bridge: {e}")
            return None

    def get_sensor_data(self, server_id: str):
        """✅ NEW: Get sensor data for a server"""
        if self.sensor_bridge:
            return self.sensor_bridge.get_real_sensor_data(server_id)
        return None

    def get_comprehensive_health_data(self, server_id: str):
        """✅ NEW: Get comprehensive health data for a server"""
        if self.sensor_bridge:
            return self.sensor_bridge.get_comprehensive_health_data(server_id)
        return None

    def get_sensor_statistics(self):
        """✅ NEW: Get sensor bridge statistics"""
        if self.sensor_bridge:
            return self.sensor_bridge.get_sensor_statistics()
        return {'error': 'Sensor bridge not initialized'}

    def test_sensor_connectivity(self, server_id: str):
        """✅ NEW: Test sensor connectivity for a server"""
        if self.sensor_bridge:
            return self.sensor_bridge.test_sensor_connectivity(server_id)
        return {'error': 'Sensor bridge not initialized'}

    def get_all_sensor_data(self):
        """✅ NEW: Get sensor data for all servers"""
        if self.sensor_bridge:
            return self.sensor_bridge.get_all_sensor_data()
        return {'error': 'Sensor bridge not initialized'}

    def get_health_summary(self):
        """✅ NEW: Get overall health summary"""
        if self.sensor_bridge:
            return self.sensor_bridge.get_health_summary()
        return {'error': 'Sensor bridge not initialized'}
    
    def start(self):
        """Start the enhanced WebSocket manager in a separate thread"""
        if not self.running and WEBSOCKETS_AVAILABLE:
            self.running = True
            thread = threading.Thread(target=self._run_loop, daemon=True)
            thread.start()
            
            # Start health monitoring
            health_thread = threading.Thread(target=self._health_monitor_loop, daemon=True)
            health_thread.start()
            
            logger.info("🚀 Enhanced WebSocket manager started with health monitoring")
        elif not WEBSOCKETS_AVAILABLE:
            logger.warning("⚠️ Enhanced WebSocket manager not started - websockets package not available")
    
    def _run_loop(self):
        """Run the asyncio event loop with enhanced error handling"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        try:
            self.loop.run_forever()
        except Exception as e:
            logger.error(f"❌ Enhanced WebSocket manager loop error: {e}")
        finally:
            self.loop.close()
    
    def _health_monitor_loop(self):
        """✅ ENHANCED: Background health monitoring loop with sensor bridge cleanup"""
        while self.running:
            try:
                time.sleep(self.health_check_interval)
                if self.running:
                    self._check_connection_health()
                    
                    # ✅ NEW: Clean up stale sensor cache
                    if self.sensor_bridge:
                        self.sensor_bridge.cleanup_stale_cache()
                        
            except Exception as health_error:
                logger.error(f"❌ Health monitor error: {health_error}")
                time.sleep(30)  # Shorter retry for health monitor
    
    def _check_connection_health(self):
        """✅ NEW: Check health of all connections"""
        try:
            current_time = time.time()
            stale_connections = []
            
            for server_id, health_info in self.connection_health.items():
                # Check for stale connections (no messages > 2 minutes)
                last_message_time = health_info.get('last_message_time', 0)
                if current_time - last_message_time > 120:  # 2 minutes
                    stale_connections.append(server_id)
                    logger.warning(f"⚠️ Stale connection detected for server {server_id}")
            
            # Clean up stale connections
            for server_id in stale_connections:
                self._cleanup_stale_connection(server_id)
                
            logger.debug(f"🏥 Health check completed: {len(self.connections)} active, {len(stale_connections)} cleaned")
            
        except Exception as e:
            logger.error(f"❌ Error in connection health check: {e}")
    
    def _cleanup_stale_connection(self, server_id):
        """✅ NEW: Clean up stale connection"""
        try:
            if server_id in self.connections:
                client = self.connections[server_id]
                if self.loop and not self.loop.is_closed():
                    asyncio.run_coroutine_threadsafe(
                        client.disconnect(), 
                        self.loop
                    )
                del self.connections[server_id]
                
            if server_id in self.connection_health:
                del self.connection_health[server_id]
                
            logger.info(f"🧹 Cleaned up stale connection for server {server_id}")
            
        except Exception as e:
            logger.error(f"❌ Error cleaning up stale connection {server_id}: {e}")
    
    def add_connection(self, server_id, region, token):
        """
        ✅ ENHANCED: Add a new WebSocket connection with pre-validation
        
        Args:
            server_id: Server ID (may include test suffix)
            region (str): Server region
            token (str): G-Portal authentication token
            
        Returns:
            Future: Asyncio future for the connection task
        """
        if not WEBSOCKETS_AVAILABLE:
            logger.warning("⚠️ Cannot add WebSocket connection - websockets package not available")
            return None
        
        if not self.running:
            self.start()
        
        # ✅ ENHANCED: Pre-connection token validation
        if not token or len(str(token)) < 10:
            logger.error(f"❌ Invalid token for server {server_id} connection")
            return None
        
        # Handle server ID properly (remove any test suffixes for storage key)
        storage_key = str(server_id).split('_')[0] if '_' in str(server_id) else str(server_id)
        
        if storage_key in self.connections:
            # Disconnect existing connection
            logger.info(f"🔄 Disconnecting existing connection for server {storage_key}")
            asyncio.run_coroutine_threadsafe(
                self.connections[storage_key].disconnect(), 
                self.loop
            )
        
        # ✅ ENHANCED: Create new connection with enhanced client
        try:
            # Import the extended client class
            from websocket.client import GPortalWebSocketClient
            
            client = GPortalWebSocketClient(
                server_id,  # Pass original server_id (may include _test)
                region, 
                token, 
                self._enhanced_message_callback
            )
            
            self.connections[storage_key] = client
            
            # ✅ NEW: Initialize connection health tracking
            self.connection_health[storage_key] = {
                'connected_at': time.time(),
                'last_message_time': time.time(),
                'message_count': 0,
                'reconnect_count': 0,
                'status': 'connecting'
            }
            
            # Start connection in the event loop
            future = asyncio.run_coroutine_threadsafe(
                self._enhanced_connect_and_listen(client, storage_key), 
                self.loop
            )
            
            logger.info(f"✅ Enhanced WebSocket connection queued for server {server_id}")
            return future
            
        except Exception as e:
            logger.error(f"❌ Error creating enhanced WebSocket connection for {server_id}: {e}")
            return None
    
    async def _enhanced_connect_and_listen(self, client, storage_key):
        """
        ✅ ENHANCED: Connect and start listening for a client with enhanced error handling
        
        Args:
            client: GPortalWebSocketClient instance
            storage_key: Storage key for tracking
        """
        try:
            logger.info(f"🔌 Starting enhanced connection for server {storage_key}")
            
            # ✅ ENHANCED: Connection with timeout
            connection_successful = await asyncio.wait_for(
                client.connect(), 
                timeout=self.connection_timeout
            )
            
            if connection_successful:
                # Update health status
                self.connection_health[storage_key]['status'] = 'connected'
                self.connection_health[storage_key]['last_message_time'] = time.time()
                
                logger.info(f"✅ Enhanced WebSocket connected for server {storage_key}")
                
                # Start listening for messages
                await client.listen_for_messages()
            else:
                logger.error(f"❌ Enhanced WebSocket connection failed for server {storage_key}")
                self.connection_health[storage_key]['status'] = 'failed'
                
        except asyncio.TimeoutError:
            logger.error(f"❌ Enhanced WebSocket connection timeout for server {storage_key}")
            self.connection_health[storage_key]['status'] = 'timeout'
            client.connected = False
        except Exception as e:
            logger.error(f"❌ Error in enhanced connect_and_listen for server {storage_key}: {e}")
            self.connection_health[storage_key]['status'] = 'error'
            client.connected = False
    
    async def _enhanced_message_callback(self, message):
        """
        ✅ ENHANCED: Callback for processing incoming messages with health tracking
        
        Args:
            message (dict): Message data from WebSocket
        """
        try:
            server_id = message.get('server_id', 'unknown')
            storage_key = str(server_id).split('_')[0] if '_' in str(server_id) else str(server_id)
            
            # ✅ NEW: Update health tracking
            if storage_key in self.connection_health:
                self.connection_health[storage_key]['last_message_time'] = time.time()
                self.connection_health[storage_key]['message_count'] += 1
                self.connection_health[storage_key]['status'] = 'active'
            
            logger.debug(f"📨 Enhanced WebSocket message from {server_id}: {message['message'][:100]}...")
            
            # Process special message types
            await self._process_enhanced_messages(message)
            
        except Exception as e:
            logger.error(f"❌ Error in enhanced message callback: {e}")
    
    async def _process_enhanced_messages(self, message):
        """
        ✅ ENHANCED: Process special message types with improved categorization
        
        Args:
            message (dict): Message data
        """
        try:
            msg_text = message.get("message", "")
            msg_type = message.get("type", "unknown")
            server_id = message.get("server_id", "unknown")
            
            # ✅ ENHANCED: Better message type detection
            if msg_type == "auth" or any(keyword in msg_text for keyword in ["VIP", "Admin", "Moderator", "Owner"]):
                logger.info(f"🔐 Auth update detected for server {server_id}")
                message["type"] = "auth"
            
            elif msg_type == "chat" or any(keyword in msg_text for keyword in ["[CHAT]", "global.say", ": "]):
                logger.debug(f"💬 Chat message from server {server_id}")
                message["type"] = "chat"
            
            elif msg_type == "save" or any(keyword in msg_text for keyword in ["[SAVE]", "saving", "saved"]):
                logger.info(f"💾 Save event for server {server_id}")
                message["type"] = "save"
            
            elif msg_type == "error" or any(keyword in msg_text for keyword in ["error", "exception", "failed"]):
                logger.warning(f"⚠️ Server error detected for {server_id}: {msg_text[:100]}...")
                message["type"] = "error"
            
            elif any(keyword in msg_text for keyword in ["[KILL]", "killed", "died"]):
                message["type"] = "kill"
            
            elif any(keyword in msg_text for keyword in ["connected", "disconnected", "joined", "left"]):
                message["type"] = "player"
            
            else:
                message["type"] = "system"
            
            # Add enhanced metadata
            message["processed_at"] = datetime.now().isoformat()
            message["source"] = "enhanced_websocket"
            
        except Exception as e:
            logger.error(f"❌ Error processing enhanced message: {e}")
    
    def remove_connection(self, server_id):
        """
        ✅ ENHANCED: Remove a WebSocket connection with proper cleanup
        
        Args:
            server_id: Server ID to disconnect
        """
        # Handle server ID properly (remove any test suffixes for storage key)
        storage_key = str(server_id).split('_')[0] if '_' in str(server_id) else str(server_id)
        
        if storage_key in self.connections:
            client = self.connections[storage_key]
            if self.loop and not self.loop.is_closed():
                asyncio.run_coroutine_threadsafe(
                    client.disconnect(), 
                    self.loop
                )
            del self.connections[storage_key]
            
            # ✅ NEW: Clean up health tracking
            if storage_key in self.connection_health:
                del self.connection_health[storage_key]
            
            logger.info(f"🔌 Enhanced WebSocket connection removed for server {storage_key}")
        else:
            logger.warning(f"⚠️ No enhanced connection found for server {storage_key}")
    
    def get_connection_status(self):
        """
        ✅ ENHANCED: Get status of all connections with health information
        
        Returns:
            dict: Enhanced status information for all connections
        """
        status = {}
        for server_id, client in self.connections.items():
            health_info = self.connection_health.get(server_id, {})
            
            status[server_id] = {
                "connected": client.connected,
                "running": getattr(client, 'running', False),
                "message_count": len(getattr(client, 'message_buffer', [])),
                "region": getattr(client, 'region', 'unknown'),
                "is_test": getattr(client, 'is_test', False),
                "reconnect_attempts": getattr(client, 'reconnect_attempts', 0),
                # ✅ NEW: Enhanced health information
                "health_status": health_info.get('status', 'unknown'),
                "connected_at": health_info.get('connected_at', 0),
                "last_message_time": health_info.get('last_message_time', 0),
                "total_messages": health_info.get('message_count', 0),
                "reconnect_count": health_info.get('reconnect_count', 0),
                # ✅ NEW: Sensor data status
                "has_sensor_data": getattr(client, 'latest_sensor_data', None) is not None,
                "sensor_data_fresh": getattr(client, 'is_sensor_data_fresh', lambda: False)(),
                "has_config_data": getattr(client, 'latest_config_data', None) is not None
            }
        return status
    
    def get_messages(self, server_id=None, limit=50, message_type=None):
        """
        ✅ ENHANCED: Get messages from specific server or all servers with filtering
        
        Args:
            server_id (str): Specific server ID, None for all servers
            limit (int): Maximum number of messages
            message_type (str): Filter by message type
            
        Returns:
            list: List of messages
        """
        logger.debug(f"📋 Enhanced get_messages: server_id={server_id}, limit={limit}, type={message_type}")
        
        if server_id and server_id in self.connections:
            messages = self.connections[server_id].get_recent_messages(limit, message_type)
            logger.debug(f"📋 Server {server_id} returned {len(messages)} enhanced messages")
            return messages
        else:
            # Get messages from all servers
            all_messages = []
            for server_key, client in self.connections.items():
                try:
                    client_messages = client.get_recent_messages(limit, message_type)
                    all_messages.extend(client_messages)
                    logger.debug(f"📋 Server {server_key} contributed {len(client_messages)} enhanced messages")
                except Exception as e:
                    logger.error(f"❌ Error getting messages from {server_key}: {e}")
            
            # Sort by timestamp and return most recent
            try:
                all_messages.sort(key=lambda x: x.get("timestamp", ""))
                final_messages = all_messages[-limit:] if limit else all_messages
                logger.debug(f"📋 Total enhanced messages: {len(final_messages)}")
                return final_messages
            except Exception as sort_error:
                logger.error(f"❌ Error sorting enhanced messages: {sort_error}")
                return all_messages[-limit:] if limit else all_messages
    
    def get_connection(self, server_id):
        """
        Get specific connection
        
        Args:
            server_id: Server ID
            
        Returns:
            GPortalWebSocketClient or None: Connection client
        """
        storage_key = str(server_id).split('_')[0] if '_' in str(server_id) else str(server_id)
        return self.connections.get(storage_key)
    
    def is_connected(self, server_id):
        """
        Check if server is connected
        
        Args:
            server_id: Server ID to check
            
        Returns:
            bool: True if connected
        """
        client = self.get_connection(server_id)
        return client.connected if client else False
    
    def get_stats(self):
        """
        ✅ ENHANCED: Get overall WebSocket manager statistics with health metrics
        
        Returns:
            dict: Enhanced statistics
        """
        total_connections = len(self.connections)
        active_connections = sum(1 for client in self.connections.values() if client.connected)
        total_messages = sum(len(getattr(client, 'message_buffer', [])) for client in self.connections.values())
        
        # ✅ NEW: Health statistics
        health_stats = {
            'healthy': 0,
            'warning': 0,
            'error': 0,
            'total_reconnects': 0
        }
        
        # ✅ NEW: Sensor statistics
        sensor_stats = {
            'servers_with_sensor_data': 0,
            'servers_with_fresh_data': 0,
            'servers_with_config_data': 0
        }
        
        current_time = time.time()
        for server_id, health_info in self.connection_health.items():
            status = health_info.get('status', 'unknown')
            last_message_time = health_info.get('last_message_time', 0)
            
            # Determine health status
            if status == 'active' and (current_time - last_message_time) < 300:  # 5 minutes
                health_stats['healthy'] += 1
            elif status in ['connected', 'active']:
                health_stats['warning'] += 1
            else:
                health_stats['error'] += 1
            
            health_stats['total_reconnects'] += health_info.get('reconnect_count', 0)
            
            # Check sensor data availability
            client = self.connections.get(server_id)
            if client:
                if getattr(client, 'latest_sensor_data', None):
                    sensor_stats['servers_with_sensor_data'] += 1
                    
                if getattr(client, 'is_sensor_data_fresh', lambda: False)():
                    sensor_stats['servers_with_fresh_data'] += 1
                    
                if getattr(client, 'latest_config_data', None):
                    sensor_stats['servers_with_config_data'] += 1
        
        return {
            "websockets_available": WEBSOCKETS_AVAILABLE,
            "manager_running": self.running,
            "total_connections": total_connections,
            "active_connections": active_connections,
            "total_messages": total_messages,
            "connection_details": self.get_connection_status(),
            # ✅ ENHANCED: Health statistics
            "health_statistics": health_stats,
            # ✅ NEW: Sensor statistics
            "sensor_statistics": sensor_stats,
            "sensor_bridge_available": self.sensor_bridge is not None,
            "max_reconnect_attempts": self.max_reconnect_attempts,
            "connection_timeout": self.connection_timeout,
            "health_check_interval": self.health_check_interval
        }
    
    def disconnect_all(self):
        """✅ ENHANCED: Disconnect all WebSocket connections with proper cleanup"""
        if not self.loop or self.loop.is_closed():
            return
            
        disconnected_count = 0
        for server_id in list(self.connections.keys()):
            try:
                self.remove_connection(server_id)
                disconnected_count += 1
            except Exception as e:
                logger.error(f"❌ Error disconnecting {server_id}: {e}")
        
        # Clear health tracking
        self.connection_health.clear()
        
        logger.info(f"🔌 All enhanced WebSocket connections disconnected ({disconnected_count} total)")
    
    def stop(self):
        """✅ ENHANCED: Stop the WebSocket manager with proper cleanup"""
        if self.running:
            self.disconnect_all()
            self.running = False
            
            if self.loop and not self.loop.is_closed():
                self.loop.call_soon_threadsafe(self.loop.stop)
            
            logger.info("🛑 Enhanced WebSocket manager stopped")

# ================================================================
# COMPATIBILITY LAYER
# ================================================================

# For backward compatibility, use enhanced manager as default
WebSocketManager = EnhancedWebSocketManager if WEBSOCKETS_AVAILABLE else type('DummyManager', (), {
    '__init__': lambda self, *args: None,
    'start': lambda self: None,
    'add_connection': lambda self, *args: None,
    'remove_connection': lambda self, *args: None,
    'get_connection_status': lambda self: {},
    'get_messages': lambda self, *args, **kwargs: [],
    'disconnect_all': lambda self: None,
    'stop': lambda self: None,
    'initialize_sensor_bridge': lambda self, *args: None,
    'get_sensor_data': lambda self, *args: None,
    'get_comprehensive_health_data': lambda self, *args: None,
    'get_sensor_statistics': lambda self: {},
    'test_sensor_connectivity': lambda self, *args: {},
    'get_all_sensor_data': lambda self: {},
    'get_health_summary': lambda self: {}
})