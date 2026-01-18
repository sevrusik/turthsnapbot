"""
Database connection manager

Handles PostgreSQL connection pooling using asyncpg
"""

import asyncpg
import logging
from typing import Optional
from contextlib import asynccontextmanager
import sys
import os

# Add parent to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config.settings import settings

logger = logging.getLogger(__name__)


class Database:
    """
    PostgreSQL connection pool manager
    """

    _pool: Optional[asyncpg.Pool] = None

    @classmethod
    async def connect(cls):
        """
        Initialize connection pool
        """
        if cls._pool is None:
            logger.info(f"Connecting to PostgreSQL: {settings.DATABASE_URL.split('@')[1]}")

            cls._pool = await asyncpg.create_pool(
                settings.DATABASE_URL,
                min_size=2,
                max_size=10,
                command_timeout=60
            )

            logger.info("PostgreSQL connection pool created")

    @classmethod
    async def disconnect(cls):
        """
        Close connection pool
        """
        if cls._pool:
            await cls._pool.close()
            cls._pool = None
            logger.info("PostgreSQL connection pool closed")

    @classmethod
    @asynccontextmanager
    async def acquire(cls):
        """
        Acquire connection from pool

        Usage:
            async with Database.acquire() as conn:
                await conn.execute("SELECT 1")
        """
        if cls._pool is None:
            await cls.connect()

        async with cls._pool.acquire() as connection:
            yield connection

    @classmethod
    async def execute(cls, query: str, *args):
        """
        Execute query without returning results

        Args:
            query: SQL query
            *args: Query parameters
        """
        async with cls.acquire() as conn:
            return await conn.execute(query, *args)

    @classmethod
    async def fetch(cls, query: str, *args):
        """
        Fetch multiple rows

        Args:
            query: SQL query
            *args: Query parameters

        Returns:
            List of records
        """
        async with cls.acquire() as conn:
            return await conn.fetch(query, *args)

    @classmethod
    async def fetchrow(cls, query: str, *args):
        """
        Fetch single row

        Args:
            query: SQL query
            *args: Query parameters

        Returns:
            Single record or None
        """
        async with cls.acquire() as conn:
            return await conn.fetchrow(query, *args)

    @classmethod
    async def fetchval(cls, query: str, *args):
        """
        Fetch single value

        Args:
            query: SQL query
            *args: Query parameters

        Returns:
            Single value or None
        """
        async with cls.acquire() as conn:
            return await conn.fetchval(query, *args)


# Global database instance
db = Database()
