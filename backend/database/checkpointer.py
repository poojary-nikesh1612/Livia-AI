"""database/checkpointer.py: LangGraph specific connection pool for Supabase."""

import logging
from contextlib import asynccontextmanager

from config.settings import settings
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

logger = logging.getLogger(__name__)


@asynccontextmanager
async def get_postgres_checkpointer():
    """
    Yields an AsyncPostgresSaver connected to Supabase.
    Automatically manages its own async connection pool.
    """

    # Clean the URL for LangGraph (Remove SQLAlchemy's '+psycopg' tag)
    langgraph_db_url = settings.DATABASE_URL.replace("+psycopg", "")

    # Pass the cleaned URL to LangGraph
    async with AsyncPostgresSaver.from_conn_string(langgraph_db_url) as saver:
        try:
            logger.info("LangGraph Checkpointer connected to Supabase.")
            yield saver

        except Exception as e:
            logger.error(f"Failed to initialize LangGraph Checkpointer: {e}")
            raise
