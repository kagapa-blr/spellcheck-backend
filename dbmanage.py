import os
import subprocess
import sys

from dotenv import load_dotenv

import alembic
from alembic import config
from database import Base, create_database_if_not_exists

# Load environment variables from .env file
load_dotenv()

ALEMBIC_DIR = 'alembic'  # Assuming the default Alembic folder is named 'alembic'

DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_PORT = os.getenv("DB_PORT", "3306")  # Default to 3306 if not set
# Function to reset the database
from sqlalchemy import create_engine, text

def reset_database():
    try:
        # Drop the existing database if it exists
        engine = create_engine(f"mysql+pymysql://{DB_USERNAME}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
        with engine.connect() as connection:
            connection.execute(text(f"DROP DATABASE IF EXISTS {DB_NAME};"))  # Drop the database
            print(f"Database '{DB_NAME}' dropped successfully.")

        # Create the database again
        with engine.connect() as connection:
            connection.execute(text(f"CREATE DATABASE {DB_NAME};"))  # Create the database
            print(f"Database '{DB_NAME}' created successfully.")

        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("All tables created successfully.")
    except Exception as e:
        print(f"Error in reset_database: {e}")

# Function to drop the existing database
def drop_database():
    try:
        database_url = 'mysql+pymysql://root:@127.0.0.1:3306/spellcheck'
        if not database_url:
            raise ValueError("DATABASE_URL environment variable is not set.")

        drop_engine = create_engine(database_url)

        with drop_engine.connect() as connection:
            connection.execute("DROP DATABASE IF EXISTS spellcheck")  # Replace 'spellcheck' with your database name
            print("Database 'spellcheck' dropped successfully.")
    except Exception as e:
        print(f"Error dropping database: {e}")


# Function to initialize Alembic if not already initialized
def initialize_alembic():
    if not os.path.exists(ALEMBIC_DIR):
        print("Alembic not initialized. Initializing Alembic...")
        subprocess.run(["alembic", "init", ALEMBIC_DIR])
        print("Alembic initialized successfully.")
    else:
        print("Alembic already initialized.")



def migrate_database():
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
    print("Please select an option:")
    print("1) Reset Database")
    print("2) DB Migrate")

    choice = input("Enter your choice: ")

    if choice == "1":
        print("Resetting the database...")
        create_database_if_not_exists()  # Ensure database exists before resetting
        reset_database()

    elif choice == "2":
        print("Running migrations...")
        migrate_database()

    else:
        print("Invalid option selected. Exiting.")
        sys.exit(1)


if __name__ == "__main__":
    main()
