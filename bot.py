import logging.handlers
from aiogram import Dispatcher
import os

from art import tprint
from colorama import Fore, init
import asyncio
import logging
from mistralai_bot.database_eng import create_db, session_maker
from mistralai_bot.middlewares.db import DataBaseSession
from mistralai_bot.handlers import admin, user

from mistralai_bot.config import bot, storage
from dotenv import load_dotenv

load_dotenv()


ADMIN = int(os.getenv('ADMIN'))


async def on_startup():
    try:
        await create_db()
        text = 'Database is running!\nBot is running!\nGreat!'
        print(Fore.GREEN + text)
    except Exception as ex:
        text = str(ex)
        print(Fore.RED + text)
    await bot.send_message(chat_id=ADMIN, text=text)


async def main():
    format = ('%(asctime)s - [%(levelname)s] - %(name)s - [%(module)s]'
              "(%(filename)s).%(funcName)s(%(lineno)d) - %(message)s")
    logging.basicConfig(level=logging.INFO, format=format, filename='mistralai_bot/bot.log')

    dp = Dispatcher(storage=storage)
    dp.include_routers(
        admin.admin, user.user_router)
    dp.startup.register(on_startup)
    dp.update.middleware(DataBaseSession(session_pool=session_maker))

    init(autoreset=True)

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()

if __name__ == "__main__":
    tprint('Start Bot', font='doom', space=2)
    asyncio.run(main())
