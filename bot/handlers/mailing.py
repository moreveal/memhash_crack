from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

class MailingState(StatesGroup):
    message = State()
