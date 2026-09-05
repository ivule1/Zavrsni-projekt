import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@localhost:5432/evoting",
)

# echo=False u produkciji; postavi na True privremeno ako trebas vidjeti SQL koji se izvrsava
engine = create_engine(DATABASE_URL, echo=False, future=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)

Base = declarative_base()


def get_db():
    """FastAPI dependency - jedna sesija po requestu, uvijek zatvorena na kraju."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
