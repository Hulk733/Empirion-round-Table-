# Empirion Genesis System

An advanced AI agent management platform with real-time monitoring, symbolic communication, and distributed processing capabilities.

## 🌟 Features

### Core System Components
- **Agent Pool Management**: Dynamic creation, monitoring, and optimization of AI agents
- **Real-time WebSocket Communication**: Live updates and bidirectional communication
- **Symbolic Glyph Engine**: Advanced symbolic messaging system for agent communication
- **Override System**: Emergency control and privileged operations
- **Thread Weaver**: Comprehensive system monitoring and event logging
- **Mobile Shell**: Offline operation support and mobile optimization

### UI Components
- **Command Room**: Central command interface for system control
- **Department View**: Overview of system modules and their status
- **Feature Console**: Advanced features and real-time analytics
- **Deep Vault**: Secure storage for sensitive and legacy data
- **External Hub**: Interface for external APIs and services

### Technical Features
- **FastAPI Backend**: High-performance async API with automatic documentation
- **SQLAlchemy ORM**: Robust database management with migrations
- **WebSocket Server**: Real-time bidirectional communication
- **Responsive UI**: Modern Tailwind CSS interface with dark theme
- **Modular Architecture**: Clean separation of concerns and extensible design

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip package manager

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd empirion-genesis
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python main.py
   ```

4. **Access the system**
   - Web Interface: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - WebSocket: ws://localhost:8765

## 📁 Project Structure

```
empirion-genesis/
├── config/
│   ├── __init__.py
│   └── settings.py          # Configuration settings
├── src/
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── hyperagent.py    # Core agent implementation
│   │   └── pool.py          # Agent pool management
│   ├── core/
│   │   ├── __init__.py
│   │   └── system.py        # Core system orchestrator
│   ├── database/
│   │   ├── __init__.py
│   │   └── models.py        # Database models
│   ├── ui/
│   │   ├── __init__.py
│   │   └── pages.py         # UI page classes
│   └── websockets/
│       ├── __init__.py
│       └── server.py        # WebSocket server
├── static/
│   └── css/
│       └── empirion.css     # Custom styles
├── main.py                  # FastAPI application
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## 🔧 Configuration

The system can be configured through environment variables or by modifying `config/settings.py`:

```python
# Database
DATABASE_URL = "sqlite:///./empirion.db"

# Server
HOST = "0.0.0.0"
PORT = 8000
WEBSOCKET_PORT = 8765

# Agent Pool
MAX_AGENTS = 50
AGENT_TIMEOUT = 300

# WebSocket
WEBSOCKET_HEARTBEAT = 30
```

## 🤖 Agent Management

### Creating Agents
```python
# Via API
POST /api/agents
{
    "name": "Agent-Alpha",
    "agent_type": "HyperAgent"
}

# Via Python
agent_id = await agent_pool.create_agent("Agent-Alpha")
```

### Submitting Tasks
```python
# Via API
POST /api/tasks
{
    "type": "data_analysis",
    "data": {"dataset": "sample_data"},
    "priority": 1,
    "complexity": 1.5
}

# Via Python
task_id = await agent_pool.submit_task({
    "type": "optimization",
    "data": {"parameters": [1, 2, 3]},
    "priority": 2
})
```

## 🌐 WebSocket Communication

### Connection
```javascript
const ws = new WebSocket('ws://localhost:8765');

ws.onopen = function() {
    // Subscribe to updates
    ws.send(JSON.stringify({
        type: 'subscribe',
        topic: 'agent_updates'
    }));
};

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Received:', data);
};
```

### Available Topics
- `agent_updates`: Agent status changes
- `pool_updates`: Agent pool metrics
- `system_logs`: System log entries
- `performance_metrics`: Performance data
- `task_updates`: Task completion status
- `optimization_metrics`: System optimization data

## 🔒 Override System

The override system provides emergency control capabilities:

```python
# Activate override (levels 1-5)
POST /api/core/override?level=3&reason="Emergency maintenance"

# Execute privileged command
POST /api/core/override/execute
{
    "command": "system_recovery",
    "parameters": {}
}

# Deactivate override
DELETE /api/core/override
```

## 🎨 Symbolic Communication

The Glyph Engine enables symbolic communication between agents:

```python
# Create a glyph
POST /api/core/glyph
{
    "symbol": "⚡",
    "meaning": {
        "type": "energy",
        "intensity": "high",
        "action": "activate"
    },
    "metadata": {
        "category": "system"
    }
}

# Send symbolic message
await glyph_engine.send_symbolic_message(
    sender="Agent-Alpha",
    recipient="Agent-Beta",
    glyphs=["glyph-id-1", "glyph-id-2"],
    context={"urgency": "high"}
)
```

## 📊 Monitoring & Analytics

### System Status
```bash
GET /api/status
```

### Performance Metrics
```bash
GET /api/metrics
```

### System Logs
```bash
GET /api/logs?level=ERROR&limit=100
```

### Core System Status
```bash
GET /api/core/status
```

## 🔧 Development

### Adding New Agent Types
1. Create a new class inheriting from `HyperAgent`
2. Implement required methods (`process_task`, `optimize`, etc.)
3. Register the agent type in the pool

### Adding New UI Pages
1. Create a new class inheriting from `BasePage`
2. Implement page-specific logic
3. Add to `page_registry` in `pages.py`

### Adding New API Endpoints
1. Add endpoint to `main.py`
2. Use appropriate Pydantic models for request/response
3. Include proper error handling

## 🧪 Testing

### Manual Testing
1. Start the system: `python main.py`
2. Open browser to http://localhost:8000
3. Test agent creation and task submission
4. Monitor WebSocket connections
5. Verify database operations

### API Testing
Use the automatic API documentation at http://localhost:8000/docs to test endpoints interactively.

## 🚀 Deployment

### Production Deployment
1. Set environment variables for production
2. Use a production WSGI server (e.g., Gunicorn)
3. Configure reverse proxy (e.g., Nginx)
4. Set up SSL certificates
5. Configure monitoring and logging

### Docker Deployment
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000 8765

CMD ["python", "main.py"]
```

## 🔍 Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Check DATABASE_URL configuration
   - Ensure database file permissions
   - Verify SQLAlchemy version compatibility

2. **WebSocket Connection Failures**
   - Check WEBSOCKET_PORT configuration
   - Verify firewall settings
   - Ensure WebSocket server is running

3. **Agent Creation Failures**
   - Check MAX_AGENTS limit
   - Verify agent name uniqueness
   - Monitor system resources

4. **Performance Issues**
   - Monitor agent pool metrics
   - Check database query performance
   - Review WebSocket connection count

### Logging
System logs are available through:
- Database: `SystemLog` table
- API: `GET /api/logs`
- Console: Real-time output during development

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- FastAPI for the excellent async web framework
- SQLAlchemy for robust ORM capabilities
- Tailwind CSS for modern UI styling
- WebSockets for real-time communication

## 📞 Support

For support and questions:
- Create an issue in the repository
- Check the API documentation at `/docs`
- Review the system logs for error details

---

**Empirion Genesis System** - Advanced AI Agent Management Platform
