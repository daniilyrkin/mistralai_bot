from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine, AsyncAttrs
from sqlalchemy import DateTime, String, BigInteger, ForeignKey, Integer, NullPool, Boolean, select, insert
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from zoneinfo import ZoneInfo
from datetime import datetime
from dotenv import load_dotenv
import os
load_dotenv()

ADMIN = int(os.getenv('ADMIN'))

engine = create_async_engine('sqlite+aiosqlite:///mistralai_bot/db.sqlite3', poolclass=NullPool)

session_maker = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase, AsyncAttrs):
    created: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(ZoneInfo('Europe/Moscow')))


class User(Base):
    __tablename__ = "users"

    tg_id: Mapped[int] = mapped_column(BigInteger(), primary_key=True)
    username: Mapped[str] = mapped_column(String(100))
    models: Mapped[int] = mapped_column(Integer(), nullable=True)
    role: Mapped[str] = mapped_column(String(100))
    vip: Mapped[bool] = mapped_column(Boolean(), default=False)
    gigachat_switch: Mapped[bool] = mapped_column(Boolean(), default=False)


class Models_mistral(Base):
    __tablename__ = "models"

    id: Mapped[int] = mapped_column(Integer(), primary_key=True)
    name: Mapped[str] = mapped_column(String(20))


class Requests(Base):
    __tablename__ = "requests"

    id: Mapped[int] = mapped_column(Integer(), primary_key=True, autoincrement=True)
    tg_id: Mapped[str] = mapped_column(BigInteger(), ForeignKey('users.tg_id'))
    request: Mapped[str] = mapped_column(String())
    url: Mapped[str] = mapped_column(String(), nullable=True)
    file_id: Mapped[int] = mapped_column(String(), nullable=True)
    answer: Mapped[str] = mapped_column(String())


async def create_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        result = await conn.execute(select(Models_mistral))
        models_exist = result.scalars().first() is not None

        if not models_exist:
            # Добавляем данные в таблицу models, если она пустая
            await conn.execute(insert(Models_mistral).values([
                {"name": "mistral-small-latest"}]))

        result = await conn.execute(select(User))
        users_exist = result.scalars().first() is not None

        if not users_exist:
            await conn.execute(insert(User).values([
                {"tg_id": int(ADMIN), "username": "daniila_22", "role": "admin", "vip": True},
            ]))

        await conn.commit()
