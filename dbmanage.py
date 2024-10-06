import os
import subprocess
import sys

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Load environment variables from .env file
load_dotenv()

# Constants for database configuration
ALEMBIC_DIR = 'alembic'
DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_PORT = os.getenv("DB_PORT", "3306")  # Default to 3306 if not set

# Define MySQL connection strings
DATABASE_URL_WITHOUT_DB = f"mysql+pymysql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}"
SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


def execute_sql_command(engine, command):
    """Executes a given SQL command."""
    with engine.connect() as connection:
        connection.execute(text(command))


def reset_database():
    """Reset the database by dropping and recreating it, then creating all tables."""
    try:
        engine = create_engine(DATABASE_URL_WITHOUT_DB)

        # Drop the existing database if it exists
        execute_sql_command(engine, f"DROP DATABASE IF EXISTS {DB_NAME};")
        print(f"Database '{DB_NAME}' dropped successfully.")

        # Create the database again
        execute_sql_command(engine, f"CREATE DATABASE {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        print(f"Database '{DB_NAME}' created successfully.")

    except SQLAlchemyError as e:
        print(f"SQLAlchemyError in reset_database: {e}")
    except Exception as e:
        print(f"Error in reset_database: {e}")


def drop_database():
    """Drop the existing database."""
    try:
        engine = create_engine(SQLALCHEMY_DATABASE_URL)
        execute_sql_command(engine, f"DROP DATABASE IF EXISTS {DB_NAME}")
        print(f"Database '{DB_NAME}' dropped successfully.")
    except SQLAlchemyError as e:
        print(f"SQLAlchemyError in drop_database: {e}")
    except Exception as e:
        print(f"Error dropping database: {e}")


def initialize_alembic():
    """Initialize Alembic if it is not already initialized."""
    if not os.path.exists(ALEMBIC_DIR):
        print("Alembic not initialized. Initializing Alembic...")
        result = subprocess.run(["alembic", "init", ALEMBIC_DIR])
        if result.returncode == 0:
            print("Alembic initialized successfully.")
        else:
            print("Failed to initialize Alembic.")
    else:
        print("Alembic already initialized.")


def migrate_database():
    """Create a new Alembic revision and run the database migration."""
    initialize_alembic()

    # Create a new Alembic revision with a descriptive message
    revision_message = "create account table"
    result = subprocess.run(["alembic", "revision", "-m", revision_message], capture_output=True, text=True)

    if result.returncode != 0:
        print(f"Error creating Alembic revision: {result.stderr}")
        return
    print(f"Alembic revision created successfully: {result.stdout}")

    # Run the database migration (upgrade to the latest version)
    print("Starting database migration...")
    result = subprocess.run(["alembic", "upgrade", "head"], capture_output=True, text=True)

    if result.returncode != 0:
        print(f"Error during migration: {result.stderr}")
        return

    print(f"Database migration completed successfully:{result.stdout.title()}")


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
