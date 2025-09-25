from sqlalchemy import select, delete, insert, update
from sqlalchemy.ext.asyncio import AsyncSession

from mistralai_bot.database_eng import User, Requests, Poll, PollAnswer, Models


dict_tables = {
    'User': User,
    'Models': Models,
    'Requests': Requests,
    'Poll': Poll,
    'PollAnswer': PollAnswer}


async def orm_get(tablename: str, session: AsyncSession, desc_bool: bool = False):
    if desc_bool is False:
        query = select(dict_tables[tablename])
    else:
        query = select(dict_tables[tablename]).order_by(dict_tables[tablename].created.desc())
    result = await session.execute(query)
    return result.scalars().all()


async def orm_get_one(tablename: str, session: AsyncSession, kwargs=None):
    if kwargs is None:
        return await session.scalar(
            select(dict_tables[tablename]).order_by(dict_tables[tablename].id.desc()).limit(1))
    else:
        return await session.scalar(select(dict_tables[tablename]).filter_by(**kwargs if kwargs == dict else kwargs))


async def orm_add(tablename: str, session: AsyncSession, data: dict):
    item = await orm_get_one(tablename=tablename, session=session, kwargs=data)
    if not item:
        await session.execute(insert(dict_tables[tablename]).values(**data))
        await session.commit()


async def orm_update(session: AsyncSession, tablename: str, filter_arg: dict, new_data: dict):
    item = await session.scalar(select(dict_tables[tablename]).filter_by(**filter_arg))
    if item:
        await session.execute(update(dict_tables[tablename]).filter_by(**filter_arg).values(**new_data))
        await session.commit()


async def orm_delete(session: AsyncSession, tablename: str, **kwargs):
    item = await session.scalar(select(dict_tables[tablename]).filter_by(**kwargs))
    if item:
        await session.execute(delete(dict_tables[tablename]).filter_by(**kwargs))
        await session.commit()
