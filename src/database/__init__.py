from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
import os
from typing import Generator

from config.settings import settings
from .models import Base

# Create engine with appropriate configuration
if settings.database_url.startswith("sqlite"):
    engine = create_engine(
        settings.database_url,
        echo=settings.database_echo,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(
        settings.database_url,
        echo=settings.database_echo
    )

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables():
    """Create all database tables"""
    # Ensure data directory exists
    os.makedirs("./data", exist_ok=True)
    Base.metadata.create_all(bind=engine)

def drop_tables():
    """Drop all database tables"""
    Base.metadata.drop_all(bind=engine)

@contextmanager
def get_db() -> Generator[Session, None, None]:
    """Get database session with automatic cleanup"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def get_db_session() -> Session:
    """Get database session for dependency injection"""
    return SessionLocal()

class DatabaseManager:
    """Database management utilities"""
    
    @staticmethod
    def initialize():
        """Initialize database with tables and initial data"""
        create_tables()
        DatabaseManager._create_initial_data()
    
    @staticmethod
    def _create_initial_data():
        """Create initial system data"""
        from .models import SystemState, DataSet
        
        with get_db() as db:
            # Check if initial data already exists
            if db.query(SystemState).first():
                return
            
            # Create initial system state
            initial_states = [
                SystemState(
                    component="core",
                    state={"status": "initialized", "version": "1.0.0"},
                    optimization_level=1.0
                ),
                SystemState(
                    component="agents",
                    state={"active_count": 0, "max_agents": settings.max_agents},
                    optimization_level=1.0
                ),
                SystemState(
                    component="websockets",
                    state={"active_connections": 0, "max_connections": settings.max_connections},
                    optimization_level=1.0
                )
            ]
            
            for state in initial_states:
                db.add(state)
            
            # Create sample datasets
            sample_datasets = [
                DataSet(
                    name="quantum_training_data",
                    description="Training data for quantum processing algorithms",
                    data_type="numerical",
                    data={"samples": [], "labels": []},
                    metadata={"size": 0, "features": 0}
                ),
                DataSet(
                    name="agent_behavior_patterns",
                    description="Behavioral patterns for agent evolution",
                    data_type="behavioral",
                    data={"patterns": [], "outcomes": []},
                    metadata={"pattern_count": 0, "success_rate": 0.0}
                )
            ]
            
            for dataset in sample_datasets:
                db.add(dataset)
    
    @staticmethod
    def reset():
        """Reset database to initial state"""
        drop_tables()
        DatabaseManager.initialize()
    
    @staticmethod
    def backup(backup_path: str):
        """Create database backup"""
        # Implementation for database backup
        pass
    
    @staticmethod
    def restore(backup_path: str):
        """Restore database from backup"""
        # Implementation for database restore
        pass
