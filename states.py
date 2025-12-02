from aiogram.fsm.state import State, StatesGroup


class BotStates(StatesGroup):
    waiting_for_username = State()
