from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional


Base = declarative_base()

from loggerflow.lifecycle.database.models import LFSettings


class Database:
    _instance = None

    def __new__(cls, database_url: Optional[str] = None):
        if cls._instance is None and database_url is not None:
            cls._instance = super().__new__(cls)
            cls._instance.engine = create_async_engine(database_url, echo=False)
            cls._instance.async_session = sessionmaker(cls._instance.engine, expire_on_commit=False, class_=AsyncSession)
            return cls._instance
        return cls

    async def init(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            async with self.session() as session:
                result = await session.execute(select(LFSettings))
                settings = result.scalars().first()
                if not settings:
                    settings = LFSettings(
                        show_first_clean_traceback=False,
                        show_process_memory=False,
                        # save_metrics=True,
                        backlight_traceback=True
                    )
                    session.add(settings)
                    await session.commit()



    @classmethod
    @asynccontextmanager
    async def session(cls) -> AsyncGenerator[AsyncSession, None]:
        async_session = cls._instance.async_session()
        try:
            yield async_session
        finally:
            await async_session.close()

    async def get_session(self) -> AsyncSession:
        # for FastAPI to Depends
        async with self.async_session() as async_session:
            try:
                yield async_session
            finally:
                await async_session.close()

