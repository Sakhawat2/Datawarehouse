import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://dw:dwpass@localhost:5432/dwdb")
# sqlalchemy.url = postgresql+psycopg2://dw:dwpass@localhost:5433/dwdb





# Create engine
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# Create session factoryS
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


# Dependency for FastAPI routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
