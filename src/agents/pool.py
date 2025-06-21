import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass

from src.agents.hyperagent import HyperAgent
from src.database import get_db
from src.database.models import Agent, Task, SystemLog, SystemState
from config.settings import settings

@dataclass
class PoolMetrics:
    total_agents: int = 0
    active_agents: int = 0
    tasks_in_queue: int = 0
    tasks_completed: int = 0
    average_success_rate: float = 0.0
    total_evolution_factor: float = 0.0

class AgentPool:
    """Manages a pool of HyperAgents with load balancing and optimization"""
    
    def __init__(self):
        self.agents: Dict[str, HyperAgent] = {}
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self.metrics = PoolMetrics()
        self.websocket_connections: Set = set()
        self.is_running = False
        self.worker_tasks: List[asyncio.Task] = []
        
        # Load balancing
        self.agent_workloads: Dict[str, int] = {}
        self.round_robin_index = 0
        
        # Performance tracking
        self.performance_history = []
        self.optimization_cycles = 0
        
    async def initialize(self):
        """Initialize the agent pool"""
        self.is_running = True
        
        # Start worker tasks for processing
        for i in range(3):  # 3 worker tasks for parallel processing
            task = asyncio.create_task(self._worker())
            self.worker_tasks.append(task)
        
        # Start monitoring and optimization
        asyncio.create_task(self._monitor_performance())
        asyncio.create_task(self._optimize_pool())
        
        # Update system state
        await self._update_system_state()
        
        print("🤖 AgentPool initialized with worker tasks")
    
    async def create_agent(self, name: str, agent_type: str = "HyperAgent") -> str:
        """Create and add a new agent to the pool"""
        if len(self.agents) >= settings.max_agents:
            raise ValueError(f"Maximum agent limit ({settings.max_agents}) reached")
        
        if name in [agent.name for agent in self.agents.values()]:
            raise ValueError(f"Agent with name '{name}' already exists")
        
        # Create new agent
        agent = HyperAgent(name, agent_type)
        await agent.initialize()
        
        # Add to pool
        self.agents[agent.id] = agent
        self.agent_workloads[agent.id] = 0
        
        # Update metrics
        await self._update_metrics()
        
        # Broadcast agent creation
        await self._broadcast_pool_update("agent_created", {
            "agent_id": agent.id,
            "agent_name": name,
            "agent_type": agent_type
        })
        
        # Log creation
        with get_db() as db:
            log_entry = SystemLog(
                level="INFO",
                message=f"Agent '{name}' created and added to pool",
                module="AgentPool",
                metadata={"agent_id": agent.id, "pool_size": len(self.agents)}
            )
            db.add(log_entry)
        
        return agent.id
    
    async def remove_agent(self, agent_id: str) -> bool:
        """Remove an agent from the pool"""
        if agent_id not in self.agents:
            return False
        
        agent = self.agents[agent_id]
        
        # Gracefully shutdown agent
        await agent.shutdown()
        
        # Remove from pool
        del self.agents[agent_id]
        del self.agent_workloads[agent_id]
        
        # Update metrics
        await self._update_metrics()
        
        # Broadcast agent removal
        await self._broadcast_pool_update("agent_removed", {
            "agent_id": agent_id,
            "agent_name": agent.name
        })
        
        # Log removal
        with get_db() as db:
            log_entry = SystemLog(
                level="INFO",
                message=f"Agent '{agent.name}' removed from pool",
                module="AgentPool",
                metadata={"agent_id": agent_id, "pool_size": len(self.agents)}
            )
            db.add(log_entry)
        
        return True
    
    async def submit_task(self, task_data: Dict[str, Any]) -> str:
        """Submit a task to the agent pool"""
        task_id = str(uuid.uuid4())
        
        # Add task metadata
        task_data.update({
            "task_id": task_id,
            "submitted_at": datetime.utcnow().isoformat(),
            "priority": task_data.get("priority", 1)
        })
        
        # Add to queue
        await self.task_queue.put(task_data)
        
        # Update metrics
        self.metrics.tasks_in_queue = self.task_queue.qsize()
        
        # Broadcast task submission
        await self._broadcast_pool_update("task_submitted", {
            "task_id": task_id,
            "task_type": task_data.get("type", "general"),
            "queue_size": self.metrics.tasks_in_queue
        })
        
        return task_id
    
    async def _worker(self):
        """Worker task for processing queued tasks"""
        while self.is_running:
            try:
                # Get task from queue with timeout
                task_data = await asyncio.wait_for(self.task_queue.get(), timeout=1.0)
                
                # Select best agent for task
                agent = await self._select_agent_for_task(task_data)
                
                if agent:
                    # Increment workload
                    self.agent_workloads[agent.id] += 1
                    
                    # Process task
                    result = await agent.process_task(task_data)
                    
                    # Decrement workload
                    self.agent_workloads[agent.id] -= 1
                    
                    # Update metrics
                    self.metrics.tasks_completed += 1
                    if self.task_queue.qsize() > 0:
                        self.metrics.tasks_in_queue = self.task_queue.qsize()
                    
                    # Broadcast task completion
                    await self._broadcast_pool_update("task_completed", {
                        "task_id": task_data.get("task_id"),
                        "agent_id": agent.id,
                        "agent_name": agent.name,
                        "result": result,
                        "success": result.get("success", False)
                    })
                else:
                    # No available agents, put task back in queue
                    await self.task_queue.put(task_data)
                    await asyncio.sleep(0.5)
                
            except asyncio.TimeoutError:
                # No tasks in queue, continue
                continue
            except Exception as e:
                print(f"Worker error: {e}")
                await asyncio.sleep(1.0)
    
    async def _select_agent_for_task(self, task_data: Dict[str, Any]) -> Optional[HyperAgent]:
        """Select the best agent for a given task"""
        if not self.agents:
            return None
        
        task_type = task_data.get("type", "general")
        task_priority = task_data.get("priority", 1)
        
        # Filter active agents
        active_agents = [agent for agent in self.agents.values() if agent.status == "active"]
        
        if not active_agents:
            return None
        
        # Selection strategy based on task priority
        if task_priority >= 5:  # High priority - use best agent
            return self._select_best_agent(active_agents, task_type)
        elif task_priority >= 3:  # Medium priority - use least loaded capable agent
            return self._select_least_loaded_capable_agent(active_agents, task_type)
        else:  # Low priority - use round robin
            return self._select_round_robin_agent(active_agents)
    
    def _select_best_agent(self, agents: List[HyperAgent], task_type: str) -> HyperAgent:
        """Select agent with highest relevant capabilities"""
        best_agent = None
        best_score = 0
        
        for agent in agents:
            relevant_caps = agent._get_relevant_capabilities(task_type)
            score = sum(cap.level for cap in relevant_caps) * agent.success_rate
            
            if score > best_score:
                best_score = score
                best_agent = agent
        
        return best_agent or agents[0]
    
    def _select_least_loaded_capable_agent(self, agents: List[HyperAgent], task_type: str) -> HyperAgent:
        """Select capable agent with lowest workload"""
        capable_agents = []
        
        for agent in agents:
            relevant_caps = agent._get_relevant_capabilities(task_type)
            avg_capability = sum(cap.level for cap in relevant_caps) / len(relevant_caps) if relevant_caps else 0.5
            
            if avg_capability >= 0.7:  # Minimum capability threshold
                capable_agents.append((agent, self.agent_workloads.get(agent.id, 0)))
        
        if not capable_agents:
            capable_agents = [(agent, self.agent_workloads.get(agent.id, 0)) for agent in agents]
        
        # Sort by workload (ascending)
        capable_agents.sort(key=lambda x: x[1])
        return capable_agents[0][0]
    
    def _select_round_robin_agent(self, agents: List[HyperAgent]) -> HyperAgent:
        """Select agent using round-robin strategy"""
        if not agents:
            return None
        
        agent = agents[self.round_robin_index % len(agents)]
        self.round_robin_index += 1
        return agent
    
    async def _monitor_performance(self):
        """Monitor pool performance and collect metrics"""
        while self.is_running:
            await self._update_metrics()
            
            # Record performance snapshot
            snapshot = {
                "timestamp": datetime.utcnow().isoformat(),
                "metrics": {
                    "total_agents": self.metrics.total_agents,
                    "active_agents": self.metrics.active_agents,
                    "tasks_in_queue": self.metrics.tasks_in_queue,
                    "tasks_completed": self.metrics.tasks_completed,
                    "average_success_rate": self.metrics.average_success_rate,
                    "total_evolution_factor": self.metrics.total_evolution_factor
                },
                "agent_workloads": self.agent_workloads.copy()
            }
            
            self.performance_history.append(snapshot)
            
            # Keep only recent history
            if len(self.performance_history) > 1000:
                self.performance_history = self.performance_history[-500:]
            
            # Broadcast performance update
            await self._broadcast_pool_update("performance_update", snapshot)
            
            await asyncio.sleep(5.0)  # Update every 5 seconds
    
    async def _optimize_pool(self):
        """Optimize pool performance and agent distribution"""
        while self.is_running:
            self.optimization_cycles += 1
            
            # Auto-scaling based on queue size
            if self.metrics.tasks_in_queue > len(self.agents) * 5 and len(self.agents) < settings.max_agents:
                # Create additional agent if queue is too long
                agent_name = f"auto_agent_{self.optimization_cycles}"
                try:
                    await self.create_agent(agent_name)
                    print(f"🔄 Auto-created agent: {agent_name}")
                except Exception as e:
                    print(f"Failed to auto-create agent: {e}")
            
            # Remove underperforming agents (if we have enough agents)
            if len(self.agents) > 3:
                await self._remove_underperforming_agents()
            
            # Optimize agent capabilities
            await self._optimize_agent_capabilities()
            
            await asyncio.sleep(30.0)  # Optimize every 30 seconds
    
    async def _remove_underperforming_agents(self):
        """Remove agents with consistently poor performance"""
        for agent in list(self.agents.values()):
            if (agent.success_rate < 0.3 and 
                agent.tasks_completed > 10 and 
                len(self.agents) > 3):
                
                print(f"🗑️ Removing underperforming agent: {agent.name}")
                await self.remove_agent(agent.id)
    
    async def _optimize_agent_capabilities(self):
        """Optimize agent capabilities based on task patterns"""
        # Analyze recent task types
        task_type_frequency = {}
        
        # This would analyze completed tasks to optimize capabilities
        # For now, we'll just ensure agents maintain good performance
        for agent in self.agents.values():
            if agent.success_rate < 0.7:
                # Boost learning rate for struggling agents
                agent.learning_rate = min(0.1, agent.learning_rate * 1.1)
    
    async def _update_metrics(self):
        """Update pool metrics"""
        self.metrics.total_agents = len(self.agents)
        self.metrics.active_agents = len([a for a in self.agents.values() if a.status == "active"])
        self.metrics.tasks_in_queue = self.task_queue.qsize()
        
        if self.agents:
            self.metrics.average_success_rate = sum(a.success_rate for a in self.agents.values()) / len(self.agents)
            self.metrics.total_evolution_factor = sum(a.evolution_factor for a in self.agents.values())
        
        # Update system state
        await self._update_system_state()
    
    async def _update_system_state(self):
        """Update system state in database"""
        with get_db() as db:
            state = db.query(SystemState).filter(SystemState.component == "agents").first()
            if state:
                state.state = {
                    "active_count": self.metrics.active_agents,
                    "total_count": self.metrics.total_agents,
                    "max_agents": settings.max_agents,
                    "tasks_in_queue": self.metrics.tasks_in_queue,
                    "tasks_completed": self.metrics.tasks_completed,
                    "average_success_rate": self.metrics.average_success_rate
                }
                state.optimization_level = self.metrics.total_evolution_factor
                state.last_updated = datetime.utcnow()
    
    async def _broadcast_pool_update(self, update_type: str, data: Dict[str, Any]):
        """Broadcast pool updates to WebSocket connections"""
        if self.websocket_connections:
            message = {
                "type": "pool_update",
                "update_type": update_type,
                "data": data,
                "timestamp": datetime.utcnow().isoformat(),
                "pool_metrics": {
                    "total_agents": self.metrics.total_agents,
                    "active_agents": self.metrics.active_agents,
                    "tasks_in_queue": self.metrics.tasks_in_queue,
                    "tasks_completed": self.metrics.tasks_completed
                }
            }
            
            for websocket in self.websocket_connections.copy():
                try:
                    await websocket.send(json.dumps(message))
                except:
                    self.websocket_connections.discard(websocket)
    
    def add_websocket_connection(self, websocket):
        """Add WebSocket connection for pool updates"""
        self.websocket_connections.add(websocket)
    
    def remove_websocket_connection(self, websocket):
        """Remove WebSocket connection"""
        self.websocket_connections.discard(websocket)
    
    def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get status of specific agent"""
        if agent_id in self.agents:
            return self.agents[agent_id].get_status()
        return None
    
    def get_pool_status(self) -> Dict[str, Any]:
        """Get overall pool status"""
        return {
            "metrics": {
                "total_agents": self.metrics.total_agents,
                "active_agents": self.metrics.active_agents,
                "tasks_in_queue": self.metrics.tasks_in_queue,
                "tasks_completed": self.metrics.tasks_completed,
                "average_success_rate": self.metrics.average_success_rate,
                "total_evolution_factor": self.metrics.total_evolution_factor
            },
            "agents": {agent_id: agent.get_status() for agent_id, agent in self.agents.items()},
            "workloads": self.agent_workloads.copy(),
            "optimization_cycles": self.optimization_cycles,
            "websocket_connections": len(self.websocket_connections),
            "is_running": self.is_running
        }
    
    async def shutdown(self):
        """Gracefully shutdown the agent pool"""
        print("🛑 Shutting down AgentPool...")
        self.is_running = False
        
        # Cancel worker tasks
        for task in self.worker_tasks:
            task.cancel()
        
        # Shutdown all agents
        for agent in list(self.agents.values()):
            await agent.shutdown()
        
        # Close WebSocket connections
        for websocket in self.websocket_connections.copy():
            try:
                await websocket.close()
            except:
                pass
        
        self.websocket_connections.clear()
        
        # Log shutdown
        with get_db() as db:
            log_entry = SystemLog(
                level="INFO",
                message="AgentPool shutdown completed",
                module="AgentPool",
                metadata={"final_metrics": self.get_pool_status()}
            )
            db.add(log_entry)
        
        print("✅ AgentPool shutdown complete")
