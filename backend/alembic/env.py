import asyncio
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import settings  # noqa: E402
from app.core.db import Base  # noqa: E402
from app.models import models  # noqa: F401,E402  (ensures models are registered on Base.metadata)

config = context.config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=settings.DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    import os
    import urllib.parse

    db_url = settings.DATABASE_URL
    try:
        parsed = urllib.parse.urlsplit(db_url)
        print(f"\n[ALEMBIC] Connecting to host: '{parsed.hostname}' on port '{parsed.port}' (db: '{parsed.path}')", flush=True)
    except Exception as e:
        print(f"\n[ALEMBIC] Database URL parse error: {e}", flush=True)

    if ("localhost" in db_url or "127.0.0.1" in db_url) and (os.environ.get("RENDER") or os.environ.get("PORT")):
        print("\n" + "!" * 80, flush=True)
        print("CRITICAL CONFIGURATION ERROR:", flush=True)
        print("DATABASE_URL is NOT SET in Render Environment Variables!", flush=True)
        print("Alembic is defaulting to localhost:5432, which does not exist in this container.", flush=True)
        print("Please go to Render Dashboard -> Environment and add DATABASE_URL.", flush=True)
        print("!" * 80 + "\n", flush=True)

    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        url=settings.DATABASE_URL,
        connect_args={"statement_cache_size": 0},
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())