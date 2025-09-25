from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine, AsyncAttrs
from sqlalchemy import DateTime, String, BigInteger, ForeignKey, Integer, NullPool
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from zoneinfo import ZoneInfo
from datetime import datetime

engine = create_async_engine('sqlite+aiosqlite:///mistralai_bot/db.sqlite3', poolclass=NullPool)

session_maker = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase, AsyncAttrs):
    created: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(ZoneInfo('Europe/Moscow')))


class User(Base):
    __tablename__ = "users"

    tg_id: Mapped[int] = mapped_column(BigInteger(), primary_key=True)
    username: Mapped[str] = mapped_column(String(100))
    models: Mapped[int] = mapped_column(Integer(), ForeignKey('users.tg_id'), nullable=True)
    role: Mapped[str] = mapped_column(String(100))


class Models(Base):
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


class Poll(Base):
    __tablename__ = "poll"

    id: Mapped[int] = mapped_column(Integer(), primary_key=True, autoincrement=True)
    question: Mapped[str] = mapped_column(String(100))
    options: Mapped[str] = mapped_column(String())
    user_answer_pool: Mapped[int] = mapped_column(Integer(), nullable=True)


class PollAnswer(Base):
    __tablename__ = "poll_answer"

    id: Mapped[int] = mapped_column(Integer(), primary_key=True, autoincrement=True)
    poll_id: Mapped[int] = mapped_column(Integer(), ForeignKey('poll.id'))
    tg_id: Mapped[int] = mapped_column(Integer(), ForeignKey('users.tg_id'))
    option: Mapped[int] = mapped_column(Integer())


class Settings(Base):
    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(Integer(), primary_key=True, autoincrement=True)
    settings_name: Mapped[str] = mapped_column(String())
    volume: Mapped[str] = mapped_column(String())


async def create_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
