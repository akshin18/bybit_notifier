from aiogram.filters import BaseFilter
from aiogram.types import Message

from src.config import settings
from src.utils import get_user


class AdminFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return bool(await get_user(message.from_user.id) and message.from_user and message.from_user.id in settings.ADMIN_IDS)
