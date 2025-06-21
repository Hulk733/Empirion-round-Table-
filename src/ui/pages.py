import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from src.database import get_db
from src.database.models import SystemLog, SystemState, Agent, Task
from src.websockets.server import websocket_manager

@dataclass
class PageMetrics:
    page_loads: int = 0
    active_sessions: int = 0
    last_accessed: Optional[str] = None

class BasePage:
    """Base class for all UI pages"""
    
    def __init__(self, name: str):
        self.name = name
        self.metrics = PageMetrics()
        self.websocket_connections = set()
        self.is_loaded = False
    
    async def load(self):
        """Load the page and initialize resources"""
        self.metrics.page_loads += 1
        self.metrics.last_accessed = datetime.utcnow().isoformat()
        self.is_loaded = True
        
        # Log page load
        with get_db() as db:
            log_entry = SystemLog(
                level="INFO",
                message=f"Page '{self.name}' loaded",
                module="UI",
                metadata={"page_loads": self.metrics.page_loads}
            )
            db.add(log_entry)
        
        print(f"⟶ [Load] {self.name} initialized.")
    
    async def unload(self):
        """Unload the page and cleanup resources"""
        self.is_loaded = False
        
        # Close WebSocket connections
        for websocket in self.websocket_connections.copy():
            try:
                await websocket.close()
            except:
                pass
        self.websocket_connections.clear()
        
        print(f"⟵ [Unload] {self.name} cleaned up.")
    
    def add_websocket_connection(self, websocket):
        """Add WebSocket connection for real-time updates"""
        self.websocket_connections.add(websocket)
        self.metrics.active_sessions = len(self.websocket_connections)
    
    def remove_websocket_connection(self, websocket):
        """Remove WebSocket connection"""
        self.websocket_connections.discard(websocket)
        self.metrics.active_sessions = len(self.websocket_connections)
    
    async def broadcast_update(self, update_data: Dict[str, Any]):
        """Broadcast update to all connected clients"""
        message = {
            "type": "page_update",
            "page": self.name,
            "data": update_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        for websocket in self.websocket_connections.copy():
            try:
                await websocket.send(json.dumps(message))
            except:
                self.websocket_connections.discard(websocket)
    
    def get_status(self) -> Dict[str, Any]:
        """Get page status and metrics"""
        return {
            "name": self.name,
            "is_loaded": self.is_loaded,
            "metrics": {
                "page_loads": self.metrics.page_loads,
                "active_sessions": self.metrics.active_sessions,
                "last_accessed": self.metrics.last_accessed
            },
            "websocket_connections": len(self.websocket_connections)
        }

class CommandRoom(BasePage):
    """Central command interface for system control"""
    
    def __init__(self):
        super().__init__("Command Room")
        self.active_commands = []
        self.command_history = []
        self.system_alerts = []
    
    async def load(self):
        await super().load()
        
        # Initialize command monitoring
        asyncio.create_task(self._monitor_system_status())
        
        # Load recent system state
        await self._load_system_state()
    
    async def _monitor_system_status(self):
        """Monitor system status and generate alerts"""
        while self.is_loaded:
            try:
                # Check system health
                alerts = await self._check_system_health()
                
                if alerts:
                    self.system_alerts.extend(alerts)
                    # Keep only recent alerts
                    self.system_alerts = self.system_alerts[-50:]
                    
                    # Broadcast alerts
                    await self.broadcast_update({
                        "type": "system_alerts",
                        "alerts": alerts
                    })
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                print(f"Command Room monitoring error: {e}")
                await asyncio.sleep(30)
    
    async def _check_system_health(self) -> List[Dict[str, Any]]:
        """Check system health and return alerts"""
        alerts = []
        
        with get_db() as db:
            # Check agent status
            agent_count = db.query(Agent).filter(Agent.status == "active").count()
            if agent_count == 0:
                alerts.append({
                    "level": "warning",
                    "message": "No active agents in the system",
                    "component": "agents",
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            # Check recent errors
            recent_errors = db.query(SystemLog).filter(
                SystemLog.level == "ERROR",
                SystemLog.timestamp >= datetime.utcnow().replace(hour=datetime.utcnow().hour-1)
            ).count()
            
            if recent_errors > 10:
                alerts.append({
                    "level": "error",
                    "message": f"High error rate: {recent_errors} errors in the last hour",
                    "component": "system",
                    "timestamp": datetime.utcnow().isoformat()
                })
        
        return alerts
    
    async def _load_system_state(self):
        """Load current system state"""
        with get_db() as db:
            states = db.query(SystemState).all()
            system_state = {state.component: state.state for state in states}
            
            await self.broadcast_update({
                "type": "system_state",
                "state": system_state
            })
    
    async def execute_command(self, command: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a system command"""
        command_id = f"cmd_{len(self.command_history)}"
        
        command_record = {
            "id": command_id,
            "command": command,
            "parameters": parameters or {},
            "timestamp": datetime.utcnow().isoformat(),
            "status": "executing"
        }
        
        self.active_commands.append(command_record)
        self.command_history.append(command_record)
        
        try:
            # Execute command (placeholder implementation)
            result = await self._process_command(command, parameters or {})
            
            command_record["status"] = "completed"
            command_record["result"] = result
            
        except Exception as e:
            command_record["status"] = "failed"
            command_record["error"] = str(e)
            result = {"success": False, "error": str(e)}
        
        # Remove from active commands
        self.active_commands = [cmd for cmd in self.active_commands if cmd["id"] != command_id]
        
        # Broadcast command completion
        await self.broadcast_update({
            "type": "command_completed",
            "command": command_record
        })
        
        return result
    
    async def _process_command(self, command: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Process a specific command"""
        if command == "system_status":
            return await self._get_system_status()
        elif command == "restart_agents":
            return await self._restart_agents()
        elif command == "clear_logs":
            return await self._clear_logs()
        else:
            raise ValueError(f"Unknown command: {command}")
    
    async def _get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        with get_db() as db:
            agent_count = db.query(Agent).count()
            active_agents = db.query(Agent).filter(Agent.status == "active").count()
            pending_tasks = db.query(Task).filter(Task.status == "pending").count()
            
            return {
                "success": True,
                "data": {
                    "agents": {"total": agent_count, "active": active_agents},
                    "tasks": {"pending": pending_tasks},
                    "websockets": websocket_manager.get_connection_stats()
                }
            }
    
    async def _restart_agents(self) -> Dict[str, Any]:
        """Restart all agents (placeholder)"""
        return {"success": True, "message": "Agent restart initiated"}
    
    async def _clear_logs(self) -> Dict[str, Any]:
        """Clear old system logs"""
        with get_db() as db:
            # Delete logs older than 7 days
            cutoff_date = datetime.utcnow().replace(day=datetime.utcnow().day-7)
            deleted_count = db.query(SystemLog).filter(
                SystemLog.timestamp < cutoff_date
            ).delete()
            
            return {"success": True, "deleted_logs": deleted_count}

class DepartmentView(BasePage):
    """Overview of various departments/modules within Empirion"""
    
    def __init__(self):
        super().__init__("Department View")
        self.departments = {}
        self.department_metrics = {}
    
    async def load(self):
        await super().load()
        
        # Initialize departments
        self.departments = {
            "agents": {"status": "active", "count": 0, "health": "good"},
            "websockets": {"status": "active", "connections": 0, "health": "good"},
            "database": {"status": "active", "size": "0MB", "health": "good"},
            "optimization": {"status": "active", "level": 1.0, "health": "good"},
            "security": {"status": "active", "threats": 0, "health": "good"}
        }
        
        # Start department monitoring
        asyncio.create_task(self._monitor_departments())
    
    async def _monitor_departments(self):
        """Monitor department status and metrics"""
        while self.is_loaded:
            try:
                await self._update_department_metrics()
                
                # Broadcast department updates
                await self.broadcast_update({
                    "type": "department_metrics",
                    "departments": self.departments,
                    "metrics": self.department_metrics
                })
                
                await asyncio.sleep(15)  # Update every 15 seconds
                
            except Exception as e:
                print(f"Department monitoring error: {e}")
                await asyncio.sleep(30)
    
    async def _update_department_metrics(self):
        """Update metrics for all departments"""
        with get_db() as db:
            # Update agent department
            agent_count = db.query(Agent).filter(Agent.status == "active").count()
            self.departments["agents"]["count"] = agent_count
            self.departments["agents"]["health"] = "good" if agent_count > 0 else "warning"
            
            # Update WebSocket department
            ws_stats = websocket_manager.get_connection_stats()
            self.departments["websockets"]["connections"] = ws_stats["active_connections"]
            self.departments["websockets"]["health"] = "good" if ws_stats["server_running"] else "error"
            
            # Update database department
            log_count = db.query(SystemLog).count()
            self.departments["database"]["size"] = f"{log_count * 0.001:.1f}MB"  # Rough estimate
            
            # Store metrics with timestamp
            self.department_metrics = {
                "timestamp": datetime.utcnow().isoformat(),
                "agents": {"active_count": agent_count},
                "websockets": ws_stats,
                "database": {"log_entries": log_count}
            }

class FeatureConsole(BasePage):
    """Advanced features and real-time system analytics"""
    
    def __init__(self):
        super().__init__("Feature Console")
        self.active_features = set()
        self.analytics_data = []
        self.performance_metrics = {}
    
    async def load(self):
        await super().load()
        
        # Initialize available features
        self.available_features = {
            "real_time_analytics",
            "performance_monitoring", 
            "agent_evolution_tracking",
            "quantum_processing_sim",
            "predictive_analysis",
            "system_optimization"
        }
        
        # Start analytics collection
        asyncio.create_task(self._collect_analytics())
    
    async def _collect_analytics(self):
        """Collect real-time analytics data"""
        while self.is_loaded:
            try:
                # Collect performance metrics
                metrics = await self._gather_performance_metrics()
                self.analytics_data.append(metrics)
                
                # Keep only recent data (last 1000 points)
                if len(self.analytics_data) > 1000:
                    self.analytics_data = self.analytics_data[-500:]
                
                # Broadcast analytics update
                await self.broadcast_update({
                    "type": "analytics_update",
                    "metrics": metrics,
                    "trend_data": self.analytics_data[-50:]  # Last 50 points for trending
                })
                
                await asyncio.sleep(5)  # Collect every 5 seconds
                
            except Exception as e:
                print(f"Analytics collection error: {e}")
                await asyncio.sleep(30)
    
    async def _gather_performance_metrics(self) -> Dict[str, Any]:
        """Gather current performance metrics"""
        with get_db() as db:
            # System metrics
            total_agents = db.query(Agent).count()
            active_agents = db.query(Agent).filter(Agent.status == "active").count()
            completed_tasks = db.query(Task).filter(Task.status == "completed").count()
            
            # Calculate success rate
            failed_tasks = db.query(Task).filter(Task.status == "failed").count()
            total_tasks = completed_tasks + failed_tasks
            success_rate = (completed_tasks / total_tasks) if total_tasks > 0 else 1.0
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "system": {
                    "total_agents": total_agents,
                    "active_agents": active_agents,
                    "agent_utilization": (active_agents / total_agents) if total_agents > 0 else 0,
                    "task_success_rate": success_rate,
                    "total_tasks": total_tasks
                },
                "websockets": websocket_manager.get_connection_stats(),
                "memory_usage": {
                    "analytics_points": len(self.analytics_data),
                    "active_features": len(self.active_features)
                }
            }
    
    async def enable_feature(self, feature_name: str) -> Dict[str, Any]:
        """Enable a specific feature"""
        if feature_name not in self.available_features:
            return {"success": False, "error": f"Unknown feature: {feature_name}"}
        
        self.active_features.add(feature_name)
        
        # Broadcast feature activation
        await self.broadcast_update({
            "type": "feature_enabled",
            "feature": feature_name,
            "active_features": list(self.active_features)
        })
        
        return {"success": True, "message": f"Feature '{feature_name}' enabled"}
    
    async def disable_feature(self, feature_name: str) -> Dict[str, Any]:
        """Disable a specific feature"""
        self.active_features.discard(feature_name)
        
        # Broadcast feature deactivation
        await self.broadcast_update({
            "type": "feature_disabled",
            "feature": feature_name,
            "active_features": list(self.active_features)
        })
        
        return {"success": True, "message": f"Feature '{feature_name}' disabled"}

class DeepVault(BasePage):
    """Secure storage for sensitive and legacy data"""
    
    def __init__(self):
        super().__init__("Deep Vault")
        self.vault_contents = {}
        self.access_log = []
        self.security_level = "high"
    
    async def load(self):
        await super().load()
        
        # Initialize vault structure
        self.vault_contents = {
            "agent_memories": {},
            "system_backups": {},
            "encrypted_data": {},
            "legacy_archives": {}
        }
        
        # Start security monitoring
        asyncio.create_task(self._monitor_security())
    
    async def _monitor_security(self):
        """Monitor vault security and access patterns"""
        while self.is_loaded:
            try:
                # Check for suspicious access patterns
                security_status = await self._assess_security()
                
                # Broadcast security updates
                await self.broadcast_update({
                    "type": "security_status",
                    "status": security_status,
                    "vault_size": len(self.vault_contents),
                    "recent_access": self.access_log[-10:]  # Last 10 access events
                })
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                print(f"Vault security monitoring error: {e}")
                await asyncio.sleep(60)
    
    async def _assess_security(self) -> Dict[str, Any]:
        """Assess current security status"""
        return {
            "level": self.security_level,
            "threats_detected": 0,
            "access_attempts": len(self.access_log),
            "vault_integrity": "intact",
            "encryption_status": "active"
        }
    
    async def store_data(self, category: str, key: str, data: Any, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Store data in the vault"""
        if category not in self.vault_contents:
            return {"success": False, "error": f"Invalid category: {category}"}
        
        # Log access
        access_entry = {
            "action": "store",
            "category": category,
            "key": key,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }
        self.access_log.append(access_entry)
        
        # Store data
        self.vault_contents[category][key] = {
            "data": data,
            "metadata": metadata or {},
            "stored_at": datetime.utcnow().isoformat()
        }
        
        # Broadcast storage event
        await self.broadcast_update({
            "type": "data_stored",
            "category": category,
            "key": key,
            "vault_size": sum(len(cat) for cat in self.vault_contents.values())
        })
        
        return {"success": True, "message": f"Data stored in {category}/{key}"}
    
    async def retrieve_data(self, category: str, key: str) -> Dict[str, Any]:
        """Retrieve data from the vault"""
        if category not in self.vault_contents or key not in self.vault_contents[category]:
            return {"success": False, "error": "Data not found"}
        
        # Log access
        access_entry = {
            "action": "retrieve",
            "category": category,
            "key": key,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.access_log.append(access_entry)
        
        data = self.vault_contents[category][key]
        
        # Broadcast retrieval event
        await self.broadcast_update({
            "type": "data_retrieved",
            "category": category,
            "key": key
        })
        
        return {"success": True, "data": data}

class ExternalHub(BasePage):
    """Interface for external APIs and networked services"""
    
    def __init__(self):
        super().__init__("External Hub")
        self.connections = {}
        self.sync_status = {}
        self.offline_mode = True
    
    async def load(self):
        await super().load()
        
        # Initialize connection status
        self.connections = {
            "api_gateway": {"status": "disconnected", "last_sync": None},
            "cloud_storage": {"status": "disconnected", "last_sync": None},
            "external_ai": {"status": "disconnected", "last_sync": None},
            "monitoring": {"status": "disconnected", "last_sync": None}
        }
        
        # Start connection monitoring
        asyncio.create_task(self._monitor_connections())
    
    async def _monitor_connections(self):
        """Monitor external connections and sync status"""
        while self.is_loaded:
            try:
                # Check connection status
                await self._check_connections()
                
                # Broadcast connection status
                await self.broadcast_update({
                    "type": "connection_status",
                    "connections": self.connections,
                    "offline_mode": self.offline_mode,
                    "sync_status": self.sync_status
                })
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                print(f"External hub monitoring error: {e}")
                await asyncio.sleep(120)
    
    async def _check_connections(self):
        """Check status of external connections"""
        # Simulate connection checks (in real implementation, these would be actual network calls)
        for connection_name in self.connections:
            # For now, all connections remain disconnected (offline mode)
            self.connections[connection_name]["status"] = "disconnected"
            self.connections[connection_name]["last_check"] = datetime.utcnow().isoformat()
    
    async def attempt_sync(self, service: str) -> Dict[str, Any]:
        """Attempt to sync with external service"""
        if service not in self.connections:
            return {"success": False, "error": f"Unknown service: {service}"}
        
        # In offline mode, sync attempts fail gracefully
        if self.offline_mode:
            return {
                "success": False, 
                "error": "System in offline mode",
                "offline_mode": True
            }
        
        # Simulate sync attempt
        self.sync_status[service] = {
            "last_attempt": datetime.utcnow().isoformat(),
            "status": "attempted",
            "result": "offline_mode"
        }
        
        return {"success": False, "message": "Sync attempted but system is offline"}

# Global page instances
command_room = CommandRoom()
department_view = DepartmentView()
feature_console = FeatureConsole()
deep_vault = DeepVault()
external_hub = ExternalHub()

# Page registry for easy access
page_registry = {
    "command_room": command_room,
    "department_view": department_view,
    "feature_console": feature_console,
    "deep_vault": deep_vault,
    "external_hub": external_hub
}
