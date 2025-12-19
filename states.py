from aiogram.fsm.state import State, StatesGroup


class BotStates(StatesGroup):
    waiting_for_username = State()


class BroadcastStates(StatesGroup):
    """States for broadcast functionality."""
    waiting_for_message_type = State()
    waiting_for_text = State()
    waiting_for_photo = State()
    waiting_for_caption = State()
    confirm_broadcast = State()


class SettingsStates(StatesGroup):
    """States for system settings management."""
    waiting_for_reminder_interval = State()
    waiting_for_reminder_delay = State()
