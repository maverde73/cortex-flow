"""
State persistence configuration for LangGraph agents (FASE 5 - PostgreSQL Support).

Provides checkpoint backends for saving and restoring agent state.
Supports: Memory (dev), PostgreSQL (production), Redis (future).
"""

import logging
from typing import Optional
from langgraph.checkpoint.memory import MemorySaver
from config_legacy import settings

logger = logging.getLogger(__name__)


def get_checkpointer():
    """
    Factory function to get the appropriate checkpointer based on configuration.

    Returns:
        A LangGraph checkpointer instance

    Raises:
        ValueError: If checkpoint_backend is not supported
    """
    backend = settings.checkpoint_backend.lower()

    if backend == "memory":
        # WARNING: This is ephemeral and only for development
        # State will be lost when the process restarts
        logger.info("Using MemorySaver (non-persistent, dev only)")
        return MemorySaver()

    elif backend == "postgres":
        try:
            from langgraph.checkpoint.postgres import PostgresSaver
            import psycopg
            from psycopg_pool import ConnectionPool

            logger.info(f"Initializing PostgreSQL checkpointer")

            # Create connection pool
            pool = ConnectionPool(
                conninfo=settings.postgres_url,
                max_size=20,
                kwargs={"autocommit": True, "prepare_threshold": 0}
            )

            # Create checkpointer with pool
            checkpointer = PostgresSaver(pool)

            # Setup tables (creates if not exists)
            checkpointer.setup()

            logger.info("PostgreSQL checkpointer initialized successfully")
            return checkpointer

        except ImportError as e:
            logger.error(f"PostgreSQL dependencies not installed: {e}")
            logger.error("Install with: pip install langgraph-checkpoint-postgres psycopg2-binary")
            raise RuntimeError("PostgreSQL checkpointer dependencies missing") from e

        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL checkpointer: {e}")
            logger.error(f"Check POSTGRES_URL in .env: {settings.postgres_url}")
            raise RuntimeError(f"PostgreSQL checkpointer initialization failed: {e}") from e

    elif backend == "redis":
        try:
            from langgraph.checkpoint.redis import RedisSaver
            import redis

            logger.info(f"Initializing Redis checkpointer")

            # Parse Redis URL and create client
            redis_client = redis.from_url(settings.redis_url)

            # Create checkpointer
            checkpointer = RedisSaver(redis_client)

            logger.info("Redis checkpointer initialized successfully")
            return checkpointer

        except ImportError as e:
            logger.error(f"Redis dependencies not installed: {e}")
            logger.error("Install with: pip install langgraph-checkpoint-redis redis")
            raise RuntimeError("Redis checkpointer dependencies missing") from e

        except Exception as e:
            logger.error(f"Failed to initialize Redis checkpointer: {e}")
            logger.error(f"Check REDIS_URL in .env: {settings.redis_url}")
            raise RuntimeError(f"Redis checkpointer initialization failed: {e}") from e

    else:
        raise ValueError(
            f"Unknown checkpoint backend: {backend}. "
            f"Supported options: memory, postgres, redis"
        )


# Global checkpointer instance (singleton)
_checkpointer: Optional[object] = None


def init_checkpointer():
    """Initialize global checkpointer instance."""
    global _checkpointer
    if _checkpointer is None:
        _checkpointer = get_checkpointer()
    return _checkpointer


def get_global_checkpointer():
    """Get or create global checkpointer instance."""
    if _checkpointer is None:
        return init_checkpointer()
    return _checkpointer
