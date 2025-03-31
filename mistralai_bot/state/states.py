from aiogram.fsm.state import State, StatesGroup


class Load(StatesGroup):
    load = State()


class Sending_load(StatesGroup):
    load = State()
