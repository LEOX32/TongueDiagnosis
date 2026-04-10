from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from ..config import settings
import os

# Use absolute path for database file
db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), f'{settings.APP_PORT}_database.db')
engine = create_engine(f'sqlite:///{db_path}')
print(f"Database path: {db_path}")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def get_db_object():
    return SessionLocal()
