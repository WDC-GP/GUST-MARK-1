"""
"""
"""
GUST Bot Enhanced - WebSocket Manager
====================================
Manages multiple WebSocket connections for live console monitoring
"""

# Standard library imports
import logging
import threading

# Local imports
from config import WEBSOCKETS_AVAILABLE

# Other imports
from .client import GPortalWebSocketClient
import asyncio




logger = logging.getLogger(__name__)

class WebSocketManager:
    """Manages multiple WebSocket connections"""
    
    def __init__(self, gust_bot):
        """
        Initialize WebSocket manager
        
        Args:
            gust_bot: Reference to main GUST bot instance
        """
        self.gust_bot = gust_bot
        self.connections = {}
        self.loop = None
        self.running = False
        
    def start(self):
        """Start the WebSocket manager in a separate thread"""
        if not self.running and WEBSOCKETS_AVAILABLE:
            self.running = True
            thread = threading.Thread(target=self._run_loop, daemon=True)
            thread.start()
            logger.info("ðŸš€ WebSocket manager started")
        elif not WEBSOCKETS_AVAILABLE:
            logger.warning("âš ï¸ WebSocket manager not started - websockets package not available")
    
    def _run_loop(self):
        """Run the asyncio event loop"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        try:
            self.loop.run_forever()
        except Exception as e:
            logger.error(f"âŒ WebSocket manager loop error: {e}")
        finally:
            self.loop.close()
    
    def add_connection(self, server_id, region, token):
        """
        Add a new WebSocket connection
        
        Args:
            server_id: Server ID (may include test suffix)
            region (str): Server region
            token (str): G-Portal authentication token
            
        Returns:
            Future: Asyncio future for the connection task
        """
        if not WEBSOCKETS_AVAILABLE:
            logger.warning("âš ï¸ Cannot add WebSocket connection - websockets package not available")
            return None
            
        if not self.running:
            self.start()
        
        # Handle server ID properly (remove any test suffixes for storage key)
        storage_key = str(server_id).split('_')[0] if '_' in str(server_id) else str(server_id)
        
        if storage_key in self.connections:
            # Disconnect existing connection
            asyncio.run_coroutine_threadsafe(
                self.connections[storage_key].disconnect(), 
                self.loop
            )
        
        # Create new connection
        client = GPortalWebSocketClient(
            server_id,  # Pass original server_id (may include _test)
            region, 
            token, 
            self._message_callback
        )
        
        self.connections[storage_key] = client
        
        # Start connection in the event loop
        future = asyncio.run_coroutine_threadsafe(
            self._connect_and_listen(client), 
            self.loop
        )
        
        return future
    
    async def _connect_and_listen(self, client):
        """
        Connect and start listening for a client
        
        Args:
            client: GPortalWebSocketClient instance
        """
        try:
            if await client.connect():
                await client.listen_for_messages()
            else:
                logger.error(f"âŒ Failed to connect WebSocket for server {client.server_id}")
        except Exception as e:
            logger.error(f"âŒ Error in connect_and_listen for server {client.server_id}: {e}")
            client.connected = False
    
    async def _message_callback(self, message):
        """
        Callback for processing incoming messages
        
        Args:
            message (dict): Message data from WebSocket
        """
        logger.info(f"ðŸ“¨ WebSocket callback received: {message['message'][:100]}...")
        
        # Process special message types
        await self._process_special_messages(message)
    
    async def _process_special_messages(self, message):
        """
        Process special message types
        
        Args:
            message (dict): Message data
        """
        msg_text = message["message"]
        msg_type = message["type"]
        
        # Process VIP/Auth updates
        if msg_type == "auth" and any(keyword in msg_text for keyword in ["VIP", "Admin", "Moderator"]):
            logger.info(f"ðŸ” Auth levels update detected for server {message['server_id']}")
        
        # Process chat messages
        elif msg_type == "chat":
            logger.info(f"ðŸ’¬ Chat message detected: {msg_text[:50]}...")
        
        # Process save events
        elif msg_type == "save":
            logger.info(f"ðŸ’¾ Server save event for server {message['server_id']}")
        
        # Process errors
        elif msg_type == "error":
            logger.warning(f"âš ï¸ Server error detected: {msg_text[:100]}...")
    
    def remove_connection(self, server_id):
        """
        Remove a WebSocket connection
        
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
            logger.info(f"ðŸ”Œ Removed WebSocket connection for server {storage_key}")
        else:
            logger.warning(f"âš ï¸ No connection found for server {storage_key}")
    
    def get_connection_status(self):
        """
        Get status of all connections
        
        Returns:
            dict: Status information for all connections
        """
        status = {}
        for server_id, client in self.connections.items():
            status[server_id] = {
                "connected": client.connected,
                "running": client.running,
                "message_count": len(client.message_buffer),
                "region": client.region,
                "is_test": client.is_test,
                "reconnect_attempts": client.reconnect_attempts
            }
        return status
    
    def get_messages(self, server_id=None, limit=50, message_type=None):
        """
        Get messages from specific server or all servers
        
        Args:
            server_id (str): Specific server ID, None for all servers
            limit (int): Maximum number of messages
            message_type (str): Filter by message type
            
        Returns:
            list: List of messages
        """
        logger.info(f"ðŸ” get_messages called: server_id={server_id}, limit={limit}, type={message_type}")
        
        if server_id and server_id in self.connections:
            messages = self.connections[server_id].get_recent_messages(limit, message_type)
            logger.info(f"ðŸ“‹ Server {server_id} returned {len(messages)} messages")
            return messages
        else:
            # Get messages from all servers
            all_messages = []
            for server_key, client in self.connections.items():
                client_messages = client.get_recent_messages(limit, message_type)
                all_messages.extend(client_messages)
                logger.info(f"ðŸ“‹ Server {server_key} contributed {len(client_messages)} messages")
            
            # Sort by timestamp and return most recent
            all_messages.sort(key=lambda x: x["timestamp"])
            final_messages = all_messages[-limit:] if limit else all_messages
            logger.info(f"ðŸ“‹ Total combined messages: {len(final_messages)}")
            return final_messages
    
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
        Get overall WebSocket manager statistics
        
        Returns:
            dict: Statistics
        """
        total_connections = len(self.connections)
        active_connections = sum(1 for client in self.connections.values() if client.connected)
        total_messages = sum(len(client.message_buffer) for client in self.connections.values())
        
        return {
            "websockets_available": WEBSOCKETS_AVAILABLE,
            "manager_running": self.running,
            "total_connections": total_connections,
            "active_connections": active_connections,
            "total_messages": total_messages,
            "connection_details": self.get_connection_status()
        }
    
    def disconnect_all(self):
        """Disconnect all WebSocket connections"""
        if not self.loop or self.loop.is_closed():
            return
            
        for server_id in list(self.connections.keys()):
            self.remove_connection(server_id)
        
        logger.info("ðŸ”Œ All WebSocket connections disconnected")
    
    def stop(self):
        """Stop the WebSocket manager"""
        if self.running:
            self.disconnect_all()
            self.running = False
            
            if self.loop and not self.loop.is_closed():
                self.loop.call_soon_threadsafe(self.loop.stop)
            
            logger.info("ðŸ›‘ WebSocket manager stopped")
