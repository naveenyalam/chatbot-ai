from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

DATABASE_URL = settings.DATABASE_URL

# Configure connection pooling and timeout properties for production
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
    engine = create_engine(DATABASE_URL, connect_args=connect_args)
else:
    connect_args = {}
    engine = create_engine(
        DATABASE_URL,
        connect_args=connect_args,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_timeout=settings.DB_POOL_TIMEOUT,
        pool_recycle=settings.DB_POOL_RECYCLE,
        pool_pre_ping=True
    )
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """
    FastAPI Dependency yielding scoped database sessions.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


_migrations_applied = False

def ensure_db_migrations():
    """Safely apply schema additions (like workspace_mode column) to existing SQLite/DB tables."""
    global _migrations_applied
    if _migrations_applied:
        return
    _migrations_applied = True

    from sqlalchemy import inspect, text
    try:
        inspector = inspect(engine)
        if "conversations" in inspector.get_table_names():
            columns = [c["name"] for c in inspector.get_columns("conversations")]
            if "workspace_mode" not in columns:
                with engine.connect() as conn:
                    conn.execute(text("ALTER TABLE conversations ADD COLUMN workspace_mode VARCHAR(50) DEFAULT 'general'"))
                    conn.commit()
    except Exception:
        pass

# Automatically run schema check on module load
ensure_db_migrations()

