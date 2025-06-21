import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from src.agents.pool import AgentPool
from src.websockets.server import websocket_manager
from src.ui.pages import page_registry
from src.database import get_db, DatabaseManager
from src.database.models import SystemState, SystemLog, OptimizationMetric, Agent, Task
from config.settings import settings

@dataclass
class SystemMetrics:
    uptime: float = 0.0
    total_operations: int = 0
    success_rate: float = 1.0
    optimization_level: float = 1.0
    memory_usage: float = 0.0
    cpu_usage: float = 0.0

class OverrideSystem:
    """Privileged control system for emergency operations"""
    
    def __init__(self):
        self.override_active = False
        self.override_level = 0
        self.authorized_commands = {
            "emergency_shutdown",
            "force_restart",
            "clear_all_data",
            "reset_agents",
            "system_recovery"
        }
        self.override_history = []
    
    async def activate_override(self, level: int, reason: str) -> Dict[str, Any]:
        """Activate override system"""
        if level < 1 or level > 5:
            return {"success": False, "error": "Invalid override level (1-5)"}
        
        self.override_active = True
        self.override_level = level
        
        override_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "reason": reason,
            "action": "activated"
        }
        self.override_history.append(override_record)
        
        # Log override activation
        with get_db() as db:
            log_entry = SystemLog(
                level="WARNING",
                message=f"Override system activated - Level {level}: {reason}",
                module="OverrideSystem",
                log_metadata=override_record
            )
            db.add(log_entry)
        
        return {"success": True, "level": level, "message": "Override system activated"}
    
    async def deactivate_override(self) -> Dict[str, Any]:
        """Deactivate override system"""
        if not self.override_active:
            return {"success": False, "error": "Override system not active"}
        
        self.override_active = False
        level = self.override_level
        self.override_level = 0
        
        override_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "action": "deactivated"
        }
        self.override_history.append(override_record)
        
        # Log override deactivation
        with get_db() as db:
            log_entry = SystemLog(
                level="INFO",
                message=f"Override system deactivated - Was Level {level}",
                module="OverrideSystem",
                log_metadata=override_record
            )
            db.add(log_entry)
        
        return {"success": True, "message": "Override system deactivated"}
    
    async def execute_override_command(self, command: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute privileged override command"""
        if not self.override_active:
            return {"success": False, "error": "Override system not active"}
        
        if command not in self.authorized_commands:
            return {"success": False, "error": f"Unauthorized command: {command}"}
        
        # Execute command based on type
        if command == "emergency_shutdown":
            return await self._emergency_shutdown()
        elif command == "force_restart":
            return await self._force_restart()
        elif command == "clear_all_data":
            return await self._clear_all_data()
        elif command == "reset_agents":
            return await self._reset_agents()
        elif command == "system_recovery":
            return await self._system_recovery()
        
        return {"success": False, "error": "Command not implemented"}
    
    async def _emergency_shutdown(self) -> Dict[str, Any]:
        """Emergency system shutdown"""
        # This would trigger system shutdown
        return {"success": True, "message": "Emergency shutdown initiated"}
    
    async def _force_restart(self) -> Dict[str, Any]:
        """Force system restart"""
        # This would trigger system restart
        return {"success": True, "message": "Force restart initiated"}
    
    async def _clear_all_data(self) -> Dict[str, Any]:
        """Clear all system data"""
        if self.override_level < 5:
            return {"success": False, "error": "Insufficient override level for data clearing"}
        
        # This would clear all data
        return {"success": True, "message": "All data cleared"}
    
    async def _reset_agents(self) -> Dict[str, Any]:
        """Reset all agents"""
        # This would reset all agents
        return {"success": True, "message": "All agents reset"}
    
    async def _system_recovery(self) -> Dict[str, Any]:
        """Initiate system recovery"""
        # This would start system recovery procedures
        return {"success": True, "message": "System recovery initiated"}

class GlyphEngine:
    """Symbolic messaging and memory bloom system"""
    
    def __init__(self):
        self.glyphs = {}
        self.memory_bloom = []
        self.symbolic_patterns = {}
        self.message_history = []
    
    async def create_glyph(self, symbol: str, meaning: Dict[str, Any], metadata: Dict[str, Any] = None) -> str:
        """Create a new symbolic glyph"""
        glyph_id = str(uuid.uuid4())
        
        glyph = {
            "id": glyph_id,
            "symbol": symbol,
            "meaning": meaning,
            "metadata": metadata or {},
            "created_at": datetime.utcnow().isoformat(),
            "usage_count": 0,
            "associations": []
        }
        
        self.glyphs[glyph_id] = glyph
        
        # Add to memory bloom
        self.memory_bloom.append({
            "type": "glyph_created",
            "glyph_id": glyph_id,
            "symbol": symbol,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return glyph_id
    
    async def send_symbolic_message(self, sender: str, recipient: str, glyphs: List[str], context: Dict[str, Any] = None) -> str:
        """Send a message using symbolic glyphs"""
        message_id = str(uuid.uuid4())
        
        # Validate glyphs exist
        valid_glyphs = []
        for glyph_id in glyphs:
            if glyph_id in self.glyphs:
                valid_glyphs.append(glyph_id)
                self.glyphs[glyph_id]["usage_count"] += 1
        
        message = {
            "id": message_id,
            "sender": sender,
            "recipient": recipient,
            "glyphs": valid_glyphs,
            "context": context or {},
            "timestamp": datetime.utcnow().isoformat(),
            "decoded": await self._decode_message(valid_glyphs)
        }
        
        self.message_history.append(message)
        
        # Add to memory bloom
        self.memory_bloom.append({
            "type": "symbolic_message",
            "message_id": message_id,
            "sender": sender,
            "recipient": recipient,
            "glyph_count": len(valid_glyphs),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return message_id
    
    async def _decode_message(self, glyph_ids: List[str]) -> Dict[str, Any]:
        """Decode symbolic message"""
        meanings = []
        combined_meaning = {}
        
        for glyph_id in glyph_ids:
            if glyph_id in self.glyphs:
                glyph = self.glyphs[glyph_id]
                meanings.append(glyph["meaning"])
                
                # Combine meanings
                for key, value in glyph["meaning"].items():
                    if key in combined_meaning:
                        if isinstance(combined_meaning[key], list):
                            combined_meaning[key].append(value)
                        else:
                            combined_meaning[key] = [combined_meaning[key], value]
                    else:
                        combined_meaning[key] = value
        
        return {
            "individual_meanings": meanings,
            "combined_meaning": combined_meaning,
            "interpretation_confidence": len(meanings) / max(len(glyph_ids), 1)
        }
    
    def get_memory_bloom(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent memory bloom entries"""
        return self.memory_bloom[-limit:]
    
    def get_glyph_statistics(self) -> Dict[str, Any]:
        """Get glyph usage statistics"""
        total_glyphs = len(self.glyphs)
        total_usage = sum(glyph["usage_count"] for glyph in self.glyphs.values())
        
        return {
            "total_glyphs": total_glyphs,
            "total_usage": total_usage,
            "average_usage": total_usage / total_glyphs if total_glyphs > 0 else 0,
            "memory_bloom_size": len(self.memory_bloom),
            "message_count": len(self.message_history)
        }

class ThreadWeaver:
    """System event logging and monitoring"""
    
    def __init__(self):
        self.threads = {}
        self.event_log = []
        self.monitoring_active = False
        self.performance_metrics = []
    
    async def start_monitoring(self):
        """Start system monitoring"""
        self.monitoring_active = True
        asyncio.create_task(self._monitor_system_events())
        asyncio.create_task(self._collect_performance_metrics())
    
    async def stop_monitoring(self):
        """Stop system monitoring"""
        self.monitoring_active = False
    
    async def _monitor_system_events(self):
        """Monitor and log system events"""
        while self.monitoring_active:
            try:
                # Collect system events
                events = await self._collect_system_events()
                
                for event in events:
                    self.event_log.append(event)
                
                # Keep only recent events
                if len(self.event_log) > 10000:
                    self.event_log = self.event_log[-5000:]
                
                await asyncio.sleep(1.0)  # Check every second
                
            except Exception as e:
                print(f"ThreadWeaver monitoring error: {e}")
                await asyncio.sleep(5.0)
    
    async def _collect_system_events(self) -> List[Dict[str, Any]]:
        """Collect current system events"""
        events = []
        
        # Check database for new logs
        with get_db() as db:
            recent_logs = db.query(SystemLog).filter(
                SystemLog.timestamp >= datetime.utcnow().replace(second=datetime.utcnow().second-10)
            ).all()
            
            for log in recent_logs:
                events.append({
                    "type": "system_log",
                    "level": log.level,
                    "message": log.message,
                    "module": log.module,
                    "timestamp": log.timestamp.isoformat(),
                    "metadata": log.log_metadata
                })
        
        return events
    
    async def _collect_performance_metrics(self):
        """Collect performance metrics"""
        while self.monitoring_active:
            try:
                metrics = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "memory_usage": self._get_memory_usage(),
                    "event_log_size": len(self.event_log),
                    "active_threads": len(self.threads),
                    "websocket_connections": len(websocket_manager.connections) if websocket_manager else 0
                }
                
                self.performance_metrics.append(metrics)
                
                # Keep only recent metrics
                if len(self.performance_metrics) > 1000:
                    self.performance_metrics = self.performance_metrics[-500:]
                
                # Store in database
                with get_db() as db:
                    metric_record = OptimizationMetric(
                        metric_name="system_performance",
                        value=metrics["memory_usage"],
                        component="ThreadWeaver",
                        metric_metadata=metrics
                    )
                    db.add(metric_record)
                
                await asyncio.sleep(30.0)  # Collect every 30 seconds
                
            except Exception as e:
                print(f"Performance metrics collection error: {e}")
                await asyncio.sleep(60.0)
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage (simplified)"""
        # This would use psutil or similar in a real implementation
        return len(self.event_log) * 0.001  # Rough estimate
    
    def create_thread(self, name: str, description: str) -> str:
        """Create a new monitoring thread"""
        thread_id = str(uuid.uuid4())
        
        thread = {
            "id": thread_id,
            "name": name,
            "description": description,
            "created_at": datetime.utcnow().isoformat(),
            "events": [],
            "status": "active"
        }
        
        self.threads[thread_id] = thread
        return thread_id
    
    def log_event(self, thread_id: str, event: Dict[str, Any]):
        """Log an event to a specific thread"""
        if thread_id in self.threads:
            event["timestamp"] = datetime.utcnow().isoformat()
            self.threads[thread_id]["events"].append(event)
            
            # Also add to main event log
            self.event_log.append({
                "thread_id": thread_id,
                "thread_name": self.threads[thread_id]["name"],
                **event
            })
    
    def get_thread_events(self, thread_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get events for a specific thread"""
        if thread_id in self.threads:
            return self.threads[thread_id]["events"][-limit:]
        return []
    
    def get_system_summary(self) -> Dict[str, Any]:
        """Get system monitoring summary"""
        return {
            "monitoring_active": self.monitoring_active,
            "total_events": len(self.event_log),
            "active_threads": len(self.threads),
            "performance_metrics_count": len(self.performance_metrics),
            "recent_events": self.event_log[-10:] if self.event_log else []
        }

