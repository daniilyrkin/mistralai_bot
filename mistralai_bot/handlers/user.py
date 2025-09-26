from aiogram import Router, F, html
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, PollAnswer
from mistralai_bot.utils.logger import logger
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.fsm.context import FSMContext
from mistralai_bot.orm_query import orm_add, orm_get_one, orm_update, orm_get
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


@user_router.message()
async def echo(message: Message, session: AsyncSession, state: FSMContext):
    user_data = await orm_get_one(session=session, tablename='User', kwargs=({'tg_id': message.from_user.id}))
    if user_data.models is not None:
        model = await orm_get_one(session=session, tablename='Models', kwargs=({'id': user_data.models}))
        await state.set_state(Load.load)
        try:
            typing_task = asyncio.create_task(send_typing_action(message.chat.id))
            data = {"url": None}

            text = str(message.text)
            entities = message.entities

            content_data = {
                'text': text,
                'url': None
            }

            if entities:
                for item in entities:
                    if item.type in data.keys():
                        data[item.type] = item.extract_from(text)
                        text = text.replace(html.quote(data['url']), '')

                        if 'pdf' in html.quote(data['url']):
                            content_data = {
                                'text': text,
                                'url': html.quote(data['url'])
                            }

            answer_mistral = await api_get(
                api_key=os.getenv('Mistral_API'),
                model=model.name,
                content=content_data)

            await orm_add(
                session=session, tablename='Requests',
                data=({
                    'tg_id': message.from_user.id,
                    'answer': (f'Mistral_AI:\n{answer_mistral}\n\n'),
                    'request': str(content_data['text']),
                    'url': str(content_data['url'])
                }))
            for x in range(0, len(answer_mistral), 4096):
                txt = answer_mistral[x: x + 4096]
                await message.answer(txt, parse_mode='MarkdownV2')
        except Exception as ex:
            await bot.send_message(
                chat_id=int(ADMIN),
                text=f'Ошибка по запросу: {message.text}\n'
                f'Пользователь: @{message.from_user.username}\n'
                f'Текст ошибки: {str(ex)}')
            await message.answer('Ошибка на сервере, попробуйте позже...')
        finally:
            typing_task.cancel()
            await state.clear()
    else:
        await message.answer('Выбири модель для продолжения...')
        await change_model(message)
