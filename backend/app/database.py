"""Database configuration and session management for Joulaa platform"""

from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import (
    AsyncSession, AsyncEngine, create_async_engine, async_sessionmaker
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.pool import NullPool
from sqlalchemy import (
    String, DateTime, Boolean, Text, Integer, Float, JSON,
    func, event, Index, text
)
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
import structlog

from .core.config import settings

logger = structlog.get_logger()


class Base(DeclarativeBase):
    """Base class for all database models"""
    
    # Common columns for all tables
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    # Soft delete support
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True
    )
    
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Metadata for tracking changes
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True
    )
    
    updated_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True
    )
    
    # Version for optimistic locking
    version: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False
    )
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id={self.id})>"
    
    def soft_delete(self, deleted_by: Optional[uuid.UUID] = None):
        """Soft delete the record"""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
        if deleted_by:
            self.updated_by = deleted_by
    
    def restore(self, restored_by: Optional[uuid.UUID] = None):
        """Restore a soft-deleted record"""
        self.is_deleted = False
        self.deleted_at = None
        if restored_by:
            self.updated_by = restored_by


class DatabaseManager:
    """Manages database connections and sessions"""
    
    def __init__(self):
        self.engine: Optional[AsyncEngine] = None
        self.session_factory: Optional[async_sessionmaker] = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize database connection"""
        if self._initialized:
            return
        
        try:
            database_url = settings.DATABASE_URL
            if database_url.startswith("postgresql://"):
                database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

            engine_kwargs = {
                "echo": settings.DEBUG,
                "pool_pre_ping": True,
                "pool_recycle": 3600,
            }
            if settings.DEBUG:
                engine_kwargs["poolclass"] = NullPool
            else:
                engine_kwargs["pool_size"] = 20
                engine_kwargs["max_overflow"] = 30

            # Create async engine
            self.engine = create_async_engine(
                database_url,
                **engine_kwargs,
            )
            
            # Create session factory
            self.session_factory = async_sessionmaker(
                bind=self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=True,
                autocommit=False
            )
            
            # Test connection
            async with self.engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            
            self._initialized = True
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize database", error=str(e), exc_info=True)
            raise
    
    async def close(self):
        """Close database connections"""
        if self.engine:
            await self.engine.dispose()
            logger.info("Database connections closed")
    
    async def create_tables(self):
        """Create all tables"""
        if not self.engine:
            await self.initialize()
        
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error("Failed to create tables", error=str(e), exc_info=True)
            raise
    
    async def drop_tables(self):
        """Drop all tables (use with caution!)"""
        if not self.engine:
            await self.initialize()
        
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
            logger.info("Database tables dropped")
        except Exception as e:
            logger.error("Failed to drop tables", error=str(e), exc_info=True)
            raise
    
    async def get_session(self) -> AsyncSession:
        """Get a database session"""
        if not self._initialized:
            await self.initialize()
        
        if not self.session_factory:
            raise RuntimeError("Database not initialized")
        
        return self.session_factory()


# Global database manager instance
db_manager = DatabaseManager()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session"""
    session = await db_manager.get_session()
    try:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
    finally:
        await session.close()


async def get_db_session() -> AsyncSession:
    """Get a database session (for use outside of FastAPI dependencies)"""
    return await db_manager.get_session()


class DatabaseHealthCheck:
    """Database health check utilities"""
    
    @staticmethod
    async def check_connection() -> bool:
        """Check if database connection is healthy"""
        try:
            session = await db_manager.get_session()
            async with session:
                await session.execute(text("SELECT 1"))
                return True
        except Exception as e:
            logger.error("Database health check failed", error=str(e))
            return False
    
    @staticmethod
    async def get_connection_info() -> dict:
        """Get database connection information"""
        try:
            session = await db_manager.get_session()
            async with session:
                result = await session.execute(
                    text(
                        """
                        SELECT
                            version(),
                            current_database(),
                            current_user,
                            inet_server_addr(),
                            inet_server_port()
                        """
                    )
                )
                row = result.first()
                
                return {
                    "version": row[0] if row else None,
                    "database": row[1] if row else None,
                    "user": row[2] if row else None,
                    "host": row[3] if row else None,
                    "port": row[4] if row else None,
                    "status": "healthy"
                }
        except Exception as e:
            logger.error("Failed to get connection info", error=str(e))
            return {"status": "unhealthy", "error": str(e)}


