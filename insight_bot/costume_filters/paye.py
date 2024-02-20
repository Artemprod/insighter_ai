from typing import Union

from aiogram.filters import Filter, BaseFilter
from aiogram.types import Message, CallbackQuery


class TariffCommandFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        # Проверяем, что в сообщении есть текст и он начинается с команды /feedback
        return message.text and message.text.startswith('/tariff')
