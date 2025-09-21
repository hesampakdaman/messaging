from pathlib import Path

import asyncpg


async def apply_migrations(pool: asyncpg.Pool, dir_path: str) -> None:
    path = Path(dir_path)
    if not path.exists():
        return

    async with pool.acquire() as conn:
        for file in sorted(path.glob("*.sql")):
            sql = file.read_text(encoding="utf-8")
            if sql.strip():
                print(f"Applying migration {file.name}")
                _ = await conn.execute(sql)
