from aiogram.filters import CommandStart, Command
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, WebAppInfo, InlineKeyboardButton

from DB.Mongo.mongo_db import MongoAssistantRepositoryORM, MongoUserRepoORM
from costume_filters.feedback import FeedbackCommandFilter

from keyboards.inline_keyboards import crete_inline_keyboard_assistants, crete_inline_keyboard_back_from_loading

from lexicon.LEXICON_RU import LEXICON_RU

router = Router()


@router.message(CommandStart())
async def process_start_command(message: Message,
                                assistant_repository: MongoAssistantRepositoryORM,
                                user_repository: MongoUserRepoORM,
                                state: FSMContext, ):
    await state.clear()
    if not await user_repository.check_user_in_db(tg_id=message.from_user.id):
        await user_repository.save_new_user(
            tg_username=message.from_user.username,
            name=message.from_user.first_name,
            tg_id=message.from_user.id,
        )
    attempts = await user_repository.get_user_attempts(tg_id=message.from_user.id)
    assistant_keyboard = crete_inline_keyboard_assistants(assistant_repository, user_tg_id=message.from_user.id)
    await message.answer(
        text=f"{LEXICON_RU['description']}\n\n <b>Осталось запросов: {attempts}</b> \n\n{LEXICON_RU['next']} ",
        reply_markup=assistant_keyboard)


@router.message(FeedbackCommandFilter())
async def feedback_handler(message: Message):
    # Создаем кнопку для Web App
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Открыть форму фидбека", web_app=WebAppInfo(url="https://tally.so/r/nPOeRd"))],
            [InlineKeyboardButton(text="Назад", callback_data='base')]  # Добавляем кнопку "Назад"
        ]
    )
    # Отправляем сообщение с кнопкой
    await message.answer("Чтобы оставить фидбек, нажмите на кнопку ниже:", reply_markup=keyboard)


# @router.message(Command(commands=['help']))
# async def process_start_command(message: Message, assistant_repository: MongoAssistantRepositoryORM,
#                                 user_repository: MongoUserRepoORM):
#     if message.text:
#         await message.edit_text(
#             text=LEXICON_RU.get('help', 'как дела ?'),
#             reply_markup=crete_inline_keyboard_assistants(assistant_repository, user_tg_id=message.from_user.id))
#
#     else:
#         await message.answer(
#             text=LEXICON_RU.get('help', 'как дела ?'),
#             reply_markup=crete_inline_keyboard_assistants(assistant_repository, user_tg_id=message.from_user.id))

# @router.message(Command(commands=['feedback']))
# async def process_start_command(message: Message, assistant_repository: MongoAssistantRepositoryORM,
#                                 user_repository: MongoUserRepoORM):
#     if message.text:
#         await message.edit_text(
#             text=LEXICON_RU.get('help', 'как дела ?'),
#             reply_markup=crete_inline_keyboard_assistants(assistant_repository, user_tg_id=message.from_user.id))
#
#     else:
#         await message.answer(
#             text=LEXICON_RU.get('help', 'как дела ?'),
#             reply_markup=crete_inline_keyboard_assistants(assistant_repository, user_tg_id=message.from_user.id))

@router.callback_query(F.data == "payed")
async def process_payed(callback: CallbackQuery, assistant_repository: MongoAssistantRepositoryORM,
                        user_repository: MongoUserRepoORM):
    attempts = await user_repository.get_user_attempts(tg_id=callback.from_user.id)
    assistant_keyboard = crete_inline_keyboard_assistants(assistant_repository, user_tg_id=callback.from_user.id)
    if callback.message.text:
        await callback.message.edit_text(text=f"<b> Осталось запросов: {attempts}</b>  \n\n {LEXICON_RU['next']}",
                                         reply_markup=assistant_keyboard)
        await callback.answer()
    else:
        await callback.message.answer(text=f"<b>Осталось запросов: {attempts}</b>  \n\n {LEXICON_RU['next']}",
                                      reply_markup=assistant_keyboard)
        await callback.answer()


@router.callback_query(F.data == "base")
async def process_payed(callback: CallbackQuery, assistant_repository: MongoAssistantRepositoryORM,
                        user_repository: MongoUserRepoORM):
    attempts = await user_repository.get_user_attempts(tg_id=callback.from_user.id)
    assistant_keyboard = crete_inline_keyboard_assistants(assistant_repository, user_tg_id=callback.from_user.id)
    if callback.message.text:
        await callback.message.edit_text(text=f"<b>Осталось запросов: {attempts}</b>  \n\n {LEXICON_RU['next']}",
                                         reply_markup=assistant_keyboard)
    else:
        await callback.message.answer(text=f"<b>Осталось запросов:{attempts}</b>  \n\n {LEXICON_RU['next']}",
                                      reply_markup=assistant_keyboard)
