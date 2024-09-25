from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import pymysql
from sqlalchemy import text
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Retrieve credentials from environment variables
DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_PORT = os.getenv("DB_PORT", "3306")  # Default to 3306 if not set

# Define MySQL connection without specifying the database
DATABASE_URL_WITHOUT_DB = f"mysql+pymysql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}"

# Target MySQL database URL
SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Create a connection to MySQL without the database to check and create it
def create_database_if_not_exists():
    # Create engine to connect without the specific database
    engine = create_engine(DATABASE_URL_WITHOUT_DB)
    with engine.connect() as conn:
        # Check if the database exists
        result = conn.execute(text(f"SHOW DATABASES LIKE '{DB_NAME}'"))
        database_exists = result.scalar()

        if not database_exists:
            # If database doesn't exist, create it with utf8mb4 and unicode collation
            conn.execute(text(f"CREATE DATABASE {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
            print(f"Database '{DB_NAME}' created with utf8mb4_unicode_ci collation.")
        else:
            print(f"Database '{DB_NAME}' already exists.")

# Call the function to ensure the database exists
create_database_if_not_exists()

# Now create the main engine for the actual database connection
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Create a session maker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for declarative models
Base = declarative_base()

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
