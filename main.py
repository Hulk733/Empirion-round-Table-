from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import asyncio
import json
from datetime import datetime

from config.settings import settings
from src.database import DatabaseManager, get_db
from src.database.models import Agent, Task, SystemLog, SystemState, DataSet
from src.agents.pool import AgentPool
from src.websockets.server import websocket_manager
from src.ui.pages import page_registry
from src.core.system import empirion_core

# Pydantic models for API requests
class AgentCreateRequest(BaseModel):
    name: str
    agent_type: str = "HyperAgent"

class TaskSubmitRequest(BaseModel):
    type: str
    data: Dict[str, Any] = {}
    priority: int = 1
    complexity: float = 1.0

class CommandRequest(BaseModel):
    command: str
    parameters: Dict[str, Any] = {}

class DataStoreRequest(BaseModel):
    category: str
    key: str
    data: Any
    metadata: Dict[str, Any] = {}

class FeatureToggleRequest(BaseModel):
    feature_name: str
    enabled: bool

# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="Empirion Genesis System - Advanced AI Agent Management Platform"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Global instances
agent_pool: Optional[AgentPool] = None

@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup"""
    global agent_pool
    
    print("🚀 Starting Empirion Genesis System...")
    
    # Initialize database
    DatabaseManager.initialize()
    print("✅ Database initialized")
    
    # Initialize WebSocket server
    await websocket_manager.start_server()
    print("✅ WebSocket server started")
    
    # Initialize agent pool
    agent_pool = AgentPool()
    await agent_pool.initialize()
    print("✅ Agent pool initialized")
    
    # Load UI pages
    for page_name, page in page_registry.items():
        await page.load()
    print("✅ UI pages loaded")
    
    # Initialize Empirion core system
    await empirion_core.initialize()
    print("✅ Empirion core system initialized")
    
    # Create initial agents
    try:
        initial_agents = ["Alpha", "Beta", "Gamma"]
        for agent_name in initial_agents:
            await agent_pool.create_agent(agent_name)
        print(f"✅ Created {len(initial_agents)} initial agents")
    except Exception as e:
        print(f"⚠️ Warning: Could not create initial agents: {e}")
    
    print("🎉 Empirion Genesis System fully initialized!")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown"""
    global agent_pool
    
    print("🛑 Shutting down Empirion Genesis System...")
    
    # Shutdown Empirion core system
    await empirion_core.shutdown()
    
    # Shutdown agent pool
    if agent_pool:
        await agent_pool.shutdown()
    
    # Shutdown WebSocket server
    await websocket_manager.shutdown()
    
    # Unload UI pages
    for page in page_registry.values():
        await page.unload()
    
    print("✅ Empirion Genesis System shutdown complete")

