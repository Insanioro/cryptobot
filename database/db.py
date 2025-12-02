import asyncpg
from typing import Optional

from config import PG_DSN


class Database:
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self) -> None:
        self.pool = await asyncpg.create_pool(dsn=PG_DSN)
        await self._create_tables()

    async def close(self) -> None:
        if self.pool:
            await self.pool.close()

    async def _create_tables(self) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    language VARCHAR(5) DEFAULT 'en',
                    join_date TIMESTAMP DEFAULT NOW()
                )
            """)

    async def add_user(self, user_id: int) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO users (user_id) VALUES ($1) ON CONFLICT DO NOTHING",
                user_id
            )

    async def set_language(self, user_id: int, lang: str) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute(
                "UPDATE users SET language = $2 WHERE user_id = $1",
                user_id, lang
            )

    async def get_language(self, user_id: int) -> str:
        async with self.pool.acquire() as conn:
            result = await conn.fetchval(
                "SELECT language FROM users WHERE user_id = $1",
                user_id
            )
            return result if result else "en"


db = Database()
