import os
import sys

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Load environment variables from .env file
load_dotenv()

# Constants for database configuration
DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_PORT = os.getenv("DB_PORT", "3306")  # Default to 3306 if not set

# Define MySQL connection strings
DATABASE_URL_WITHOUT_DB = f"mysql+pymysql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}"
SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


def execute_sql_command(engine, command):
    with engine.connect() as connection:
        connection.execute(text(command))


def fetch_tables():
    """Fetch all tables from the current database."""
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    with engine.connect() as conn:
        result = conn.execute(text("SHOW TABLES"))
        return [row[0] for row in result.fetchall()]


def reset_full_database():
    try:
        confirm = input(f"This will DROP and RECREATE the database '{DB_NAME}'. Type YES to continue: ")
        if confirm != "YES":
            print("Operation cancelled.")
            return

        engine = create_engine(DATABASE_URL_WITHOUT_DB)

        execute_sql_command(engine, f"DROP DATABASE IF EXISTS {DB_NAME};")
        print(f"Database '{DB_NAME}' dropped successfully.")

        execute_sql_command(
            engine,
            f"CREATE DATABASE {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
        )
        print(f"Database '{DB_NAME}' created successfully.")

    except SQLAlchemyError as e:
        print(f"SQLAlchemyError in reset_full_database: {e}")


def reset_selected_tables():
    try:
        tables = fetch_tables()

        if not tables:
            print("No tables found in database.")
            return

        print("\nAvailable Tables:")
        for i, table in enumerate(tables, start=1):
            print(f"{i}) {table}")

        selected = input("\nEnter table numbers to reset (comma separated, e.g. 1,3,5): ").strip()

        indexes = [int(x.strip()) - 1 for x in selected.split(",") if x.strip().isdigit()]
        selected_tables = [tables[i] for i in indexes if 0 <= i < len(tables)]

        if not selected_tables:
            print("No valid tables selected.")
            return

        print("\nSelected tables:")
        for t in selected_tables:
            print(f" - {t}")

        confirm = input("\n This will DROP selected tables. Type YES to continue: ")
        if confirm.lower() != "yes" or confirm.lower()=='y':
            print("Operation cancelled.")
            return

        engine = create_engine(SQLALCHEMY_DATABASE_URL)
        for table in selected_tables:
            execute_sql_command(engine, f"DROP TABLE IF EXISTS `{table}`;")
            print(f"Table '{table}' dropped successfully.")

        print("\n✅ Done. Recreate tables using Alembic or app startup.")

    except SQLAlchemyError as e:
        print(f"SQLAlchemyError in reset_selected_tables: {e}")
    except Exception as e:
        print(f"Error in reset_selected_tables: {e}")


def main():
    print("\nDatabase Reset Utility")
    print("1) Reset FULL Database (Drop & Recreate DB)")
    print("2) Reset Specific Tables (Select from list)")

    choice = input("\nEnter your choice: ").strip()

    if choice == "1":
        reset_full_database()
    elif choice == "2":
        reset_selected_tables()
    else:
        print("Invalid option selected.")
        sys.exit(1)


if __name__ == "__main__":
    main()