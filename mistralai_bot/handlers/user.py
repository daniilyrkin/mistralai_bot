from aiogram import Router, F, html
from aiogram.filters import Command
from aiogram.types import PollAnswer
from aiogram.types import Message, CallbackQuery
from mistralai_bot.utils.logger import logger
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.fsm.context import FSMContext
from mistralai_bot.orm_query import orm_add, orm_get_one, orm_update
from mistralai_bot.mist_api import api_get
from mistralai_bot.state.states import Load
from mistralai_bot.keyboards.keyboards import Keyboards_all as keyboards
import asyncio
from mistralai_bot.config import bot
import os
from dotenv import load_dotenv

load_dotenv()

ADMIN = int(os.getenv('ADMIN'))
user_router = Router()

models = {
    'codestral': 'cg.codestral-latest',
    'mistral-large': 'cg.mistral-large-latest',
    'mistral-small': 'cg.mistral-small-latest'
}


@user_router.message(Command('start', 'help', 'menu'))
async def help(message: Message, session: AsyncSession):
    username = message.from_user.username
    user_id = message.from_user.id
    keyboard = await keyboards.reply_key_builder('Выбрать модель')
    await orm_add(
        session=session, tablename='User',
        data=({
            'tg_id': user_id, 'username': username,
            'role': 'user'}))
    await message.answer(
        text=f"Приветствую {message.from_user.first_name}!\n"
        "Я бот, взаимодействующий с API MistralAI. Все бесплатно, но на твоих запросах они будут обучать свой ИИ 🌚\n"
        "Так же ИИ не запоминает последнее сообщение и может нести не связанную бессмыслицу.\n"
        "Нажми кнопку *Выбрать модель* и выбери модель, чтобы начать работу.\n"
        "После выбора модели можете сразу писать боту свой запрос\n"
        "Это не официальный бот MistralAI !!!",
        parse_mode='Markdown',
        reply_markup=keyboard)
    await logger(message, text=message.text)


@user_router.message(F.text == 'Выбрать модель')
async def change_model(message: Message):
    keyboard = await keyboards.inline_key_builder(models)
    await message.answer(
        text=(
            'Поясню по кнопкам.\n'
            '*codestral* - ИИ будет лучше работать с кодом.\n'
            '*mistral-large* - ИИ будет работать лучше с текстом\n'
            '*mistral-small* - ИИ работает быстрее, но есть нюансы...'),
        parse_mode='Markdown',
        reply_markup=keyboard)


@user_router.callback_query(F.data.startswith('cg'))
async def cancel_change_model(callback: CallbackQuery, session: AsyncSession):
    model = callback.data.split('.')
    user_id = callback.from_user.id
    await orm_update(
        tablename='User', session=session,
        filter_arg={'tg_id': user_id},
        new_data={'models': model[1]})
    await callback.message.answer('Модель успешно выбрана!')


@user_router.message(Load.load)
async def load(message: Message):
    mes = await message.answer('Ваше сообщение генерируется...')
    await asyncio.sleep(2)
    await mes.delete()


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


@user_router.message()
async def echo(message: Message, session: AsyncSession, state: FSMContext):
    await state.set_state(Load.load)
    mes = await message.answer('Загрузка...⏳')
    try:
        data = {
            "url": None}

        text = message.text
        entities = message.entities

        for item in entities:
            if item.type in data.keys():
                data[item.type] = item.extract_from(text)

        content_data = {
            'text': str(text).replace(html.quote(data['url']), ''),
            'url': html.quote(data['url'])
        }

        user_data = await orm_get_one(session=session, tablename='User', kwargs=({'tg_id': message.from_user.id}))

        answer_mistral = await api_get(
            api_key=os.getenv('Mistral_API'),
            model=user_data.models,
            content=content_data)

        await orm_add(
            session=session, tablename='Requests',
            data=({
                'tg_id': message.from_user.id,
                'answer':
                    (f'Mistral_AI:\n{answer_mistral}\n\n'),
                'request': str(content_data)
            }))
        for x in range(0, len(answer_mistral), 4096):
            txt = answer_mistral[x: x + 4096]
            await message.answer(txt, parse_mode='MarkdownV2')
    except Exception as ex:
        await bot.send_message(
            chat_id=int(ADMIN),
            text=f'Ошибка по запросу: {message.text}\nТекст ошибки: {str(ex)}')
        await message.answer('Ошибка на сервере, попробуйте позже...')
    finally:
        await mes.delete()
        await state.clear()