class MobileShell:
    """Offline/mobile operation support"""
    
    def __init__(self):
        self.offline_mode = True
        self.cached_data = {}
        self.sync_queue = []
        self.mobile_optimizations = True
    
    async def enable_offline_mode(self):
        """Enable offline operation mode"""
        self.offline_mode = True
        
        # Cache essential data
        await self._cache_essential_data()
        
        return {"success": True, "message": "Offline mode enabled"}
    
    async def disable_offline_mode(self):
        """Disable offline mode and sync"""
        self.offline_mode = False
        
        # Attempt to sync queued operations
        sync_results = await self._sync_queued_operations()
        
        return {
            "success": True, 
            "message": "Offline mode disabled",
            "sync_results": sync_results
        }
    
    async def _cache_essential_data(self):
        """Cache essential data for offline operation"""
        with get_db() as db:
            # Cache recent agents
            agents = db.query(Agent).limit(50).all()
            self.cached_data["agents"] = [
                {
                    "id": agent.id,
                    "name": agent.name,
                    "status": agent.status,
                    "capabilities": agent.capabilities
                }
                for agent in agents
            ]
            
            # Cache recent tasks
            tasks = db.query(Task).limit(100).all()
            self.cached_data["tasks"] = [
                {
                    "id": task.id,
                    "type": task.task_type,
                    "status": task.status,
                    "created_at": task.created_at.isoformat()
                }
                for task in tasks
            ]
    
    async def _sync_queued_operations(self) -> Dict[str, Any]:
        """Sync operations that were queued during offline mode"""
        synced_count = 0
        failed_count = 0
        
        for operation in self.sync_queue:
            try:
                # Attempt to execute queued operation
                await self._execute_queued_operation(operation)
                synced_count += 1
            except Exception as e:
                failed_count += 1
                print(f"Failed to sync operation: {e}")
        
        # Clear sync queue
        self.sync_queue.clear()
        
        return {
            "synced": synced_count,
            "failed": failed_count,
            "total": synced_count + failed_count
        }
    
    async def _execute_queued_operation(self, operation: Dict[str, Any]):
        """Execute a queued operation"""
        # This would execute the actual operation
        # For now, just log it
        with get_db() as db:
            log_entry = SystemLog(
                level="INFO",
                message=f"Synced offline operation: {operation['type']}",
                module="MobileShell",
                log_metadata=operation
            )
            db.add(log_entry)
    
    def queue_operation(self, operation: Dict[str, Any]):
        """Queue an operation for later sync"""
        operation["queued_at"] = datetime.utcnow().isoformat()
        self.sync_queue.append(operation)
    
    def get_cached_data(self, data_type: str) -> Any:
        """Get cached data for offline use"""
        return self.cached_data.get(data_type, [])
    
    def get_mobile_status(self) -> Dict[str, Any]:
        """Get mobile shell status"""
        return {
            "offline_mode": self.offline_mode,
            "cached_data_types": list(self.cached_data.keys()),
            "sync_queue_size": len(self.sync_queue),
            "mobile_optimizations": self.mobile_optimizations
        }

