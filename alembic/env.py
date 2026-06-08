import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# --------------------------------------------------
# Add project root to sys.path
# --------------------------------------------------
BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR))

# --------------------------------------------------
# Alembic Config
# --------------------------------------------------
config = context.config

# --------------------------------------------------
# Import DB URL + Base
# --------------------------------------------------
from app.config.database import SQLALCHEMY_DATABASE_URL, Base

# IMPORTANT: force model registration
# This ensures all models are loaded into Base.metadata
from app.dbmodels import models  # noqa: F401

# Override DB URL from alembic.ini
config.set_main_option("sqlalchemy.url", SQLALCHEMY_DATABASE_URL)
print(f"SQLALCHEMY_DATABASE_URL: {SQLALCHEMY_DATABASE_URL}")
# Setup logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# --------------------------------------------------
# Target metadata
# --------------------------------------------------
target_metadata = Base.metadata

# Debug: show detected tables
print("\n========= Tables detected by Alembic =========")
for table_name in target_metadata.tables.keys():
    print(f" - {table_name}")
print("=============================================\n")


# --------------------------------------------------
# Offline migrations
# --------------------------------------------------
def run_migrations_offline():
    context.configure(
        url=SQLALCHEMY_DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


# --------------------------------------------------
# Online migrations
# --------------------------------------------------
def run_migrations_online():
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


# --------------------------------------------------
# Entry point
# --------------------------------------------------
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
