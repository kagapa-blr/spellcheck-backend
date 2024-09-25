import os
import subprocess
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from database import Base  # Adjust the import according to your project structure

# Load environment variables from .env file
load_dotenv()

ALEMBIC_DIR = 'alembic'  # Assuming the default Alembic folder is named 'alembic'

DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_PORT = os.getenv("DB_PORT", "3306")  # Default to 3306 if not set

# Define MySQL connection without specifying the database
DATABASE_URL_WITHOUT_DB = f"mysql+pymysql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}"
# Target MySQL database URL
SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def reset_database():
    """Reset the database by dropping and recreating it, then creating all tables."""
    try:
        # Connect to the MySQL server without specifying a database
        engine = create_engine(DATABASE_URL_WITHOUT_DB)

        # Drop the existing database if it exists
        with engine.connect() as connection:
            connection.execute(text(f"DROP DATABASE IF EXISTS {DB_NAME};"))  # Drop the database
            print(f"Database '{DB_NAME}' dropped successfully.")

        # Create the database again
        with engine.connect() as connection:
            connection.execute(text(f"CREATE DATABASE {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"))  # Create the database
            print(f"Database '{DB_NAME}' created successfully.")

        # Create the main engine for the actual database connection
        engine = create_engine(SQLALCHEMY_DATABASE_URL)

        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("All tables created successfully.")
        print("Created tables:", Base.metadata.tables.keys())  # Show created tables

    except SQLAlchemyError as e:
        print(f"SQLAlchemyError in reset_database: {e}")
    except Exception as e:
        print(f"Error in reset_database: {e}")

def drop_database():
    """Drop the existing database."""
    try:
        drop_engine = create_engine(SQLALCHEMY_DATABASE_URL)

        with drop_engine.connect() as connection:
            connection.execute(text(f"DROP DATABASE IF EXISTS {DB_NAME}"))  # Drop the database
            print(f"Database '{DB_NAME}' dropped successfully.")
    except Exception as e:
        print(f"Error dropping database: {e}")

def initialize_alembic():
    """Initialize Alembic if it is not already initialized."""
    if not os.path.exists(ALEMBIC_DIR):
        print("Alembic not initialized. Initializing Alembic...")
        subprocess.run(["alembic", "init", ALEMBIC_DIR])
        print("Alembic initialized successfully.")
    else:
        print("Alembic already initialized.")

def migrate_database():
    """Create a new Alembic revision and run the database migration."""
    initialize_alembic()
    # Create a new Alembic revision with a descriptive message
    revision_message = "create account table"
    result = subprocess.run(["alembic", "revision", "-m", revision_message], capture_output=True, text=True)

    # Check if the revision command was successful
    if result.returncode != 0:
        print(f"Error creating Alembic revision: {result.stderr}")
        return
    print("Alembic revision created successfully.")

    # Run the database migration (upgrade to the latest version)
    print("Starting database migration...")
    result = subprocess.run(["alembic", "upgrade", "head"], capture_output=True, text=True)

    # Check if the upgrade command was successful
    if result.returncode != 0:
        print(f"Error during migration: {result.stderr}")
        return

    print(f"Database migration completed successfully:\n{result.stdout}")

def main():
    """Main function to run database management tasks."""
    print("Please select an option:")
    print("1) Reset Database")
    print("2) DB Migrate")

    choice = input("Enter your choice: ")

    if choice == "1":
        print("Resetting the database...")
        reset_database()
    elif choice == "2":
        print("Running migrations...")
        migrate_database()
    else:
        print("Invalid option selected. Exiting.")
        sys.exit(1)

if __name__ == "__main__":
    main()