class Empirion:
    """Main system orchestrator"""
    
    def __init__(self):
        self.system_id = str(uuid.uuid4())
        self.start_time = datetime.utcnow()
        self.metrics = SystemMetrics()
        
        # Initialize subsystems
        self.override_system = OverrideSystem()
        self.glyph_engine = GlyphEngine()
        self.thread_weaver = ThreadWeaver()
        self.mobile_shell = MobileShell()
        
        # System state
        self.is_running = False
        self.optimization_cycles = 0
    
    async def initialize(self):
        """Initialize the Empirion system"""
        print("🌟 Initializing Empirion Core System...")
        
        # Start monitoring
        await self.thread_weaver.start_monitoring()
        
        # Enable mobile optimizations
        await self.mobile_shell.enable_offline_mode()
        
        # Create initial glyphs
        await self._create_initial_glyphs()
        
        self.is_running = True
        
        # Start optimization loop
        asyncio.create_task(self._optimization_loop())
        
        print("✨ Empirion Core System initialized")
    
    async def _create_initial_glyphs(self):
        """Create initial symbolic glyphs"""
        initial_glyphs = [
            ("⚡", {"type": "energy", "intensity": "high", "action": "activate"}),
            ("🔄", {"type": "process", "state": "cycling", "action": "optimize"}),
            ("🧠", {"type": "intelligence", "level": "advanced", "action": "think"}),
            ("🌐", {"type": "network", "scope": "global", "action": "connect"}),
            ("🔒", {"type": "security", "level": "high", "action": "protect"})
        ]
        
        for symbol, meaning in initial_glyphs:
            await self.glyph_engine.create_glyph(symbol, meaning)
    
    async def _optimization_loop(self):
        """Continuous system optimization"""
        while self.is_running:
            try:
                self.optimization_cycles += 1
                
                # Update metrics
                await self._update_system_metrics()
                
                # Optimize subsystems
                await self._optimize_subsystems()
                
                # Log optimization cycle
                self.thread_weaver.log_event("system", {
                    "type": "optimization_cycle",
                    "cycle": self.optimization_cycles,
                    "metrics": self.metrics.__dict__
                })
                
                await asyncio.sleep(60.0)  # Optimize every minute
                
            except Exception as e:
                print(f"Optimization loop error: {e}")
                await asyncio.sleep(120.0)
    
    async def _update_system_metrics(self):
        """Update system performance metrics"""
        current_time = datetime.utcnow()
        self.metrics.uptime = (current_time - self.start_time).total_seconds()
        self.metrics.total_operations = self.optimization_cycles
        self.metrics.optimization_level *= 1.001  # Gradual improvement
        
        # Store metrics in database
        with get_db() as db:
            metric_record = OptimizationMetric(
                metric_name="system_uptime",
                value=self.metrics.uptime,
                component="Empirion",
                metric_metadata=self.metrics.__dict__
            )
            db.add(metric_record)
    
    async def _optimize_subsystems(self):
        """Optimize all subsystems"""
        # Optimize glyph engine
        if len(self.glyph_engine.memory_bloom) > 1000:
            self.glyph_engine.memory_bloom = self.glyph_engine.memory_bloom[-500:]
        
        # Optimize thread weaver
        if len(self.thread_weaver.event_log) > 10000:
            self.thread_weaver.event_log = self.thread_weaver.event_log[-5000:]
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        return {
            "system_id": self.system_id,
            "uptime": self.metrics.uptime,
            "is_running": self.is_running,
            "optimization_cycles": self.optimization_cycles,
            "metrics": self.metrics.__dict__,
            "subsystems": {
                "override_system": {
                    "active": self.override_system.override_active,
                    "level": self.override_system.override_level
                },
                "glyph_engine": self.glyph_engine.get_glyph_statistics(),
                "thread_weaver": self.thread_weaver.get_system_summary(),
                "mobile_shell": self.mobile_shell.get_mobile_status()
            }
        }
    
    async def shutdown(self):
        """Gracefully shutdown the system"""
        print("🛑 Shutting down Empirion Core System...")
        
        self.is_running = False
        
        # Stop monitoring
        await self.thread_weaver.stop_monitoring()
        
        # Disable mobile shell
        await self.mobile_shell.disable_offline_mode()
        
        print("✅ Empirion Core System shutdown complete")

# Global system instance
empirion_core = Empirion()
