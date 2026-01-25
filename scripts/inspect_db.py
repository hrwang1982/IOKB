import asyncio
import sys
import os

sys.path.append(os.getcwd())

from app.core.database import init_db, async_session_maker
from app.models.cmdb import CIType
from sqlalchemy import select

async def inspect():
    await init_db()
    async with async_session_maker() as db:
        result = await db.execute(select(CIType))
        types = result.scalars().all()
        print(f"Found {len(types)} CI Types:")
        print("-" * 60)
        print(f"{'ID':<5} | {'Code':<20} | {'Name':<20}")
        print("-" * 60)
        for t in types:
            code_repr = f"'{t.code}'" if t.code is not None else "None"
            print(f"{t.id:<5} | {code_repr:<20} | {t.name:<20}")

if __name__ == "__main__":
    asyncio.run(inspect())
