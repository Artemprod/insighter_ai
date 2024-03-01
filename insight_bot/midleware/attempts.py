from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from DB.Mongo.mongo_db import MongoUserRepoORM, UserBalanceRepoORM
from keyboards.inline_keyboards import crete_inline_keyboard_payed
from lexicon.LEXICON_RU import TIME_ERROR_MESSAGE_MIDDLEWARE


class CheckAttemptsMiddleware(BaseMiddleware):
    def __init__(self, user_repository: MongoUserRepoORM,
                 balance_repo: UserBalanceRepoORM):
        super().__init__()
        self.balance_repo = balance_repo
        self.user_repository = user_repository

    async def __call__(self, handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]], event: TelegramObject,
                       data: Dict[str, Any]) -> Any:
        user_id, chat_id, message = None, None, None
        callback_data = None

        # Определение типа события (сообщение или callback_query) и идентификаторов
        if hasattr(event, 'message') and event.message and not event.callback_query:
            chat_id = event.message.chat.id
            user_id = event.message.from_user.id
            message = event.message

        elif hasattr(event, 'callback_query') and event.callback_query and not event.message:
            chat_id = event.callback_query.message.chat.id
            user_id = event.callback_query.from_user.id
            message = event.callback_query.message
            callback_data = event.callback_query.data

        if not await self.user_repository.check_user_in_db(tg_id=user_id):
            return await handler(event, data)

        # Временной баланс пользователя
        time_left = await self.balance_repo.get_user_time_balance(tg_id=user_id)

        if time_left <= 0 and callback_data and 'gen_answer' in callback_data:
            # Сообщение об оплате и кнопки при нулевом балансе
            keyboard = crete_inline_keyboard_payed()  # Предполагаем, что функция создает инлайн-клавиатуру
            await message.bot.send_message(chat_id, text=TIME_ERROR_MESSAGE_MIDDLEWARE)
            await message.answer_contact(phone_number="+79896186869", first_name="Александр",
                                         last_name="Чернышов", reply_markup=keyboard)
        else:
            return await handler(event, data)


