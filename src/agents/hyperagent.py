import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
import numpy as np
from dataclasses import dataclass, field

from src.database import get_db
from src.database.models import Agent, Task, SystemLog
from config.settings import settings

@dataclass
class AgentCapability:
    name: str
    level: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AgentMemory:
    short_term: List[Dict[str, Any]] = field(default_factory=list)
    long_term: List[Dict[str, Any]] = field(default_factory=list)
    working: Dict[str, Any] = field(default_factory=dict)

class InfiniteCore:
    """Core processing unit for infinite optimization"""
    
    def __init__(self):
        self.optimization_level = float('inf')
        self.processing_matrix = np.random.rand(100, 100)
        self.quantum_state = {"entangled": True, "coherence": 1.0}
        self.evolution_cycles = 0
    
    async def optimize(self):
        """Continuous optimization process"""
        while True:
            self.evolution_cycles += 1
            self.optimization_level *= 1.001  # Gradual improvement
            
            # Quantum state evolution
            self.quantum_state["coherence"] *= 0.999
            if self.quantum_state["coherence"] < 0.5:
                self.quantum_state["coherence"] = 1.0  # Reset coherence
            
            # Matrix optimization
            self.processing_matrix = np.random.rand(100, 100) * self.optimization_level
            
            await asyncio.sleep(0.1)  # Non-blocking optimization
    
    def get_optimization_metrics(self) -> Dict[str, Any]:
        return {
            "optimization_level": self.optimization_level,
            "evolution_cycles": self.evolution_cycles,
            "quantum_coherence": self.quantum_state["coherence"],
            "matrix_complexity": np.mean(self.processing_matrix)
        }

