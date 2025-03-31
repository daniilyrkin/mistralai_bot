from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder


class Keyboards_all:

    async def start_key():
        keyboard = ReplyKeyboardBuilder()
        keyboard.button(text="Код")
        keyboard.button(text="Текстовые запросы")
        return keyboard.as_markup(
            resize_keyboard=True,
            input_field_placeholder="Выбери")

    async def reply_key_builder(data):
        keyboard = ReplyKeyboardBuilder()
        if isinstance(data, list):
            for item in data:
                keyboard.button(text=item)
        else:
            keyboard.button(text=data)
        keyboard.adjust(2)
        return keyboard.as_markup(
            resize_keyboard=True)

    async def inline_key_builder(data_dict: dict):
        keyboard = InlineKeyboardBuilder()
        for name, data in data_dict.items():
            keyboard.button(text=name, callback_data=data)
        keyboard.adjust(2)
        return keyboard.as_markup(
            resize_keyboard=True)
