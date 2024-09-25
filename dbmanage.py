import os
import subprocess
import sys

import alembic.command
import alembic.config
from dotenv import load_dotenv

from database import Base, engine, create_database_if_not_exists

# Load environment variables from .env file
load_dotenv()

ALEMBIC_DIR = 'alembic'  # Assuming the default Alembic folder is named 'alembic'


# Function to reset the database
def reset_database():
    # Recreate database by dropping all tables and creating them again
    Base.metadata.drop_all(bind=engine)  # Drop all tables
    print("All tables dropped.")

    Base.metadata.create_all(bind=engine)  # Create all tables
    print("All tables created successfully.")


# Function to initialize Alembic if not already initialized
def initialize_alembic():
    if not os.path.exists(ALEMBIC_DIR):
        print("Alembic not initialized. Initializing Alembic...")
        subprocess.run(["alembic", "init", ALEMBIC_DIR])
        print("Alembic initialized successfully.")
    else:
        print("Alembic already initialized.")


# Function to run Alembic migrations
def migrate_database():
    initialize_alembic()

    # Alembic configuration file path
    alembic_cfg = alembic.config.Config("alembic.ini")

    # Run the migration
    alembic.command.upgrade(alembic_cfg, "head")
    print("Database migration completed successfully.")


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
