from sqlalchemy import select, delete, insert, update
from sqlalchemy.ext.asyncio import AsyncSession

from mistralai_bot.database_eng import User, Requests, Models_mistral


dict_tables = {
    'User': User,
    'Models': Models_mistral,
    'Requests': Requests}


async def orm_get(
        tablename: str, session: AsyncSession, limit: int = None, filters: dict = None, desc_bool: bool = True):
    if desc_bool is False:
        query = select(dict_tables[tablename])
    else:
        query = select(dict_tables[tablename]).order_by(dict_tables[tablename].created.desc())
    if filters:
        query = query.filter_by(**filters)
    if limit:
        query = query.limit(limit)
    result = await session.execute(query)
    return result.scalars().all()


async def orm_get_latest_record(tablename: str, session: AsyncSession, filters: dict = None):
    if filters is None:
        return await session.scalar(
            select(dict_tables[tablename]).order_by(dict_tables[tablename].created.desc()))
    else:
        return await session.scalar(
            select(dict_tables[tablename]).filter_by(**filters).order_by(dict_tables[tablename].created.desc()))


async def orm_add(tablename: str, session: AsyncSession, data: dict):
    item = await orm_get_latest_record(tablename=tablename, session=session, filters=data)
    if not item:
        await session.execute(insert(dict_tables[tablename]).values(**data))
        await session.commit()


async def orm_update(session: AsyncSession, tablename: str, filter_arg: dict, new_data: dict):
    item = await session.scalar(select(dict_tables[tablename]).filter_by(**filter_arg))
    if item:
        await session.execute(update(dict_tables[tablename]).filter_by(**filter_arg).values(**new_data))
        await session.commit()


async def orm_delete(session: AsyncSession, tablename: str, del_obj: dict):
    item = await session.scalar(select(dict_tables[tablename]).filter_by(**del_obj))
    if item:
        await session.execute(delete(dict_tables[tablename]).filter_by(**del_obj))
        await session.commit()
