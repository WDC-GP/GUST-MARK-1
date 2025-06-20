"""
GUST Bot Enhanced - Enhanced WebSocket Manager (STABILITY FIX)
=============================================================
✅ ENHANCED: Pre-connection token validation and timeout handling
✅ ENHANCED: Exponential backoff reconnection with maximum attempts
✅ ENHANCED: Connection health monitoring and status tracking
✅ ENHANCED: Automatic cleanup of disconnected connections
✅ ENHANCED: Enhanced message handling with proper JSON parsing
✅ ENHANCED: Comprehensive error handling and logging
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
    from .client import GPortalWebSocketClient

logger = logging.getLogger(__name__)

class EnhancedWebSocketManager:
    """Enhanced WebSocket manager with stability improvements"""
    
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
        
        logger.info("✅ Enhanced WebSocket Manager initialized")
    
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
        """✅ NEW: Background health monitoring loop"""
        while self.running:
            try:
                time.sleep(self.health_check_interval)
                if self.running:
                    self._check_connection_health()
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
        if not token or len(token) < 10:
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
            client = EnhancedGPortalWebSocketClient(
                server_id,  # Pass original server_id (may include _test)
                region, 
                token, 
                self._enhanced_message_callback,
                max_reconnect_attempts=self.max_reconnect_attempts,
                reconnect_delays=self.reconnect_delays,
                connection_timeout=self.connection_timeout
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
            client: EnhancedGPortalWebSocketClient instance
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
                "reconnect_count": health_info.get('reconnect_count', 0)
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
            EnhancedGPortalWebSocketClient or None: Connection client
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
        
        current_time = time.time()
        for health_info in self.connection_health.values():
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
        
        return {
            "websockets_available": WEBSOCKETS_AVAILABLE,
            "manager_running": self.running,
            "total_connections": total_connections,
            "active_connections": active_connections,
            "total_messages": total_messages,
            "connection_details": self.get_connection_status(),
            # ✅ NEW: Enhanced statistics
            "health_statistics": health_stats,
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
# ENHANCED WEBSOCKET CLIENT
# ================================================================

if WEBSOCKETS_AVAILABLE:
    class EnhancedGPortalWebSocketClient:
        """✅ NEW: Enhanced G-Portal WebSocket client with stability improvements"""
        
        def __init__(self, server_id, region, token, message_callback, 
                     max_reconnect_attempts=5, reconnect_delays=None, connection_timeout=30):
            """
            Initialize enhanced WebSocket client
            
            Args:
                server_id: Server ID
                region: Server region  
                token: G-Portal authentication token
                message_callback: Callback function for messages
                max_reconnect_attempts: Maximum reconnection attempts
                reconnect_delays: List of delays between reconnection attempts
                connection_timeout: Connection timeout in seconds
            """
            self.server_id = server_id
            self.region = region
            self.token = token
            self.message_callback = message_callback
            self.max_reconnect_attempts = max_reconnect_attempts
            self.reconnect_delays = reconnect_delays or [2, 4, 8, 16, 32, 60]
            self.connection_timeout = connection_timeout
            
            self.websocket = None
            self.connected = False
            self.running = False
            self.reconnect_attempts = 0
            self.message_buffer = []
            self.is_test = '_test' in str(server_id)
            
            logger.debug(f"✅ Enhanced WebSocket client initialized for server {server_id}")
        
        async def connect(self):
            """✅ ENHANCED: Connect to G-Portal WebSocket with timeout and validation"""
            try:
                # ✅ ENHANCED: Pre-connection validation
                if not self.token or len(self.token) < 10:
                    logger.error(f"❌ Invalid token for server {self.server_id}")
                    return False
                
                uri = f"wss://www.g-portal.com/ngpapi/graphql"
                headers = {
                    "Authorization": f"Bearer {self.token}",
                    "Origin": "https://www.g-portal.com",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
                
                logger.info(f"🔌 Enhanced connecting to WebSocket for server {self.server_id}")
                
                # ✅ ENHANCED: Connection with timeout
                self.websocket = await asyncio.wait_for(
                    websockets.connect(uri, extra_headers=headers),
                    timeout=self.connection_timeout
                )
                
                self.connected = True
                self.running = True
                self.reconnect_attempts = 0
                
                logger.info(f"✅ Enhanced WebSocket connected for server {self.server_id}")
                
                # Send subscription
                subscription = {
                    "type": "start",
                    "payload": {
                        "query": """
                        subscription {
                          consoleMessage(rsid: {id: %d, region: %s}) {
                            message
                            timestamp
                          }
                        }
                        """ % (int(str(self.server_id).split('_')[0]), self.region)
                    }
                }
                
                await self.websocket.send(json.dumps(subscription))
                logger.debug(f"📡 Enhanced subscription sent for server {self.server_id}")
                
                return True
                
            except asyncio.TimeoutError:
                logger.error(f"❌ Enhanced WebSocket connection timeout for server {self.server_id}")
                return False
            except Exception as e:
                logger.error(f"❌ Enhanced WebSocket connection error for server {self.server_id}: {e}")
                return False
        
        async def listen_for_messages(self):
            """✅ ENHANCED: Listen for messages with automatic reconnection"""
            while self.running:
                try:
                    if not self.connected or not self.websocket:
                        await self._attempt_reconnection()
                        continue
                    
                    # Listen for messages
                    message = await self.websocket.recv()
                    await self._process_message(message)
                    
                except websockets.exceptions.ConnectionClosed:
                    logger.warning(f"⚠️ Enhanced WebSocket connection closed for server {self.server_id}")
                    self.connected = False
                    await self._attempt_reconnection()
                    
                except Exception as e:
                    logger.error(f"❌ Enhanced WebSocket listen error for server {self.server_id}: {e}")
                    self.connected = False
                    await asyncio.sleep(5)  # Short delay before retry
        
        async def _attempt_reconnection(self):
            """✅ NEW: Attempt reconnection with exponential backoff"""
            if self.reconnect_attempts >= self.max_reconnect_attempts:
                logger.error(f"❌ Max reconnection attempts reached for server {self.server_id}")
                self.running = False
                return
            
            delay_index = min(self.reconnect_attempts, len(self.reconnect_delays) - 1)
            delay = self.reconnect_delays[delay_index]
            
            logger.info(f"🔄 Enhanced reconnection attempt {self.reconnect_attempts + 1}/{self.max_reconnect_attempts} for server {self.server_id} in {delay}s")
            
            await asyncio.sleep(delay)
            
            self.reconnect_attempts += 1
            success = await self.connect()
            
            if success:
                logger.info(f"✅ Enhanced reconnection successful for server {self.server_id}")
            else:
                logger.warning(f"❌ Enhanced reconnection failed for server {self.server_id}")
        
        async def _process_message(self, message):
            """✅ ENHANCED: Process incoming message with proper parsing"""
            try:
                data = json.loads(message)
                
                if 'payload' in data and 'data' in data['payload']:
                    console_data = data['payload']['data'].get('consoleMessage', {})
                    
                    processed_message = {
                        'server_id': self.server_id,
                        'message': console_data.get('message', ''),
                        'timestamp': console_data.get('timestamp', datetime.now().isoformat()),
                        'source': 'enhanced_websocket_live',
                        'type': 'system'  # Will be classified by callback
                    }
                    
                    # Add to buffer
                    self.message_buffer.append(processed_message)
                    if len(self.message_buffer) > 1000:  # Keep last 1000 messages
                        self.message_buffer = self.message_buffer[-1000:]
                    
                    # Call callback
                    if self.message_callback:
                        await self.message_callback(processed_message)
                        
            except json.JSONDecodeError:
                logger.warning(f"⚠️ Invalid JSON message from server {self.server_id}")
            except Exception as e:
                logger.error(f"❌ Error processing message from server {self.server_id}: {e}")
        
        def get_recent_messages(self, limit=50, message_type=None):
            """Get recent messages with filtering"""
            messages = self.message_buffer
            
            if message_type and message_type != 'all':
                messages = [msg for msg in messages if msg.get('type') == message_type]
            
            return messages[-limit:] if limit else messages
        
        async def disconnect(self):
            """✅ ENHANCED: Disconnect with proper cleanup"""
            self.running = False
            self.connected = False
            
            if self.websocket:
                try:
                    await self.websocket.close()
                except Exception as e:
                    logger.debug(f"Error closing WebSocket for server {self.server_id}: {e}")
                
            logger.info(f"🔌 Enhanced WebSocket disconnected for server {self.server_id}")

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
    'stop': lambda self: None
})
