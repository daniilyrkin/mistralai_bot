from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, PollAnswer
from mistralai_bot.utils.logger import logger
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.fsm.context import FSMContext
from mistralai_bot.orm_query import orm_add, orm_get_latest_record, orm_update, orm_get
from mistralai_bot.mist_api import get_mistral_api, get_gigachat_api
from mistralai_bot.state.states import Load
from mistralai_bot.keyboards.keyboards import Keyboards_all as keyboards
import asyncio
from mistralai_bot.config import bot
import os
from dotenv import load_dotenv

load_dotenv()

ADMIN = int(os.getenv('ADMIN'))
user_router = Router()


async def reg_user(message: Message, session: AsyncSession):
    username = message.from_user.username
    user_id = message.from_user.id
    await orm_add(
        session=session, tablename='User',
        data=({
            'tg_id': user_id, 'username': username,
            'role': 'user', 'models': 1}))


@user_router.message(Command('start', 'help', 'menu'))
async def help(message: Message, session: AsyncSession):
    username = message.from_user.username
    user_id = message.from_user.id
    await orm_add(
        session=session, tablename='User',
        data=({
            'tg_id': user_id, 'username': username,
            'role': 'user'}))
    await message.answer(
        text=f"Приветствую {message.from_user.first_name}!\n"
        "Я бот, взаимодействующий с API MistralAI(бесплатно), а также API Gigachat(платно)🌚\n"
        "Так же ИИ не запоминает последнее сообщение и может нести не связанную бессмыслицу.\n"
        "Нажми кнопку *Выбрать модель* и выбери модель, чтобы начать работу.\n"
        "После выбора модели можете сразу писать боту свой запрос\n",
        parse_mode='Markdown')
    await logger(message, text=message.text)


@user_router.message(Command('info'))
async def info_user(message: Message, session: AsyncSession):
    user_data = await orm_get_latest_record(
        session=session, tablename='User', filters=({'tg_id': message.from_user.id})
    )
    if user_data.models is not None:
        model = await orm_get_latest_record(session=session, tablename='Models', filters=({'id': user_data.models}))
    req = 0
    for req_info in await orm_get(session=session, tablename='Requests'):
        if int(req_info.tg_id) == int(message.from_user.id):
            req += 1
    await message.answer(
        text=f"Имя: {user_data.username}\nВыбранная модель: {model.name}\nКол-во запросов за все время: {req}")


@user_router.message(Command('switch_giga'))
async def switch_giga(message: Message, session: AsyncSession):
    user_data = await orm_get_latest_record(
        session=session, tablename='User', filters=({'tg_id': message.from_user.id})
    )
    if user_data.vip is True:
        giga_switch = not user_data.gigachat_switch
        await orm_update(
            tablename='User', session=session,
            filter_arg={'tg_id': message.from_user.id},
            new_data={'gigachat_switch': giga_switch})
        if giga_switch is True:
            await message.answer('GigaChat активен.')
        else:
            await message.answer('GigaChat не активен.')
    else:
        await message.answer('У вас нет доступа...')


@user_router.message(F.text == 'Выбрать модель')
@user_router.message(Command('models'))
async def change_model(message: Message, session: AsyncSession):
    models = {}
    for model in await orm_get(session=session, tablename='Models'):
        models[model.name] = ('cg.' + str(model.id))
    keyboard = await keyboards.inline_key_builder(models)
    await message.answer(
        text=(
            'Выберите модель из списка.'),
        parse_mode='Markdown',
        reply_markup=keyboard)


@user_router.callback_query(F.data.startswith('cg'))
async def cancel_change_model(callback: CallbackQuery, session: AsyncSession):
    model = callback.data.split('.')
    user_id = callback.from_user.id
    await orm_update(
        tablename='User', session=session,
        filter_arg={'tg_id': user_id},
        new_data={'models': int(model[1])})
    await callback.message.answer('Модель успешно выбрана!')


@user_router.poll_answer()
async def handle_poll_answer(poll_answer: PollAnswer):
    user_id = poll_answer.user.id
    user_name = poll_answer.user.username
    poll_id = poll_answer.poll_id
    option_ids = poll_answer.option_ids

    await bot.send_message(chat_id=user_id, text='Спасибо за ваш ответ!')
    await bot.send_message(
        chat_id=ADMIN,
        text=f"User {user_id} (@{user_name}) answered poll {poll_id} with options {option_ids}")


# Ответ бота на сообщение
@user_router.message(Load.load)
async def load(message: Message):
    mes = await message.answer('Подожди, я еще не ответил...')
    await asyncio.sleep(2)
    await mes.delete()


# Ожидание ответа от бота
async def send_typing_action(chat_id):
    await asyncio.sleep(1)
    while True:
        await bot.send_chat_action(chat_id, 'typing')
        await asyncio.sleep(5)


async def save_request(session: AsyncSession, user_id: int, request_text: str, answer: str):
    await orm_add(
        session=session, tablename='Requests',
        data={
            'tg_id': user_id,
            'answer': answer,
            'request': request_text,
            'url': None
        })


async def send_answer(message: Message, answer: str):
    for x in range(0, len(answer), 4096):
        txt = answer[x: x + 4096]
        await message.answer(txt, parse_mode='MarkdownV2')


async def handle_error(message: Message, ex: Exception):
    await bot.send_message(
        chat_id=int(ADMIN),
        text=f'Ошибка по запросу: {message.text}\n'
             f'Пользователь: @{message.from_user.username}\n'
             f'Текст ошибки: {str(ex)}')
    await message.answer('Ошибка на сервере, попробуйте позже...')


async def func(session: AsyncSession, user_data, text: str):
    model = await orm_get_latest_record(session=session, tablename='Models', filters={'id': user_data.models})

    content_dict = {'system': '', 'user': text}

    if user_data.gigachat_switch is True:
        mistral_answer = await get_mistral_api(
            api_key=os.getenv('Mistral_API'),
            model=model.name,
            content=content_dict)

        gigachat_answer = await get_gigachat_api(
            api_key=os.getenv('GIGACHAT_KEY'),
            model='GigaChat',
            content=content_dict)

        return f'MistralAI : {mistral_answer}\n\nGigachat: {gigachat_answer}'
    else:
        return await get_mistral_api(
            api_key=os.getenv('Mistral_API'),
            model=model.name,
            content=content_dict)


@user_router.message()
async def echo(message: Message, session: AsyncSession, state: FSMContext):
    user_data = await orm_get_latest_record(
        session=session, tablename='User', filters={'tg_id': message.from_user.id})
    await state.set_state(Load.load)
    try:
        typing_task = asyncio.create_task(send_typing_action(message.chat.id))
        text = str(message.text)
        answer = await func(session=session, user_data=user_data, text=text)
        await save_request(session=session, user_id=int(message.from_user.id), request_text=text, answer=answer)
        await send_answer(message, answer)
    except Exception as ex:
        await handle_error(message, ex)
    finally:
        typing_task.cancel()
        await state.clear()
