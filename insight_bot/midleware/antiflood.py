from aiogram import BaseMiddleware, types
from datetime import datetime, timedelta
from typing import Callable, Dict, Any, Awaitable


class AntiFloodMiddleware(BaseMiddleware):
    def __init__(self) -> None:
        # Использование словаря для хранения последнего времени действия для каждого чата
        self.last_action_time_per_chat: Dict[int, datetime] = {}

    async def __call__(
            self,
            handler: Callable[[types.TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: types.TelegramObject,
            data: Dict[str, Any]
    ) -> Any:

        # Определение chat_id из различных типов событий
        chat_id = message = None
        if hasattr(event, 'message'):
            chat_id = event.message.chat.id
        elif hasattr(event, 'callback_query') and event.callback_query:
            chat_id = event.callback_query.message.chat.id

        if chat_id is not None:
            current_time = datetime.now()
            last_action_time = self.last_action_time_per_chat.get(chat_id)

            # Проверка, не слишком ли часто совершается действие
            if last_action_time and (current_time - last_action_time) < timedelta(seconds=0.5):
                return

            # Обновление времени последнего действия
            self.last_action_time_per_chat[chat_id] = current_time
        return await handler(event, data)
