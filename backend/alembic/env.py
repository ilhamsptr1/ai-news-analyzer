"""
Alembic migration environment.
Reads DATABASE_URL from application settings (loaded from .env).
Password is never hardcoded here.
"""

import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# ── Add backend/ to sys.path so app modules are importable ──────────────────
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# ── Import app settings and models ──────────────────────────────────────────
from app.config import settings  # noqa: E402
from app.database import Base  # noqa: E402
import app.models  # noqa: E402, F401  — registers all ORM models with metadata

# ── Alembic Config object ────────────────────────────────────────────────────
config = context.config

# ── Logging ─────────────────────────────────────────────────────────────────
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ── Override sqlalchemy.url from our settings (no hardcoded password) ───────
config.set_main_option("sqlalchemy.url", settings.database_url)

# ── Target metadata for autogenerate ────────────────────────────────────────
target_metadata = Base.metadata


# ── Offline migration ────────────────────────────────────────────────────────
def run_migrations_offline() -> None:
    """Run migrations without a live database connection (generates SQL)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


# ── Online migration ─────────────────────────────────────────────────────────
def run_migrations_online() -> None:
    """Run migrations against a live database connection."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
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


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
