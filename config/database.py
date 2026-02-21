import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError, OperationalError

# Load environment variables from .env file
load_dotenv()

# Retrieve credentials from environment variables
DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_PORT = os.getenv("DB_PORT", "3306")

if not all([DB_USERNAME, DB_PASSWORD, DB_HOST, DB_NAME]):
    raise RuntimeError("Missing DB credentials in .env")

# Target MySQL database URL
SQLALCHEMY_DATABASE_URL = (
    f"mysql+pymysql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# Create engine (NO schema changes here)
try:
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=3600,
        future=True,
    )
except OperationalError as e:
    raise RuntimeError(f"Error connecting to database '{DB_NAME}': {e}")
except SQLAlchemyError as e:
    raise RuntimeError(f"SQLAlchemy engine error: {e}")

# Create session maker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()