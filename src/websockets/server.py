import asyncio
import json
import uuid
import websockets
from datetime import datetime
from typing import Dict, Set, Any, Optional
from websockets.server import WebSocketServerProtocol

from src.database import get_db
from src.database.models import WebSocketConnection, SystemLog
from config.settings import settings

class WebSocketManager:
    """Manages WebSocket connections and real-time communication"""
    
    def __init__(self):
        self.connections: Dict[str, WebSocketServerProtocol] = {}
        self.connection_metadata: Dict[str, Dict[str, Any]] = {}
        self.subscriptions: Dict[str, Set[str]] = {}  # topic -> connection_ids
        self.server = None
        self.is_running = False
        
        # Message handlers
        self.message_handlers = {
            "subscribe": self._handle_subscribe,
            "unsubscribe": self._handle_unsubscribe,
            "ping": self._handle_ping,
            "agent_command": self._handle_agent_command,
            "system_command": self._handle_system_command,
            "get_status": self._handle_get_status
        }
        
        # Available subscription topics
        self.available_topics = {
            "agent_updates",
            "pool_updates", 
            "system_logs",
            "performance_metrics",
            "task_updates",
            "optimization_metrics"
        }
    
    async def start_server(self):
        """Start the WebSocket server"""
        self.is_running = True
        
        self.server = await websockets.serve(
            self._handle_connection,
            settings.host,
            settings.websocket_port,
            ping_interval=settings.websocket_heartbeat,
            ping_timeout=settings.websocket_heartbeat * 2
        )
        
        # Start cleanup task
        asyncio.create_task(self._cleanup_connections())
        
        print(f"🌐 WebSocket server started on {settings.host}:{settings.websocket_port}")
    
    async def _handle_connection(self, websocket: WebSocketServerProtocol, path: str):
        """Handle new WebSocket connection"""
        connection_id = str(uuid.uuid4())
        
        # Store connection
        self.connections[connection_id] = websocket
        self.connection_metadata[connection_id] = {
            "connected_at": datetime.utcnow().isoformat(),
            "path": path,
            "remote_address": websocket.remote_address,
            "subscriptions": set(),
            "last_ping": datetime.utcnow().isoformat()
        }
        
        # Store in database
        with get_db() as db:
            conn_record = WebSocketConnection(
                connection_id=connection_id,
                client_info={
                    "path": path,
                    "remote_address": str(websocket.remote_address),
                    "user_agent": websocket.request_headers.get("User-Agent", "Unknown")
                }
            )
            db.add(conn_record)
        
        # Send welcome message
        await self._send_to_connection(connection_id, {
            "type": "welcome",
            "connection_id": connection_id,
            "server_info": {
                "name": settings.app_name,
                "version": settings.version,
                "available_topics": list(self.available_topics)
            },
            "timestamp": datetime.utcnow().isoformat()
        })
        
        print(f"🔗 New WebSocket connection: {connection_id}")
        
        try:
            # Handle messages from this connection
            async for message in websocket:
                await self._process_message(connection_id, message)
                
        except websockets.exceptions.ConnectionClosed:
            print(f"🔌 WebSocket connection closed: {connection_id}")
        except Exception as e:
            print(f"❌ WebSocket error for {connection_id}: {e}")
        finally:
            await self._cleanup_connection(connection_id)
    
    async def _process_message(self, connection_id: str, message: str):
        """Process incoming WebSocket message"""
        try:
            data = json.loads(message)
            message_type = data.get("type")
            
            if message_type in self.message_handlers:
                await self.message_handlers[message_type](connection_id, data)
            else:
                await self._send_error(connection_id, f"Unknown message type: {message_type}")
                
        except json.JSONDecodeError:
            await self._send_error(connection_id, "Invalid JSON message")
        except Exception as e:
            await self._send_error(connection_id, f"Message processing error: {str(e)}")
    
    async def _handle_subscribe(self, connection_id: str, data: Dict[str, Any]):
        """Handle subscription request"""
        topic = data.get("topic")
        
        if topic not in self.available_topics:
            await self._send_error(connection_id, f"Invalid topic: {topic}")
            return
        
        # Add subscription
        if topic not in self.subscriptions:
            self.subscriptions[topic] = set()
        
        self.subscriptions[topic].add(connection_id)
        self.connection_metadata[connection_id]["subscriptions"].add(topic)
        
        await self._send_to_connection(connection_id, {
            "type": "subscription_confirmed",
            "topic": topic,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        print(f"📡 Connection {connection_id} subscribed to {topic}")
    
    async def _handle_unsubscribe(self, connection_id: str, data: Dict[str, Any]):
        """Handle unsubscription request"""
        topic = data.get("topic")
        
        if topic in self.subscriptions:
            self.subscriptions[topic].discard(connection_id)
            
        if connection_id in self.connection_metadata:
            self.connection_metadata[connection_id]["subscriptions"].discard(topic)
        
        await self._send_to_connection(connection_id, {
            "type": "unsubscription_confirmed",
            "topic": topic,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def _handle_ping(self, connection_id: str, data: Dict[str, Any]):
        """Handle ping message"""
        self.connection_metadata[connection_id]["last_ping"] = datetime.utcnow().isoformat()
        
        await self._send_to_connection(connection_id, {
            "type": "pong",
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def _handle_agent_command(self, connection_id: str, data: Dict[str, Any]):
        """Handle agent-related commands"""
        command = data.get("command")
        agent_id = data.get("agent_id")
        
        # This would integrate with the AgentPool
        # For now, send acknowledgment
        await self._send_to_connection(connection_id, {
            "type": "command_response",
            "command": command,
            "agent_id": agent_id,
            "status": "received",
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def _handle_system_command(self, connection_id: str, data: Dict[str, Any]):
        """Handle system-level commands"""
        command = data.get("command")
        
        # This would integrate with the main system
        # For now, send acknowledgment
        await self._send_to_connection(connection_id, {
            "type": "system_response",
            "command": command,
            "status": "received",
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def _handle_get_status(self, connection_id: str, data: Dict[str, Any]):
        """Handle status request"""
        status_type = data.get("status_type", "general")
        
        status_data = {
            "type": "status_response",
            "status_type": status_type,
            "data": {
                "websocket_server": {
                    "active_connections": len(self.connections),
                    "total_subscriptions": sum(len(subs) for subs in self.subscriptions.values()),
                    "available_topics": list(self.available_topics)
                }
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self._send_to_connection(connection_id, status_data)
    
    async def _send_to_connection(self, connection_id: str, message: Dict[str, Any]):
        """Send message to specific connection"""
        if connection_id in self.connections:
            try:
                await self.connections[connection_id].send(json.dumps(message))
            except Exception as e:
                print(f"Failed to send to {connection_id}: {e}")
                await self._cleanup_connection(connection_id)
    
    async def _send_error(self, connection_id: str, error_message: str):
        """Send error message to connection"""
        await self._send_to_connection(connection_id, {
            "type": "error",
            "message": error_message,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def broadcast_to_topic(self, topic: str, message: Dict[str, Any]):
        """Broadcast message to all subscribers of a topic"""
        if topic not in self.subscriptions:
            return
        
        message["topic"] = topic
        message["timestamp"] = datetime.utcnow().isoformat()
        
        # Send to all subscribers
        for connection_id in self.subscriptions[topic].copy():
            await self._send_to_connection(connection_id, message)
    
    async def broadcast_to_all(self, message: Dict[str, Any]):
        """Broadcast message to all connections"""
        message["timestamp"] = datetime.utcnow().isoformat()
        
        for connection_id in list(self.connections.keys()):
            await self._send_to_connection(connection_id, message)
    
    async def _cleanup_connection(self, connection_id: str):
        """Clean up a disconnected connection"""
        # Remove from all subscriptions
        for topic_subs in self.subscriptions.values():
            topic_subs.discard(connection_id)
        
        # Remove connection data
        self.connections.pop(connection_id, None)
        self.connection_metadata.pop(connection_id, None)
        
        # Update database
        with get_db() as db:
            conn = db.query(WebSocketConnection).filter(
                WebSocketConnection.connection_id == connection_id
            ).first()
            if conn:
                conn.is_active = False
        
        print(f"🧹 Cleaned up connection: {connection_id}")
    
    async def _cleanup_connections(self):
        """Periodically clean up stale connections"""
        while self.is_running:
            current_time = datetime.utcnow()
            stale_connections = []
            
            for connection_id, metadata in self.connection_metadata.items():
                last_ping = datetime.fromisoformat(metadata["last_ping"])
                if (current_time - last_ping).total_seconds() > settings.websocket_heartbeat * 3:
                    stale_connections.append(connection_id)
            
            for connection_id in stale_connections:
                await self._cleanup_connection(connection_id)
            
            await asyncio.sleep(30)  # Check every 30 seconds
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get WebSocket connection statistics"""
        return {
            "active_connections": len(self.connections),
            "total_subscriptions": sum(len(subs) for subs in self.subscriptions.values()),
            "subscriptions_by_topic": {
                topic: len(subs) for topic, subs in self.subscriptions.items()
            },
            "available_topics": list(self.available_topics),
            "server_running": self.is_running
        }
    
    async def shutdown(self):
        """Shutdown the WebSocket server"""
        print("🛑 Shutting down WebSocket server...")
        self.is_running = False
        
        # Close all connections
        for connection_id in list(self.connections.keys()):
            try:
                await self.connections[connection_id].close()
            except:
                pass
            await self._cleanup_connection(connection_id)
        
        # Close server
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        
        # Log shutdown
        with get_db() as db:
            log_entry = SystemLog(
                level="INFO",
                message="WebSocket server shutdown completed",
                module="WebSocketManager",
                metadata={"final_stats": self.get_connection_stats()}
            )
            db.add(log_entry)
        
        print("✅ WebSocket server shutdown complete")

# Global WebSocket manager instance
websocket_manager = WebSocketManager()