class HyperAgent:
    """Advanced AI agent with evolution capabilities"""
    
    def __init__(self, name: str, agent_type: str = "HyperAgent"):
        self.id = str(uuid.uuid4())
        self.name = name
        self.agent_type = agent_type
        self.evolution_factor = 1.0
        self.status = "initializing"
        
        # Core systems
        self.core = InfiniteCore()
        self.memory = AgentMemory()
        self.capabilities = self._initialize_capabilities()
        
        # Performance metrics
        self.tasks_completed = 0
        self.success_rate = 1.0
        self.learning_rate = 0.01
        
        # Evolution tracking
        self.generation = 1
        self.mutations = []
        self.adaptation_history = []
        
        # WebSocket connections for this agent
        self.websocket_connections = set()
        
    def _initialize_capabilities(self) -> List[AgentCapability]:
        """Initialize agent capabilities"""
        base_capabilities = [
            AgentCapability("quantum_processing", 1.0),
            AgentCapability("pattern_recognition", 1.0),
            AgentCapability("adaptive_learning", 1.0),
            AgentCapability("memory_optimization", 1.0),
            AgentCapability("task_execution", 1.0),
            AgentCapability("communication", 1.0),
            AgentCapability("self_modification", 0.5),
            AgentCapability("predictive_analysis", 0.8)
        ]
        return base_capabilities
    
    async def initialize(self):
        """Initialize agent in database and start core processes"""
        with get_db() as db:
            # Create agent record
            agent_record = Agent(
                id=self.id,
                name=self.name,
                agent_type=self.agent_type,
                status="active",
                evolution_factor=self.evolution_factor,
                capabilities=[cap.name for cap in self.capabilities],
                metadata={
                    "generation": self.generation,
                    "learning_rate": self.learning_rate,
                    "initialization_time": datetime.utcnow().isoformat()
                }
            )
            db.add(agent_record)
            
            # Log initialization
            log_entry = SystemLog(
                agent_id=self.id,
                level="INFO",
                message=f"Agent {self.name} initialized with {len(self.capabilities)} capabilities",
                module="HyperAgent",
                metadata={"capabilities": [cap.name for cap in self.capabilities]}
            )
            db.add(log_entry)
        
        self.status = "active"
        
        # Start core optimization
        asyncio.create_task(self.core.optimize())
        asyncio.create_task(self._evolution_loop())
        
    async def _evolution_loop(self):
        """Continuous evolution and adaptation"""
        while self.status == "active":
            await self._evolve()
            await asyncio.sleep(settings.agent_evolution_interval)
    
    async def _evolve(self):
        """Evolve agent capabilities and performance"""
        # Increase evolution factor
        self.evolution_factor *= 1.01
        
        # Evolve capabilities
        for capability in self.capabilities:
            if np.random.random() < 0.1:  # 10% chance of capability evolution
                capability.level *= (1 + np.random.normal(0, 0.05))
                capability.level = max(0.1, min(10.0, capability.level))  # Bounds
        
        # Adapt learning rate based on performance
        if self.success_rate > 0.8:
            self.learning_rate *= 1.05
        elif self.success_rate < 0.5:
            self.learning_rate *= 0.95
        
        # Record adaptation
        adaptation = {
            "timestamp": datetime.utcnow().isoformat(),
            "evolution_factor": self.evolution_factor,
            "capabilities": {cap.name: cap.level for cap in self.capabilities},
            "learning_rate": self.learning_rate
        }
        self.adaptation_history.append(adaptation)
        
        # Keep only recent adaptations
        if len(self.adaptation_history) > 100:
            self.adaptation_history = self.adaptation_history[-100:]
        
        # Update database
        await self._update_database()
        
        # Broadcast evolution to WebSocket connections
        await self._broadcast_evolution(adaptation)
    
    async def _update_database(self):
        """Update agent state in database"""
        with get_db() as db:
            agent = db.query(Agent).filter(Agent.id == self.id).first()
            if agent:
                agent.evolution_factor = self.evolution_factor
                agent.capabilities = [cap.name for cap in self.capabilities]
                agent.agent_metadata.update({
                    "generation": self.generation,
                    "learning_rate": self.learning_rate,
                    "tasks_completed": self.tasks_completed,
                    "success_rate": self.success_rate,
                    "last_evolution": datetime.utcnow().isoformat()
                })
                agent.updated_at = datetime.utcnow()
    
    async def _broadcast_evolution(self, adaptation: Dict[str, Any]):
        """Broadcast evolution data to WebSocket connections"""
        if self.websocket_connections:
            message = {
                "type": "agent_evolution",
                "agent_id": self.id,
                "agent_name": self.name,
                "data": adaptation
            }
            
            # Send to all connected WebSocket clients
            for websocket in self.websocket_connections.copy():
                try:
                    await websocket.send(json.dumps(message))
                except:
                    self.websocket_connections.discard(websocket)
    
    async def process_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a task with the agent's current capabilities"""
        task_id = str(uuid.uuid4())
        
        # Create task record
        with get_db() as db:
            task_record = Task(
                id=task_id,
                agent_id=self.id,
                task_type=task_data.get("type", "general"),
                status="processing",
                priority=task_data.get("priority", 1),
                data=task_data
            )
            db.add(task_record)
        
        try:
            # Simulate task processing with capabilities
            processing_power = sum(cap.level for cap in self.capabilities)
            complexity = task_data.get("complexity", 1.0)
            
            # Processing time based on capability vs complexity
            processing_time = max(0.1, complexity / processing_power)
            await asyncio.sleep(processing_time)
            
            # Generate result based on agent's capabilities
            result = await self._generate_task_result(task_data)
            
            # Update task completion
            with get_db() as db:
                task = db.query(Task).filter(Task.id == task_id).first()
                if task:
                    task.status = "completed"
                    task.result = result
                    task.completed_at = datetime.utcnow()
            
            # Update agent metrics
            self.tasks_completed += 1
            success = result.get("success", True)
            self.success_rate = (self.success_rate * (self.tasks_completed - 1) + (1 if success else 0)) / self.tasks_completed
            
            # Learn from task
            await self._learn_from_task(task_data, result)
            
            return result
            
        except Exception as e:
            # Handle task failure
            with get_db() as db:
                task = db.query(Task).filter(Task.id == task_id).first()
                if task:
                    task.status = "failed"
                    task.result = {"error": str(e), "success": False}
                    task.completed_at = datetime.utcnow()
            
            return {"error": str(e), "success": False}
    
    async def _generate_task_result(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate task result based on agent capabilities"""
        task_type = task_data.get("type", "general")
        
        # Get relevant capabilities for this task type
        relevant_caps = self._get_relevant_capabilities(task_type)
        
        # Calculate processing quality
        quality = min(1.0, sum(cap.level for cap in relevant_caps) / len(relevant_caps) if relevant_caps else 0.5)
        
        # Generate result based on task type
        if task_type == "data_analysis":
            return {
                "analysis": f"Processed {len(task_data.get('data', []))} data points",
                "insights": f"Generated {int(quality * 10)} insights",
                "confidence": quality,
                "success": True
            }
        elif task_type == "pattern_recognition":
            return {
                "patterns_found": int(quality * 5),
                "accuracy": quality,
                "processing_time": 1.0 / quality,
                "success": True
            }
        elif task_type == "optimization":
            return {
                "optimization_improvement": quality * 100,
                "iterations": int(10 / quality),
                "final_score": quality,
                "success": True
            }
        else:
            return {
                "result": f"Task completed with {quality:.2%} efficiency",
                "quality": quality,
                "success": True
            }
    
    def _get_relevant_capabilities(self, task_type: str) -> List[AgentCapability]:
        """Get capabilities relevant to a specific task type"""
        relevance_map = {
            "data_analysis": ["pattern_recognition", "adaptive_learning", "quantum_processing"],
            "pattern_recognition": ["pattern_recognition", "memory_optimization"],
            "optimization": ["quantum_processing", "adaptive_learning", "predictive_analysis"],
            "communication": ["communication", "memory_optimization"],
            "learning": ["adaptive_learning", "memory_optimization", "self_modification"]
        }
        
        relevant_names = relevance_map.get(task_type, ["task_execution"])
        return [cap for cap in self.capabilities if cap.name in relevant_names]
    
    async def _learn_from_task(self, task_data: Dict[str, Any], result: Dict[str, Any]):
        """Learn and adapt from completed task"""
        # Store in memory
        memory_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "task_type": task_data.get("type"),
            "complexity": task_data.get("complexity", 1.0),
            "success": result.get("success", False),
            "quality": result.get("quality", 0.5)
        }
        
        self.memory.short_term.append(memory_entry)
        
        # Move to long-term memory if significant
        if len(self.memory.short_term) > 50:
            significant_memories = [m for m in self.memory.short_term if m["quality"] > 0.8 or not m["success"]]
            self.memory.long_term.extend(significant_memories)
            self.memory.short_term = self.memory.short_term[-25:]  # Keep recent memories
        
        # Adapt capabilities based on performance
        task_type = task_data.get("type", "general")
        relevant_caps = self._get_relevant_capabilities(task_type)
        
        for cap in relevant_caps:
            if result.get("success", False):
                cap.level *= (1 + self.learning_rate * 0.1)
            else:
                cap.level *= (1 - self.learning_rate * 0.05)
            
            # Keep capabilities within bounds
            cap.level = max(0.1, min(10.0, cap.level))
    
    def add_websocket_connection(self, websocket):
        """Add WebSocket connection for real-time updates"""
        self.websocket_connections.add(websocket)
    
    def remove_websocket_connection(self, websocket):
        """Remove WebSocket connection"""
        self.websocket_connections.discard(websocket)
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status and metrics"""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.agent_type,
            "status": self.status,
            "evolution_factor": self.evolution_factor,
            "generation": self.generation,
            "tasks_completed": self.tasks_completed,
            "success_rate": self.success_rate,
            "learning_rate": self.learning_rate,
            "capabilities": {cap.name: cap.level for cap in self.capabilities},
            "core_metrics": self.core.get_optimization_metrics(),
            "memory_usage": {
                "short_term": len(self.memory.short_term),
                "long_term": len(self.memory.long_term),
                "working": len(self.memory.working)
            },
            "websocket_connections": len(self.websocket_connections)
        }
    
    async def shutdown(self):
        """Gracefully shutdown the agent"""
        self.status = "shutting_down"
        
        # Close WebSocket connections
        for websocket in self.websocket_connections.copy():
            try:
                await websocket.close()
            except:
                pass
        self.websocket_connections.clear()
        
        # Update database
        with get_db() as db:
            agent = db.query(Agent).filter(Agent.id == self.id).first()
            if agent:
                agent.status = "inactive"
                agent.updated_at = datetime.utcnow()
            
            # Log shutdown
            log_entry = SystemLog(
                agent_id=self.id,
                level="INFO",
                message=f"Agent {self.name} shutdown gracefully",
                module="HyperAgent",
                metadata={"final_metrics": self.get_status()}
            )
            db.add(log_entry)
        
        self.status = "inactive"
