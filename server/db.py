from typing import AsyncGenerator
import sys
import os

server_path = os.path.join(os.getcwd(), "server")
sys.path.insert(0, server_path)

from config import DATABASE_URL
from sqlalchemy.orm import declarative_base
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

Base = declarative_base()
metadata = Base.metadata

async_engine = create_async_engine(DATABASE_URL)
async_session_maker = async_sessionmaker(async_engine, expire_on_commit=False)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session
