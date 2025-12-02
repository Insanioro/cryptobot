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
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS username_valuations (
                    username VARCHAR(33) PRIMARY KEY,
                    structure VARCHAR(50),
                    category VARCHAR(50),
                    rarity VARCHAR(50),
                    demand VARCHAR(50),
                    score VARCHAR(10),
                    branding VARCHAR(50),
                    price_low INTEGER,
                    price_high INTEGER,
                    created_at TIMESTAMP DEFAULT NOW()
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

    async def get_valuation(self, username: str) -> dict | None:
        """Get cached valuation for username."""
        clean_username = username.lstrip("@").lower()
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM username_valuations WHERE username = $1",
                clean_username
            )
            if row:
                return {
                    "username": f"@{clean_username}",
                    "structure": row["structure"],
                    "category": row["category"],
                    "rarity": row["rarity"],
                    "demand": row["demand"],
                    "score": row["score"],
                    "branding": row["branding"],
                    "price_low": row["price_low"],
                    "price_high": row["price_high"],
                }
            return None

    async def save_valuation(self, data: dict) -> None:
        """Save valuation data to cache."""
        clean_username = data["username"].lstrip("@").lower()
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO username_valuations 
                (username, structure, category, rarity, demand, score, branding, price_low, price_high)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ON CONFLICT (username) DO NOTHING
                """,
                clean_username,
                data["structure"],
                data["category"],
                data["rarity"],
                data["demand"],
                data["score"],
                data["branding"],
                data["price_low"],
                data["price_high"]
            )


db = Database()
