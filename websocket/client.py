"""
GUST Bot Enhanced - WebSocket Client (EXTENDED FOR SENSOR DATA)
==============================================================
✅ EXTENDED: Real-time sensor data (CPU, memory, uptime) from G-Portal GraphQL
✅ EXTENDED: Server configuration data subscriptions
✅ EXTENDED: Enhanced message processing for multiple data streams
✅ ENHANCED: Sensor data storage and callback system
"""

# Standard library imports
from collections import deque
from datetime import datetime
import json
import logging
import time

# Utility imports
from utils.helpers import classify_message

# Local imports
from config import Config, WEBSOCKETS_AVAILABLE

# Other imports
import asyncio

if WEBSOCKETS_AVAILABLE:
    import websockets

logger = logging.getLogger(__name__)

class GPortalWebSocketClient:
    """✅ EXTENDED: WebSocket client for G-Portal live console monitoring + sensor data"""
    
    def __init__(self, server_id, region, token, message_callback=None):
        """
        Initialize WebSocket client with sensor data support
        
        Args:
            server_id: Server ID (may include test suffix)
            region (str): Server region (US, EU, AS)
            token (str): G-Portal authentication token
            message_callback: Async callback function for messages
        """
        # Handle test server IDs that might have suffixes
        if isinstance(server_id, str) and '_test' in server_id:
            self.server_id = int(server_id.split('_')[0])
            self.is_test = True
        else:
            self.server_id = int(server_id)
            self.is_test = False
        
        self.region = region.upper()
        self.token = token
        self.message_callback = message_callback
        self.ws = None
        self.connected = False
        self.running = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.message_buffer = deque(maxlen=Config.CONSOLE_MESSAGE_BUFFER_SIZE)
        
        # ✅ NEW: Sensor data storage
        self.latest_sensor_data = None
        self.latest_config_data = None
        self.sensor_data_timestamp = None
        self.sensor_callbacks = []
        
    async def connect(self):
        """
        ✅ EXTENDED: Establish WebSocket connection to G-Portal with sensor subscriptions
        
        Returns:
            bool: True if connection successful
        """
        try:
            uri = Config.WEBSOCKET_URI
            
            logger.info(f"🔌 Connecting to WebSocket for server {self.server_id} ({self.region})")
            
            # Try different connection methods for compatibility
            try:
                # Method 1: Try with subprotocols parameter (most compatible)
                self.ws = await websockets.connect(
                    uri,
                    subprotocols=["graphql-ws"],
                    ping_interval=Config.WEBSOCKET_PING_INTERVAL,
                    ping_timeout=Config.WEBSOCKET_PING_TIMEOUT
                )
                logger.info(f"✅ WebSocket connected using method 1 for server {self.server_id}")
                
            except Exception as e1:
                logger.warning(f"⚠️ Method 1 failed: {e1}")
                try:
                    # Method 2: Basic connection without extra parameters
                    self.ws = await websockets.connect(uri)
                    logger.info(f"✅ WebSocket connected using method 2 for server {self.server_id}")
                    
                except Exception as e2:
                    logger.error(f"❌ All connection methods failed: {e1}, {e2}")
                    raise e2
            
            # Initialize connection with authentication
            init_message = {
                "type": "connection_init",
                "payload": {
                    "authorization": f"Bearer {self.token}"
                }
            }
            
            await self.ws.send(json.dumps(init_message))
            logger.info(f"📤 Sent connection_init for server {self.server_id}")
            
            # Wait for connection acknowledgment
            ack_received = False
            timeout = Config.WEBSOCKET_CONNECTION_TIMEOUT
            start_time = time.time()
            
            logger.info(f"⏳ Waiting for connection acknowledgment for server {self.server_id}...")
            
            while not ack_received and (time.time() - start_time) < timeout:
                try:
                    message = await asyncio.wait_for(self.ws.recv(), timeout=2.0)
                    data = json.loads(message)
                    logger.info(f"📨 Received message: {data}")
                    
                    if data.get("type") == "connection_ack":
                        ack_received = True
                        logger.info(f"✅ WebSocket connection acknowledged for server {self.server_id}")
                        break
                        
                except asyncio.TimeoutError:
                    logger.debug(f"⏳ Still waiting for ack for server {self.server_id}...")
                    continue
                except json.JSONDecodeError as e:
                    logger.error(f"❌ JSON decode error: {e}")
                    continue
                except Exception as e:
                    logger.error(f"❌ Error during connection ack: {e}")
                    break
            
            if ack_received:
                logger.info(f"✅ WebSocket connection acknowledged for server {self.server_id}")
                
                # Subscribe to console messages (existing)
                await self.subscribe_to_console()
                
                # ✅ NEW: Subscribe to sensor data
                await self.subscribe_to_sensors()
                
                # ✅ NEW: Subscribe to config data  
                await self.subscribe_to_server_config()
                
                self.connected = True
                self.reconnect_attempts = 0
                return True
            else:
                raise Exception(f"Connection acknowledgment timeout after {timeout}s")
                
        except Exception as e:
            logger.error(f"❌ WebSocket connection failed for server {self.server_id}: {e}")
            self.connected = False
            return False
    
    async def subscribe_to_console(self):
        """Subscribe to console messages stream"""
        subscription_payload = {
            "id": f"console_stream_{self.server_id}",
            "type": "start",
            "payload": {
                "variables": {
                    "sid": self.server_id,
                    "region": self.region
                },
                "extensions": {},
                "operationName": "consoleMessages",
                "query": """subscription consoleMessages($sid: Int!, $region: REGION!) {
                    consoleMessages(rsid: {id: $sid, region: $region}) {
                        stream
                        channel
                        message
                        __typename
                    }
                }"""
            }
        }
        
        try:
            await self.ws.send(json.dumps(subscription_payload))
            logger.info(f"📡 Subscribed to console messages for server {self.server_id}")
        except Exception as e:
            logger.error(f"❌ Failed to subscribe to console for server {self.server_id}: {e}")
            raise e

    async def subscribe_to_sensors(self):
        """✅ NEW: Subscribe to server sensor data (CPU, memory, uptime)"""
        try:
            # Get clean server ID (remove test suffixes)
            clean_server_id = str(self.server_id).split('_')[0]
            region_code = f'"{self.region}"'
            
            subscription_payload = {
                "id": f"sensors_stream_{self.server_id}",
                "type": "start",
                "payload": {
                    "query": f"""subscription ServiceSensors($sid: Int!, $region: String!) {{
                        serviceSensors(rsid: {{id: $sid, region: $region}}) {{
                            cpu
                            cpuTotal
                            memory {{
                                percent
                                used
                                total
                            }}
                            uptime
                            timestamp
                            __typename
                        }}
                    }}""",
                    "variables": {
                        "sid": int(clean_server_id),
                        "region": self.region
                    }
                }
            }
            
            await self.ws.send(json.dumps(subscription_payload))
            logger.info(f"📡 Subscribed to sensor data for server {self.server_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to subscribe to sensors for server {self.server_id}: {e}")
            raise e

    async def subscribe_to_server_config(self):
        """✅ NEW: Subscribe to server configuration data"""
        try:
            clean_server_id = str(self.server_id).split('_')[0]
            
            subscription_payload = {
                "id": f"config_stream_{self.server_id}",
                "type": "start", 
                "payload": {
                    "query": f"""subscription ServerConfig($sid: Int!, $region: String!) {{
                        cfgContext(rsid: {{id: $sid, region: $region}}) {{
                            ns {{
                                service {{
                                    currentState {{
                                        state
                                        fsmState
                                        fsmIsTransitioning
                                    }}
                                    config {{
                                        state
                                        ipAddress
                                    }}
                                }}
                            }}
                        }}
                    }}""",
                    "variables": {
                        "sid": int(clean_server_id),
                        "region": self.region
                    }
                }
            }
            
            await self.ws.send(json.dumps(subscription_payload))
            logger.info(f"📡 Subscribed to config data for server {self.server_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to subscribe to config for server {self.server_id}: {e}")
            raise e
    
    def _is_connection_open(self):
        """Check if WebSocket connection is open"""
        if not self.ws:
            return False
        
        try:
            # Try different methods to check connection state
            if hasattr(self.ws, 'closed'):
                return not self.ws.closed
            elif hasattr(self.ws, 'state'):
                # For newer websockets versions
                import websockets
                return self.ws.state == websockets.protocol.State.OPEN
            else:
                # Fallback - assume open if we have a connection
                return True
        except Exception:
            return False
    
    async def listen_for_messages(self):
        """Main message listening loop"""
        self.running = True
        logger.info(f"👂 Starting message listener for server {self.server_id}")
        
        try:
            while self.running and self.connected:
                try:
                    # Receive message with timeout
                    message = await asyncio.wait_for(self.ws.recv(), timeout=10.0)
                    await self.process_message(message)
                    
                except asyncio.TimeoutError:
                    # Send ping to keep connection alive
                    if self.ws and self._is_connection_open():
                        try:
                            await self.ws.ping()
                            logger.debug(f"📡 Ping sent to server {self.server_id}")
                        except Exception as ping_error:
                            logger.warning(f"⚠️ Ping failed for server {self.server_id}: {ping_error}")
                    continue
                    
                except websockets.exceptions.ConnectionClosed as e:
                    logger.warning(f"⚠️ WebSocket connection closed for server {self.server_id}: {e}")
                    self.connected = False
                    break
                except websockets.exceptions.WebSocketException as e:
                    logger.error(f"❌ WebSocket error for server {self.server_id}: {e}")
                    self.connected = False
                    break
                except Exception as e:
                    logger.error(f"❌ Error processing message for server {self.server_id}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"❌ Fatal error in message listener for server {self.server_id}: {e}")
        finally:
            self.connected = False
            self.running = False
            logger.info(f"🔌 Message listener stopped for server {self.server_id}")
    
    async def process_message(self, message):
        """✅ EXTENDED: Process incoming WebSocket message including sensor data"""
        try:
            data = json.loads(message)
            
            # Handle different message types
            if data.get("type") == "data":
                stream_id = data.get("id", "")
                payload = data.get("payload", {})
                
                # Existing console message handling
                if f"console_stream_{self.server_id}" in stream_id:
                    console_data = payload.get("data", {})
                    if console_data.get("consoleMessages"):
                        console_msg = console_data["consoleMessages"]
                        message_text = console_msg.get("message", "")
                        
                        if message_text:
                            # Create structured message object
                            processed_message = {
                                "timestamp": datetime.now().isoformat(),
                                "server_id": self.server_id,
                                "region": self.region,
                                "message": message_text,
                                "stream": console_msg.get("stream", ""),
                                "channel": console_msg.get("channel", ""),
                                "type": classify_message(message_text),
                                "source": "websocket_live"
                            }
                            
                            # Add to buffer
                            self.message_buffer.append(processed_message)
                            
                            # Call callback if provided
                            if self.message_callback:
                                try:
                                    await self.message_callback(processed_message)
                                except Exception as callback_error:
                                    logger.error(f"❌ Callback error for server {self.server_id}: {callback_error}")
                            
                            logger.info(f"📨 Live console message from {self.server_id}: {message_text[:100]}...")
                
                # ✅ NEW: Sensor data handling
                elif f"sensors_stream_{self.server_id}" in stream_id:
                    sensor_data = payload.get("data", {})
                    if sensor_data.get("serviceSensors"):
                        await self.process_sensor_data(sensor_data["serviceSensors"])
                
                # ✅ NEW: Config data handling
                elif f"config_stream_{self.server_id}" in stream_id:
                    config_data = payload.get("data", {})
                    if config_data.get("cfgContext"):
                        await self.process_config_data(config_data["cfgContext"])
            
            elif data.get("type") == "error":
                logger.error(f"❌ WebSocket error for server {self.server_id}: {data}")
                
            elif data.get("type") == "complete":
                logger.info(f"✅ Subscription completed for server {self.server_id}")
                
        except json.JSONDecodeError:
            logger.error(f"❌ Invalid JSON message from server {self.server_id}: {message[:100]}...")
        except Exception as e:
            logger.error(f"❌ Error processing message from server {self.server_id}: {e}")

    async def process_sensor_data(self, sensor_data):
        """✅ NEW: Process incoming sensor data"""
        try:
            # Store the latest sensor data
            self.latest_sensor_data = {
                'cpu_usage': sensor_data.get('cpu', 0),
                'cpu_total': sensor_data.get('cpuTotal', 0),
                'memory_percent': sensor_data.get('memory', {}).get('percent', 0),
                'memory_used_mb': sensor_data.get('memory', {}).get('used', 0),
                'memory_total_mb': sensor_data.get('memory', {}).get('total', 0),
                'uptime_seconds': sensor_data.get('uptime', 0),
                'timestamp': sensor_data.get('timestamp'),
                'data_source': 'graphql_websocket',
                'server_id': self.server_id
            }
            
            self.sensor_data_timestamp = time.time()
            
            logger.debug(f"📊 Sensor data updated for server {self.server_id}: "
                        f"CPU: {self.latest_sensor_data['cpu_total']}%, "
                        f"Memory: {self.latest_sensor_data['memory_percent']}%")
            
            # Call sensor callbacks
            for callback in self.sensor_callbacks:
                try:
                    await callback(self.latest_sensor_data)
                except Exception as callback_error:
                    logger.error(f"❌ Sensor callback error: {callback_error}")
                    
        except Exception as e:
            logger.error(f"❌ Error processing sensor data: {e}")

    async def process_config_data(self, config_data):
        """✅ NEW: Process incoming config data"""
        try:
            ns = config_data.get('ns', {})
            service = ns.get('service', {})
            current_state = service.get('currentState', {})
            config = service.get('config', {})
            
            self.latest_config_data = {
                'server_state': current_state.get('state', 'UNKNOWN'),
                'fsm_state': current_state.get('fsmState', 'Unknown'),
                'is_transitioning': current_state.get('fsmIsTransitioning', False),
                'ip_address': config.get('ipAddress', ''),
                'timestamp': time.time(),
                'server_id': self.server_id
            }
            
            logger.debug(f"⚙️ Config data updated for server {self.server_id}: "
                        f"State: {self.latest_config_data['server_state']}")
                        
        except Exception as e:
            logger.error(f"❌ Error processing config data: {e}")

    def add_sensor_callback(self, callback):
        """✅ NEW: Add callback for sensor data updates"""
        self.sensor_callbacks.append(callback)

    def get_latest_sensor_data(self):
        """✅ NEW: Get the latest sensor data"""
        return self.latest_sensor_data

    def is_sensor_data_fresh(self, max_age_seconds=30):
        """✅ NEW: Check if sensor data is fresh"""
        if not self.sensor_data_timestamp:
            return False
        return (time.time() - self.sensor_data_timestamp) < max_age_seconds

    def get_latest_config_data(self):
        """✅ NEW: Get the latest config data"""
        return self.latest_config_data
    
    async def disconnect(self):
        """Cleanly disconnect WebSocket"""
        logger.info(f"🔌 Disconnecting WebSocket for server {self.server_id}")
        
        self.running = False
        self.connected = False
        
        if self.ws and self._is_connection_open():
            try:
                # Send stop messages for all subscriptions
                stop_console = {
                    "id": f"console_stream_{self.server_id}",
                    "type": "stop"
                }
                stop_sensors = {
                    "id": f"sensors_stream_{self.server_id}",
                    "type": "stop"
                }
                stop_config = {
                    "id": f"config_stream_{self.server_id}",
                    "type": "stop"
                }
                
                await self.ws.send(json.dumps(stop_console))
                await self.ws.send(json.dumps(stop_sensors))
                await self.ws.send(json.dumps(stop_config))
                
                # Close connection
                await self.ws.close()
                logger.info(f"✅ WebSocket disconnected cleanly for server {self.server_id}")
                
            except Exception as e:
                logger.warning(f"⚠️ Error during disconnect for server {self.server_id}: {e}")
    
    def get_recent_messages(self, limit=50, message_type=None):
        """
        Get recent messages from buffer
        
        Args:
            limit (int): Maximum number of messages to return
            message_type (str): Filter by message type, None for all
            
        Returns:
            list: List of recent messages
        """
        messages = list(self.message_buffer)
        
        # Filter by type if specified
        if message_type and message_type != "all":
            messages = [msg for msg in messages if msg.get("type") == message_type]
        
        # Sort by timestamp (most recent last)
        messages.sort(key=lambda x: x.get("timestamp", ""))
        
        # Return requested number of messages
        return messages[-limit:] if limit else messages
    
    def get_connection_info(self):
        """
        ✅ EXTENDED: Get connection information including sensor data status
        
        Returns:
            dict: Connection status and info
        """
        return {
            "server_id": self.server_id,
            "region": self.region,
            "connected": self.connected,
            "running": self.running,
            "is_test": self.is_test,
            "message_count": len(self.message_buffer),
            "reconnect_attempts": self.reconnect_attempts,
            "max_reconnect_attempts": self.max_reconnect_attempts,
            # ✅ NEW: Sensor data status
            "has_sensor_data": self.latest_sensor_data is not None,
            "sensor_data_fresh": self.is_sensor_data_fresh(),
            "sensor_data_timestamp": self.sensor_data_timestamp,
            "has_config_data": self.latest_config_data is not None,
            "sensor_callbacks_count": len(self.sensor_callbacks)
        }