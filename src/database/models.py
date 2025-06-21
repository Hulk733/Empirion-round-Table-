from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()

class Agent(Base):
    __tablename__ = "agents"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False, unique=True)
    agent_type = Column(String(50), default="HyperAgent")
    status = Column(String(20), default="active")
    evolution_factor = Column(Float, default=1.0)
    capabilities = Column(JSON, default=list)
    agent_metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tasks = relationship("Task", back_populates="agent")
    logs = relationship("SystemLog", back_populates="agent")

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = Column(String, ForeignKey("agents.id"), nullable=False)
    task_type = Column(String(50), nullable=False)
    status = Column(String(20), default="pending")
    priority = Column(Integer, default=1)
    data = Column(JSON, default=dict)
    result = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    agent = relationship("Agent", back_populates="tasks")

class SystemLog(Base):
    __tablename__ = "system_logs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = Column(String, ForeignKey("agents.id"), nullable=True)
    level = Column(String(10), nullable=False)
    message = Column(Text, nullable=False)
    module = Column(String(50), nullable=False)
    log_metadata = Column(JSON, default=dict)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    agent = relationship("Agent", back_populates="logs")

class SystemState(Base):
    __tablename__ = "system_state"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    component = Column(String(50), nullable=False)
    state = Column(JSON, nullable=False)
    optimization_level = Column(Float, default=1.0)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class WebSocketConnection(Base):
    __tablename__ = "websocket_connections"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    connection_id = Column(String(100), nullable=False, unique=True)
    client_info = Column(JSON, default=dict)
    connected_at = Column(DateTime, default=datetime.utcnow)
    last_ping = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

class DataSet(Base):
    __tablename__ = "datasets"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    description = Column(Text)
    data_type = Column(String(50), nullable=False)
    data = Column(JSON, nullable=False)
    dataset_metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class OptimizationMetric(Base):
    __tablename__ = "optimization_metrics"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    metric_name = Column(String(100), nullable=False)
    value = Column(Float, nullable=False)
    target_value = Column(Float, nullable=True)
    component = Column(String(50), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    metric_metadata = Column(JSON, default=dict)
