from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from DB.Mongo.mongo_db import MongoUserRepoORM, UserBalanceRepoORM
from keyboards.inline_keyboards import crete_inline_keyboard_payed
from lexicon.LEXICON_RU import LEXICON_COMMANDS


class CheckAttemptsMiddleware(BaseMiddleware):
    def __init__(self, user_repository: MongoUserRepoORM,
                 balance_repo: UserBalanceRepoORM):
        super().__init__()
        self.balance_repo = balance_repo
        self.user_repository = user_repository

    async def __call__(self, handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]], event: TelegramObject,
                       data: Dict[str, Any]) -> Any:

        user_id = None
        chat_id = None
        message = None
        print('CheckAttemptsMiddleware вызван')

        if event.message is not None and event.callback_query is None:

            chat_id = event.message.chat.id
            user_id = event.message.from_user.id
            message = event.message



        elif event.callback_query is not None and event.message is None:
            chat_id = event.callback_query.message.chat.id
            user_id = event.callback_query.from_user.id
            message = event.callback_query.message

            if event.callback_query.data == 'my_docs' or event.callback_query.data == 'base' or "show_docs" in event.callback_query.data:
                return await handler(event, data)

        # my_docs AssistantCallbackFactory

        if not await self.user_repository.check_user_in_db(tg_id=user_id):
            return await handler(event, data)

        # attempts = await self.user_repository.get_user_attempts(tg_id=user_id)
        time_left = await self.balance_repo.get_user_time_balance(tg_id=user_id)
        print(f"Минуты пользователя {user_id}: {time_left}")
        commands = LEXICON_COMMANDS.keys()
        if time_left <= 0 and message.text not in commands:
            keyboard = crete_inline_keyboard_payed()
            await message.bot.send_message(chat_id, "У тебя закончились Минуты. Чтобы получить напиши в личку")
            await message.answer_contact(phone_number="+79896186869", first_name="Александр",
                                         last_name="Чернышов", reply_markup=keyboard)

        else:
            return await handler(event, data)

    @staticmethod
    async def extract_prefix(data: str):
        parts = data.split(':')
        return parts[0] if parts else None
