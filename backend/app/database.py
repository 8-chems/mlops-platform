from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import OperationalError
import logging

from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

# Lazy engine creation to prevent blocking at import time
_engine = None
_SessionLocal = None

def get_engine():
    global _engine
    if _engine is None:
        try:
            _engine = create_engine(
                settings.database_url,
                pool_pre_ping=True,
                connect_args={"connect_timeout": 10}
            )
            logger.info("Database engine created successfully")
        except Exception as e:
            logger.error(f"Failed to create database engine: {e}")
            raise
    return _engine

def get_session_local():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    return _SessionLocal

Base = declarative_base()

# Don't create engine at import time - only when first needed
engine = None
SessionLocal = None

def get_db():
    global SessionLocal
    if SessionLocal is None:
        SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        yield db
    except OperationalError as e:
        logger.error(f"Database operational error: {e}")
        db.close()
        raise
    finally:
        db.close()
