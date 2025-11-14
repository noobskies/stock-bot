"""
Base Repository for Database Operations.

Provides common session management and utility methods for all repositories.
"""

from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from typing import Any, Dict, List, Optional
from loguru import logger


class BaseRepository:
    """
    Base repository class with common database operations.
    
    All specific repositories inherit from this to get session management
    and common utility methods.
    """
    
    def __init__(self, session_maker: sessionmaker):
        """
        Initialize base repository.
        
        Args:
            session_maker: SQLAlchemy session maker from engine
        """
        self.SessionLocal = session_maker
    
    @contextmanager
    def get_session(self):
        """
        Context manager for database sessions.
        
        Automatically handles commit/rollback and session cleanup.
        
        Usage:
            with self.get_session() as session:
                # perform operations
                session.add(entity)
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            session.close()
