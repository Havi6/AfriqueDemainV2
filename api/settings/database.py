from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from api.settings.config import DATABASE_URL


def make_engine_with_fallback(url: str):
    """Create a SQLAlchemy engine and attempt a test connection.
    If a UnicodeDecodeError occurs during connection (psycopg2 decoding issue),
    retry creating the engine forcing the client encoding to LATIN1.
    """
    # Try default engine first
    engine = create_engine(url)
    try:
        conn = engine.connect()
        conn.close()
        return engine
    except Exception as exc:
        # psycopg2 may wrap a UnicodeDecodeError inside other exceptions; inspect the exception chain
        e = exc
        found_unicode_error = False
        while e is not None:
            if isinstance(e, UnicodeDecodeError):
                found_unicode_error = True
                break
            e = getattr(e, "__cause__", None) or getattr(e, "__context__", None)

        if not found_unicode_error:
            # not a UnicodeDecodeError; re-raise the original exception
            raise

        try:
            try:
                engine.dispose()
            except Exception:
                pass
            # Retry with client_encoding set to LATIN1 (works around server non-UTF8 responses)
            engine = create_engine(url, connect_args={"options": "-c client_encoding=LATIN1"})
            conn = engine.connect()
            conn.close()
            return engine
        except Exception:
            # If retry fails, re-raise the original Unicode-related exception for visibility
            raise

# create engine with fallback to handle UnicodeDecodeError from psycopg2
engine = make_engine_with_fallback(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)
Base = declarative_base()

# initilisation de la db
def init_db():
    Base.metadata.create_all(bind=engine)
    
# createur de session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from settings.config import DATABASE_URL
from  sqlalchemy.ext.asyncio import AsyncSession, create_async_engine



engine = create_engine(DATABASE_URL, connect_args={"options": "-c client_encoding=LATIN1"})
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)
Base = declarative_base()

#initilisation dez la db
def init_db():
    Base.metadata.create_all(bind=engine)
    
#createur de session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        """

