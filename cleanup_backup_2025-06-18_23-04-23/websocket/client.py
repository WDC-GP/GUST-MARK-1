"""
"""
"""
GUST Bot Enhanced - WebSocket Client
===================================
WebSocket client for G-Portal live console monitoring
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
    """WebSocket client for G-Portal live console monitoring"""
    
    def __init__(self, server_id, region, token, message_callback=None):
        """
        Initialize WebSocket client
        
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
        
    async def connect(self):
        """
        Establish WebSocket connection to G-Portal
        
        Returns:
            bool: True if connection successful
        """
        try:
            uri = Config.WEBSOCKET_URI
            
            logger.info(f"ðŸ”„ Connecting to WebSocket for server {self.server_id} ({self.region})")
            
            # Try different connection methods for compatibility
            try:
                # Method 1: Try with subprotocols parameter (most compatible)
                self.ws = await websockets.connect(
                    uri,
                    subprotocols=["graphql-ws"],
                    ping_interval=Config.WEBSOCKET_PING_INTERVAL,
                    ping_timeout=Config.WEBSOCKET_PING_TIMEOUT
                )
                logger.info(f"âœ… WebSocket connected using method 1 for server {self.server_id}")
                
            except Exception as e1:
                logger.warning(f"âš ï¸ Method 1 failed: {e1}")
                try:
                    # Method 2: Basic connection without extra parameters
                    self.ws = await websockets.connect(uri)
                    logger.info(f"âœ… WebSocket connected using method 2 for server {self.server_id}")
                    
                except Exception as e2:
                    logger.error(f"âŒ All connection methods failed: {e1}, {e2}")
                    raise e2
            
            # Initialize connection with authentication
            init_message = {
                "type": "connection_init",
                "payload": {
                    "authorization": f"Bearer {self.token}"
                }
            }
            
            await self.ws.send(json.dumps(init_message))
            logger.info(f"ðŸ“¤ Sent connection_init for server {self.server_id}")
            
            # Wait for connection acknowledgment
            ack_received = False
            timeout = Config.WEBSOCKET_CONNECTION_TIMEOUT
            start_time = time.time()
            
            logger.info(f"â³ Waiting for connection acknowledgment for server {self.server_id}...")
            
            while not ack_received and (time.time() - start_time) < timeout:
                try:
                    message = await asyncio.wait_for(self.ws.recv(), timeout=2.0)
                    data = json.loads(message)
                    logger.info(f"ðŸ“¨ Received message: {data}")
                    
                    if data.get("type") == "connection_ack":
                        ack_received = True
                        logger.info(f"âœ… WebSocket connection acknowledged for server {self.server_id}")
                        
                        # Subscribe to console messages
                        await self.subscribe_to_console()
                        self.connected = True
                        self.reconnect_attempts = 0
                        break
                        
                except asyncio.TimeoutError:
                    logger.debug(f"â³ Still waiting for ack for server {self.server_id}...")
                    continue
                except json.JSONDecodeError as e:
                    logger.error(f"âŒ JSON decode error: {e}")
                    continue
                except Exception as e:
                    logger.error(f"âŒ Error during connection ack: {e}")
                    break
            
            if not ack_received:
                raise Exception(f"Connection acknowledgment timeout after {timeout}s")
                
            return True
            
        except Exception as e:
            logger.error(f"âŒ WebSocket connection failed for server {self.server_id}: {e}")
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
            logger.info(f"ðŸ“¡ Subscribed to console messages for server {self.server_id}")
        except Exception as e:
            logger.error(f"âŒ Failed to subscribe to console for server {self.server_id}: {e}")
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
        logger.info(f"ðŸ‘‚ Starting message listener for server {self.server_id}")
        
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
                            logger.debug(f"ðŸ“¡ Ping sent to server {self.server_id}")
                        except Exception as ping_error:
                            logger.warning(f"âš ï¸ Ping failed for server {self.server_id}: {ping_error}")
                    continue
                    
                except websockets.exceptions.ConnectionClosed as e:
                    logger.warning(f"âš ï¸ WebSocket connection closed for server {self.server_id}: {e}")
                    self.connected = False
                    break
                except websockets.exceptions.WebSocketException as e:
                    logger.error(f"âŒ WebSocket error for server {self.server_id}: {e}")
                    self.connected = False
                    break
                except Exception as e:
                    logger.error(f"âŒ Error processing message for server {self.server_id}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"âŒ Fatal error in message listener for server {self.server_id}: {e}")
        finally:
            self.connected = False
            self.running = False
            logger.info(f"ðŸ”Œ Message listener stopped for server {self.server_id}")
    
    async def process_message(self, message):
        """Process incoming WebSocket message"""
        try:
            data = json.loads(message)
            
            # Handle different message types
            if data.get("type") == "data":
                stream_id = data.get("id", "")
                if f"console_stream_{self.server_id}" in stream_id:
                    payload = data.get("payload", {})
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
                                    logger.error(f"âŒ Callback error for server {self.server_id}: {callback_error}")
                            
                            logger.info(f"ðŸ“¨ Live console message from {self.server_id}: {message_text[:100]}...")
            
            elif data.get("type") == "error":
                logger.error(f"âŒ WebSocket error for server {self.server_id}: {data}")
                
            elif data.get("type") == "complete":
                logger.info(f"âœ… Subscription completed for server {self.server_id}")
                
        except json.JSONDecodeError:
            logger.error(f"âŒ Invalid JSON message from server {self.server_id}: {message[:100]}...")
        except Exception as e:
            logger.error(f"âŒ Error processing message from server {self.server_id}: {e}")
    
    async def disconnect(self):
        """Cleanly disconnect WebSocket"""
        logger.info(f"ðŸ”Œ Disconnecting WebSocket for server {self.server_id}")
        
        self.running = False
        self.connected = False
        
        if self.ws and self._is_connection_open():
            try:
                # Send stop message for subscription
                stop_message = {
                    "id": f"console_stream_{self.server_id}",
                    "type": "stop"
                }
                await self.ws.send(json.dumps(stop_message))
                
                # Close connection
                await self.ws.close()
                logger.info(f"âœ… WebSocket disconnected cleanly for server {self.server_id}")
                
            except Exception as e:
                logger.warning(f"âš ï¸ Error during disconnect for server {self.server_id}: {e}")
    
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
        Get connection information
        
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
            "max_reconnect_attempts": self.max_reconnect_attempts
        }