# Root endpoint
@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main dashboard"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Empirion Genesis System</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <script src="https://cdn.tailwindcss.com"></script>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    </head>
    <body class="bg-gray-900 text-white">
        <div id="app" class="min-h-screen">
            <header class="bg-gray-800 shadow-lg">
                <div class="container mx-auto px-4 py-6">
                    <h1 class="text-3xl font-bold text-blue-400">
                        <i class="fas fa-atom mr-2"></i>
                        Empirion Genesis System
                    </h1>
                    <p class="text-gray-300 mt-2">Advanced AI Agent Management Platform</p>
                </div>
            </header>
            
            <main class="container mx-auto px-4 py-8">
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    <!-- System Status Card -->
                    <div class="bg-gray-800 rounded-lg p-6 shadow-lg">
                        <h2 class="text-xl font-semibold mb-4 text-green-400">
                            <i class="fas fa-heartbeat mr-2"></i>
                            System Status
                        </h2>
                        <div id="system-status" class="space-y-2">
                            <div class="flex justify-between">
                                <span>Status:</span>
                                <span class="text-green-400">Online</span>
                            </div>
                            <div class="flex justify-between">
                                <span>Agents:</span>
                                <span id="agent-count">Loading...</span>
                            </div>
                            <div class="flex justify-between">
                                <span>WebSocket:</span>
                                <span id="ws-status" class="text-yellow-400">Connecting...</span>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Quick Actions Card -->
                    <div class="bg-gray-800 rounded-lg p-6 shadow-lg">
                        <h2 class="text-xl font-semibold mb-4 text-blue-400">
                            <i class="fas fa-bolt mr-2"></i>
                            Quick Actions
                        </h2>
                        <div class="space-y-3">
                            <button onclick="createAgent()" class="w-full bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded transition-colors">
                                <i class="fas fa-plus mr-2"></i>Create Agent
                            </button>
                            <button onclick="submitTask()" class="w-full bg-green-600 hover:bg-green-700 px-4 py-2 rounded transition-colors">
                                <i class="fas fa-tasks mr-2"></i>Submit Task
                            </button>
                            <button onclick="viewLogs()" class="w-full bg-purple-600 hover:bg-purple-700 px-4 py-2 rounded transition-colors">
                                <i class="fas fa-list mr-2"></i>View Logs
                            </button>
                        </div>
                    </div>
                    
                    <!-- Real-time Updates Card -->
                    <div class="bg-gray-800 rounded-lg p-6 shadow-lg">
                        <h2 class="text-xl font-semibold mb-4 text-purple-400">
                            <i class="fas fa-broadcast-tower mr-2"></i>
                            Live Updates
                        </h2>
                        <div id="live-updates" class="space-y-2 text-sm max-h-32 overflow-y-auto">
                            <div class="text-gray-400">Connecting to live feed...</div>
                        </div>
                    </div>
                </div>
                
                <!-- Navigation Cards -->
                <div class="grid grid-cols-2 md:grid-cols-5 gap-4 mt-8">
                    <a href="/pages/command-room" class="bg-red-600 hover:bg-red-700 rounded-lg p-4 text-center transition-colors">
                        <i class="fas fa-satellite-dish text-2xl mb-2"></i>
                        <div class="font-semibold">Command Room</div>
                    </a>
                    <a href="/pages/department-view" class="bg-blue-600 hover:bg-blue-700 rounded-lg p-4 text-center transition-colors">
                        <i class="fas fa-building text-2xl mb-2"></i>
                        <div class="font-semibold">Departments</div>
                    </a>
                    <a href="/pages/feature-console" class="bg-green-600 hover:bg-green-700 rounded-lg p-4 text-center transition-colors">
                        <i class="fas fa-cogs text-2xl mb-2"></i>
                        <div class="font-semibold">Features</div>
                    </a>
                    <a href="/pages/deep-vault" class="bg-purple-600 hover:bg-purple-700 rounded-lg p-4 text-center transition-colors">
                        <i class="fas fa-vault text-2xl mb-2"></i>
                        <div class="font-semibold">Deep Vault</div>
                    </a>
                    <a href="/pages/external-hub" class="bg-yellow-600 hover:bg-yellow-700 rounded-lg p-4 text-center transition-colors">
                        <i class="fas fa-globe text-2xl mb-2"></i>
                        <div class="font-semibold">External Hub</div>
                    </a>
                </div>
            </main>
        </div>
        
        <script>
            let ws = null;
            
            function connectWebSocket() {
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const wsUrl = `${protocol}//${window.location.hostname}:8765`;
                
                ws = new WebSocket(wsUrl);
                
                ws.onopen = function() {
                    document.getElementById('ws-status').textContent = 'Connected';
                    document.getElementById('ws-status').className = 'text-green-400';
                    
                    // Subscribe to updates
                    ws.send(JSON.stringify({
                        type: 'subscribe',
                        topic: 'pool_updates'
                    }));
                };
                
                ws.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    handleWebSocketMessage(data);
                };
                
                ws.onclose = function() {
                    document.getElementById('ws-status').textContent = 'Disconnected';
                    document.getElementById('ws-status').className = 'text-red-400';
                    
                    // Reconnect after 5 seconds
                    setTimeout(connectWebSocket, 5000);
                };
                
                ws.onerror = function() {
                    document.getElementById('ws-status').textContent = 'Error';
                    document.getElementById('ws-status').className = 'text-red-400';
                };
            }
            
            function handleWebSocketMessage(data) {
                if (data.type === 'pool_update') {
                    if (data.pool_metrics) {
                        document.getElementById('agent-count').textContent = 
                            `${data.pool_metrics.active_agents}/${data.pool_metrics.total_agents}`;
                    }
                }
                
                // Add to live updates
                const updatesDiv = document.getElementById('live-updates');
                const updateElement = document.createElement('div');
                updateElement.className = 'text-xs text-gray-300';
                updateElement.textContent = `${new Date().toLocaleTimeString()}: ${data.type}`;
                updatesDiv.insertBefore(updateElement, updatesDiv.firstChild);
                
                // Keep only last 10 updates
                while (updatesDiv.children.length > 10) {
                    updatesDiv.removeChild(updatesDiv.lastChild);
                }
            }
            
            async function createAgent() {
                const name = prompt('Enter agent name:');
                if (!name) return;
                
                try {
                    const response = await fetch('/api/agents', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({name: name})
                    });
                    const result = await response.json();
                    alert(response.ok ? 'Agent created successfully!' : `Error: ${result.detail}`);
                } catch (error) {
                    alert(`Error: ${error.message}`);
                }
            }
            
            async function submitTask() {
                const type = prompt('Enter task type (data_analysis, optimization, etc.):') || 'general';
                
                try {
                    const response = await fetch('/api/tasks', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            type: type,
                            data: {sample: 'data'},
                            priority: 1
                        })
                    });
                    const result = await response.json();
                    alert(response.ok ? `Task submitted: ${result.task_id}` : `Error: ${result.detail}`);
                } catch (error) {
                    alert(`Error: ${error.message}`);
                }
            }
            
            function viewLogs() {
                window.open('/api/logs', '_blank');
            }
            
            // Initialize
            connectWebSocket();
            
            // Load initial status
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    if (data.agents) {
                        document.getElementById('agent-count').textContent = 
                            `${data.agents.active}/${data.agents.total}`;
                    }
                })
                .catch(error => console.error('Error loading status:', error));
        </script>
    </body>
    </html>
    """

# API Routes

@app.get("/api/status")
async def get_system_status():
    """Get overall system status"""
    if not agent_pool:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    pool_status = agent_pool.get_pool_status()
    ws_stats = websocket_manager.get_connection_stats()
    
    with get_db() as db:
        total_tasks = db.query(Task).count()
        completed_tasks = db.query(Task).filter(Task.status == "completed").count()
        
    return {
        "status": "online",
        "timestamp": datetime.utcnow().isoformat(),
        "agents": {
            "total": pool_status["metrics"]["total_agents"],
            "active": pool_status["metrics"]["active_agents"],
            "tasks_completed": pool_status["metrics"]["tasks_completed"],
            "average_success_rate": pool_status["metrics"]["average_success_rate"]
        },
        "websockets": ws_stats,
        "database": {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks
        },
        "pages": {name: page.get_status() for name, page in page_registry.items()}
    }

@app.post("/api/agents")
async def create_agent(request: AgentCreateRequest):
    """Create a new agent"""
    if not agent_pool:
        raise HTTPException(status_code=503, detail="Agent pool not initialized")
    
    try:
        agent_id = await agent_pool.create_agent(request.name, request.agent_type)
        return {"success": True, "agent_id": agent_id, "message": f"Agent '{request.name}' created"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/agents")
async def list_agents():
    """List all agents"""
    if not agent_pool:
        raise HTTPException(status_code=503, detail="Agent pool not initialized")
    
    pool_status = agent_pool.get_pool_status()
    return {
        "agents": pool_status["agents"],
        "metrics": pool_status["metrics"]
    }

@app.get("/api/agents/{agent_id}")
async def get_agent(agent_id: str):
    """Get specific agent details"""
    if not agent_pool:
        raise HTTPException(status_code=503, detail="Agent pool not initialized")
    
    agent_status = agent_pool.get_agent_status(agent_id)
    if not agent_status:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return agent_status

@app.delete("/api/agents/{agent_id}")
async def remove_agent(agent_id: str):
    """Remove an agent"""
    if not agent_pool:
        raise HTTPException(status_code=503, detail="Agent pool not initialized")
    
    success = await agent_pool.remove_agent(agent_id)
    if not success:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return {"success": True, "message": "Agent removed"}

@app.post("/api/tasks")
async def submit_task(request: TaskSubmitRequest):
    """Submit a task to the agent pool"""
    if not agent_pool:
        raise HTTPException(status_code=503, detail="Agent pool not initialized")
    
    task_data = {
        "type": request.type,
        "data": request.data,
        "priority": request.priority,
        "complexity": request.complexity
    }
    
    task_id = await agent_pool.submit_task(task_data)
    return {"success": True, "task_id": task_id, "message": "Task submitted"}

@app.get("/api/tasks")
async def list_tasks(limit: int = 50, status: Optional[str] = None):
    """List tasks"""
    with get_db() as db:
        query = db.query(Task)
        if status:
            query = query.filter(Task.status == status)
        
        tasks = query.order_by(Task.created_at.desc()).limit(limit).all()
        
        return {
            "tasks": [
                {
                    "id": task.id,
                    "agent_id": task.agent_id,
                    "type": task.task_type,
                    "status": task.status,
                    "priority": task.priority,
                    "created_at": task.created_at.isoformat(),
                    "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                    "result": task.result
                }
                for task in tasks
            ]
        }

@app.get("/api/logs")
async def get_logs(limit: int = 100, level: Optional[str] = None):
    """Get system logs"""
    with get_db() as db:
        query = db.query(SystemLog)
        if level:
            query = query.filter(SystemLog.level == level.upper())
        
        logs = query.order_by(SystemLog.timestamp.desc()).limit(limit).all()
        
        return {
            "logs": [
                {
                    "id": log.id,
                    "agent_id": log.agent_id,
                    "level": log.level,
                    "message": log.message,
                    "module": log.module,
                    "timestamp": log.timestamp.isoformat(),
                    "metadata": log.log_metadata
                }
                for log in logs
            ]
        }

@app.post("/api/commands")
async def execute_command(request: CommandRequest):
    """Execute a system command"""
    command_room = page_registry["command_room"]
    
    try:
        result = await command_room.execute_command(request.command, request.parameters)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/vault/store")
async def store_data(request: DataStoreRequest):
    """Store data in the deep vault"""
    deep_vault = page_registry["deep_vault"]
    
    result = await deep_vault.store_data(
        request.category, 
        request.key, 
        request.data, 
        request.metadata
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result

@app.get("/api/vault/retrieve/{category}/{key}")
async def retrieve_data(category: str, key: str):
    """Retrieve data from the deep vault"""
    deep_vault = page_registry["deep_vault"]
    
    result = await deep_vault.retrieve_data(category, key)
    
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result

@app.post("/api/features/toggle")
async def toggle_feature(request: FeatureToggleRequest):
    """Enable or disable a feature"""
    feature_console = page_registry["feature_console"]
    
    if request.enabled:
        result = await feature_console.enable_feature(request.feature_name)
    else:
        result = await feature_console.disable_feature(request.feature_name)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Feature toggle failed"))
    
    return result

@app.get("/api/datasets")
async def list_datasets():
    """List available datasets"""
    with get_db() as db:
        datasets = db.query(DataSet).all()
        
        return {
            "datasets": [
                {
                    "id": ds.id,
                    "name": ds.name,
                    "description": ds.description,
                    "data_type": ds.data_type,
                    "metadata": ds.dataset_metadata,
                    "created_at": ds.created_at.isoformat(),
                    "updated_at": ds.updated_at.isoformat()
                }
                for ds in datasets
            ]
        }

@app.get("/api/metrics")
async def get_metrics():
    """Get system performance metrics"""
    if not agent_pool:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    pool_status = agent_pool.get_pool_status()
    ws_stats = websocket_manager.get_connection_stats()
    core_status = empirion_core.get_system_status()
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "agent_pool": pool_status["metrics"],
        "websockets": ws_stats,
        "core_system": core_status,
        "pages": {name: page.get_status() for name, page in page_registry.items()}
    }

@app.get("/api/core/status")
async def get_core_status():
    """Get Empirion core system status"""
    return empirion_core.get_system_status()

@app.post("/api/core/override")
async def activate_override(level: int, reason: str):
    """Activate override system"""
    result = await empirion_core.override_system.activate_override(level, reason)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@app.delete("/api/core/override")
async def deactivate_override():
    """Deactivate override system"""
    result = await empirion_core.override_system.deactivate_override()
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@app.post("/api/core/glyph")
async def create_glyph(symbol: str, meaning: Dict[str, Any], metadata: Dict[str, Any] = None):
    """Create a symbolic glyph"""
    glyph_id = await empirion_core.glyph_engine.create_glyph(symbol, meaning, metadata)
    return {"success": True, "glyph_id": glyph_id}

@app.get("/api/core/glyphs")
async def get_glyph_stats():
    """Get glyph engine statistics"""
    return empirion_core.glyph_engine.get_glyph_statistics()

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time communication"""
    await websocket.accept()
    
    # Add to WebSocket manager
    connection_id = f"api_{datetime.utcnow().timestamp()}"
    websocket_manager.connections[connection_id] = websocket
    
    # Add to agent pool for updates
    if agent_pool:
        agent_pool.add_websocket_connection(websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle WebSocket messages
            if message.get("type") == "ping":
                await websocket.send_text(json.dumps({
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                }))
            
    except WebSocketDisconnect:
        # Clean up connections
        websocket_manager.connections.pop(connection_id, None)
        if agent_pool:
            agent_pool.remove_websocket_connection(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
