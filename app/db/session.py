"""
Database Session Management.

Provides thread-safe database session creation and dependency injection
for FastAPI routes.

Note: For schema migrations, use Alembic:
    alembic upgrade head    # Apply all migrations
    alembic revision --autogenerate -m "description"  # Create new migration
"""
import threading
from typing import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import settings
from app.db.models import Base


# Thread-safe singleton pattern for engine and sessionmaker
_engine = None
_SessionLocal = None
_lock = threading.Lock()


def get_engine():
    """Get or create the database engine (singleton)."""
    global _engine
    with _lock:
        if _engine is None:
            _engine = create_engine(
                settings.DATABASE_URL,
                pool_pre_ping=True,
                pool_size=10,
                max_overflow=20,
                echo=settings.DEBUG,
            )
    return _engine


def get_session_maker():
    """Get or create the session maker (singleton)."""
    global _SessionLocal
    with _lock:
        if _SessionLocal is None:
            engine = get_engine()
            _SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=engine
            )
    return _SessionLocal


def get_session_local() -> Session:
    """Create a new database session."""
    SessionLocal = get_session_maker()
    return SessionLocal()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency injection for FastAPI routes.
    
    Yields a database session and ensures proper cleanup.
    
    Usage:
        @router.get("/items")
        def get_items(db: Session = Depends(get_db)):
            ...
    """
    db = get_session_local()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    Context manager for database sessions.
    
    Usage:
        with get_db_context() as db:
            session = db.query(LearningSession).first()
    """
    db = get_session_local()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Initialize database tables.
    
    Note: In production, use Alembic migrations instead:
        alembic upgrade head
    
    This method uses create_all() which is fine for development
    but doesn't handle schema changes properly.
    """
    engine = get_engine()
    Base.metadata.create_all(bind=engine)


def run_migrations() -> None:
    """
    Run Alembic migrations programmatically.
    
    This applies all pending migrations to bring the database
    schema up to date.
    """
    from alembic.config import Config
    from alembic import command
    import os
    
    # Get the path to alembic.ini
    base_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    alembic_ini_path = os.path.join(base_path, "alembic.ini")
    
    if os.path.exists(alembic_ini_path):
        alembic_cfg = Config(alembic_ini_path)
        alembic_cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
        command.upgrade(alembic_cfg, "head")
    else:
        # Fallback to create_all if alembic.ini not found
        init_db()


def drop_db() -> None:
    """Drop all database tables. Use with caution!"""
    engine = get_engine()
    Base.metadata.drop_all(bind=engine)
