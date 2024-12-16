from aiogram.filters import Filter
from aiogram.types import Message

from handlers.database import Database

class AdminFilter(Filter):
    def __init__(self) -> None:
        pass

    async def __call__(self, message: Message) -> bool:
        database = Database()
        return await database.is_user_admin(message.from_user.id)
