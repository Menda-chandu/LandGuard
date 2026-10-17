from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

# Create SQLAlchemy Database Engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    echo=False
)

# Session Local Factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative Base Model
Base = declarative_base()


def get_db():
    """
    FastAPI dependency to yield a database session per request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connection() -> dict:
    """
    Helper function to verify database connectivity for health checks.
    """
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            try:
                if engine.dialect.name == "postgresql":
                    res = connection.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'"))
                else:
                    res = connection.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
                tables = [r[0] for r in res.fetchall()]
            except Exception:
                tables = []
        return {"status": "connected", "database": engine.url.database, "engine": engine.dialect.name, "tables": tables}
    except Exception as e:
        return {"status": "disconnected", "error": str(e)}
