from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.types.input_file import FSInputFile, BufferedInputFile
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.fsm.context import FSMContext
from collections import deque
import json
import os
from dotenv import load_dotenv
from mistralai_bot.orm_query import orm_get
from mistralai_bot.keyboards.keyboards import Keyboards_all as keyboards
from mistralai_bot.utils.statistics_diogram import Diagram_creator
from aiogram.filters import CommandObject
from mistralai_bot.state.states import Sending_load
from mistralai_bot.config import bot

admin = Router()
load_dotenv()

ADMIN = int(os.getenv('ADMIN'))
admin.message.filter(F.chat.id.in_({ADMIN}))


@admin.message(Command('admin'))
async def admin_comands(message: Message):
    keyboard = await keyboards.reply_key_builder(
        ['/users', '/requests', '/logs', '/statistics month', '/statistics day', '/settings'])
    await message.answer('Получи свои права админа5', reply_markup=keyboard)


@admin.message(Command('users'))
async def users_list(message: Message, session: AsyncSession):
    text = ''
    for user in await orm_get(session=session, tablename='User'):
        if id:
            text += (
                f'ID: {user.tg_id}, Имя: @{user.username}\n'
                f'Модель: {user.models}\n')
        else:
            text = 'Пользователи не найдены'
    await message.answer(text)


"""@admin.message(Command('settings'))
async def settings_bot(message: Message, session: AsyncSession):
    keyboard = await keyboards.reply_key_builder(['/изменить_приветствие', '/посмотреть_приветствие '])
    await message.answer('Возможные настройки', reply_markup=keyboard)


@admin.message(Command('изменить_приветствие'))
async def change_greeting(message: Message, session: AsyncSession):
    model = callback.data.split('.')
    user_id = callback.from_user.id
    await orm_update(
        tablename='User', session=session,
        filter_arg={'tg_id': user_id},
        new_data={'models': model[1]})
    await callback.message.answer('Модель успешно выбрана!')"""


@admin.message(Command('sending'))
async def sending_message_(message: Message, session: AsyncSession, state: FSMContext):
    await state.set_state(Sending_load.load)
    await message.answer('Введи сообщение для рассылки')


@admin.message(Sending_load.load)
async def sending_message(message: Message, session: AsyncSession, state: FSMContext):
    i = 0
    err_user = ''
    for user in await orm_get(session=session, tablename='User'):
        try:
            if message.poll:
                ...
                """await bot.send_poll(
                    chat_id=ids,
                    question=message.poll.question,
                    options=[option.text for option in message.poll.options],
                    is_anonymous=message.poll.is_anonymous,
                    type=message.poll.type,
                    correct_option_id=message.poll.correct_option_id,
                    explanation=message.poll.explanation)
                await orm_add(
                    session=session,
                    tablename='Poll',
                    data=({
                        'question': str(message.poll.question),
                        'options': str([option.text for option in message.poll.options])
                    })
                )"""
            elif message.text:
                await bot.send_message(
                    chat_id=user.tg_id,
                    text=message.text
                )
            """for user in await orm_get(session=session, tablename='User'):
                if user.tg_id:
                    text += (
                        f'ID: {user.tg_id}, Имя: {user.username}\n'
                        f'Модель: {user.models}\n')
                else:
                    text = 'Пользователи не найдены'
            await callback.message.answer('Модель успешно выбрана!')"""
            i = i + 1
        except Exception as ex:
            err_user += f'\nЮзер: @{user.username}\nОшибка: {str(ex)}'

    await state.clear()
    await message.answer(
        f'Отправлено, кол-во получивших человек {i}\n'
        f'Пользователи с ошибкой: {err_user}')


@admin.message(Command('requests'))
async def get_requsts(message: Message, session: AsyncSession):
    data = []
    users = await orm_get(session=session, tablename='User')
    requests = await orm_get(session=session, tablename='Requests', desc_bool=True)
    requests_by_user = {}
    for req in requests:
        if req.tg_id not in requests_by_user:
            requests_by_user[req.tg_id] = []
        requests_by_user[req.tg_id].append({
            'Time': req.created.isoformat(),
            'Request': req.request,
            'Answer': req.answer,
            'Url': req.url,
            'file_id': req.file_id
        })
    for user in users:
        user_data = {
            'tg_id': user.tg_id,
            'Name': user.username,
            'Data': requests_by_user.get(user.tg_id, [])
        }
        data.append(user_data)
    with open('mistralai_bot/answer_bot.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    file = FSInputFile('mistralai_bot/answer_bot.json')
    await message.answer_document(file)
    os.remove("mistralai_bot/answer_bot.json")


@admin.message(Command('statistics'))
async def statistics(message: Message, session: AsyncSession, command: CommandObject):
    command_args: str = command.args
    data = await orm_get(session=session, tablename='Requests')
    if not data:
        await message.answer("Нет данных для отображения.")
        return

    plot_buf = Diagram_creator(data).plot_statistics(time=command_args)
    plot_input_file = BufferedInputFile(plot_buf.getvalue(), filename="statistics.png")
    await message.answer_photo(plot_input_file)


@admin.message(Command('logs'))
async def logs(message: Message):
    text = ''
    with open('mistralai_bot/bot.log', 'r') as file:
        lines = deque(file, maxlen=10)
        for line in lines:
            text += f'{line}\n'
    ss = FSInputFile("mistralai_bot/bot.log")
    await message.answer(text)
    await message.answer_document(ss)