class TransactionManager:
    """Context manager for database transactions"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.transaction = None
    
    async def __aenter__(self):
        self.transaction = await self.session.begin()
        return self.session
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            await self.transaction.rollback()
        else:
            await self.transaction.commit()


def transaction(session: AsyncSession):
    """Create a transaction context manager"""
    return TransactionManager(session)


# Database event listeners for automatic timestamp updates
@event.listens_for(Base, 'before_update', propagate=True)
def receive_before_update(mapper, connection, target):
    """Update the updated_at timestamp before update"""
    target.updated_at = datetime.utcnow()
    target.version += 1


# Database utilities
class QueryBuilder:
    """Utility class for building common queries"""
    
    @staticmethod
    def apply_filters(query, model, filters: dict):
        """Apply filters to a query"""
        for field, value in filters.items():
            if hasattr(model, field) and value is not None:
                if isinstance(value, list):
                    query = query.where(getattr(model, field).in_(value))
                elif isinstance(value, dict):
                    # Handle range queries
                    if 'gte' in value:
                        query = query.where(getattr(model, field) >= value['gte'])
                    if 'lte' in value:
                        query = query.where(getattr(model, field) <= value['lte'])
                    if 'gt' in value:
                        query = query.where(getattr(model, field) > value['gt'])
                    if 'lt' in value:
                        query = query.where(getattr(model, field) < value['lt'])
                else:
                    query = query.where(getattr(model, field) == value)
        return query
    
    @staticmethod
    def apply_search(query, model, search_term: str, search_fields: list):
        """Apply text search to specified fields"""
        if not search_term or not search_fields:
            return query
        
        search_conditions = []
        for field in search_fields:
            if hasattr(model, field):
                search_conditions.append(
                    getattr(model, field).ilike(f"%{search_term}%")
                )
        
        if search_conditions:
            from sqlalchemy import or_
            query = query.where(or_(*search_conditions))
        
        return query
    
    @staticmethod
    def apply_sorting(query, model, sort_by: str, sort_order: str = 'asc'):
        """Apply sorting to query"""
        if hasattr(model, sort_by):
            field = getattr(model, sort_by)
            if sort_order.lower() == 'desc':
                query = query.order_by(field.desc())
            else:
                query = query.order_by(field.asc())
        return query
    
    @staticmethod
    def apply_pagination(query, page: int, page_size: int):
        """Apply pagination to query"""
        offset = (page - 1) * page_size
        return query.offset(offset).limit(page_size)


# Database initialization functions
async def init_db():
    """Initialize database on startup"""
    await db_manager.initialize()
    
    # Create tables if they don't exist
    if settings.DEBUG:
        await db_manager.create_tables()


async def close_db():
    """Close database connections on shutdown"""
    await db_manager.close()


# Database migration utilities (basic)
class MigrationManager:
    """Basic migration management"""
    
    @staticmethod
    async def run_migrations():
        """Run database migrations"""
        # In a production environment, you would use Alembic
        # This is a placeholder for basic migration functionality
        logger.info("Running database migrations...")
        
        try:
            await db_manager.create_tables()
            logger.info("Migrations completed successfully")
        except Exception as e:
            logger.error("Migration failed", error=str(e), exc_info=True)
            raise
    
    @staticmethod
    async def create_indexes():
        """Create additional indexes for performance"""
        if not db_manager.engine:
            await db_manager.initialize()
        
        try:
            async with db_manager.engine.begin() as conn:
                # Create custom indexes here
                # Example: CREATE INDEX CONCURRENTLY IF NOT EXISTS ...
                pass
            
            logger.info("Custom indexes created successfully")
        except Exception as e:
            logger.error("Failed to create indexes", error=str(e), exc_info=True)
            raise


# Export commonly used items
__all__ = [
    'Base',
    'get_db',
    'get_db_session',
    'db_manager',
    'init_db',
    'close_db',
    'DatabaseHealthCheck',
    'TransactionManager',
    'transaction',
    'QueryBuilder',
    'MigrationManager'
]
