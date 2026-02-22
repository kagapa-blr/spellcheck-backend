import sys
from pathlib import Path
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Import your SQLAlchemy Base and DB URL
from config.database import SQLALCHEMY_DATABASE_URL, Base

# Add project root to PYTHONPATH (so Alembic can find your modules)
BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR))

# IMPORTANT: import all models so Alembic can see the tables
from dbmodels.models import User, MainDictionary, UserAddedWord, Suggestion

# Alembic Config object
config = context.config

# Override sqlalchemy.url from alembic.ini with your app's database URL
config.set_main_option("sqlalchemy.url", SQLALCHEMY_DATABASE_URL)

# Setup logging from alembic.ini if present
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set metadata for autogenerate
target_metadata = Base.metadata

# --- DEBUG: print all tables Alembic sees ---
print("Tables detected for migration:")
for table_name in target_metadata.tables.keys():
    print(f" - {table_name}")
print("------------------------------------------------\n")


def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    context.configure(
        url=SQLALCHEMY_DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,  # detect column type changes
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


# Run the appropriate migration mode
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()