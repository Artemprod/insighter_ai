from aiogram.filters import CommandStart, Command
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, WebAppInfo, InlineKeyboardButton, BotCommand
from DB.Mongo.mongo_db import MongoAssistantRepositoryORM, MongoUserRepoORM, UserBalanceRepoORM
from keyboards.inline_keyboards import crete_inline_keyboard_assistants, crete_inline_keyboard_back_from_loading

from lexicon.LEXICON_RU import LEXICON_RU

from services.service_functions import seconds_to_min_sec, generate_telegram_user_link

router = Router()


@router.message(CommandStart())
async def process_start_command(message: Message,
                                assistant_repository: MongoAssistantRepositoryORM,
                                user_repository: MongoUserRepoORM,
                                state: FSMContext,
                                user_balance_repo: UserBalanceRepoORM):
    await state.clear()
    if not await user_repository.check_user_in_db(tg_id=message.from_user.id):
        tg_link = await generate_telegram_user_link(username=message.from_user.username,
                                                    user_tg_id=message.from_user.id)
        await user_repository.save_new_user(
            tg_username=message.from_user.username,
            name=message.from_user.first_name,
            tg_id=message.from_user.id,
            tg_link=tg_link
        )
    time_left = await user_balance_repo.get_user_time_balance(tg_id=message.from_user.id)
    assistant_keyboard = crete_inline_keyboard_assistants(assistant_repository,
                                                          user_tg_id=message.from_user.id)

    await message.answer(
            text=f"{LEXICON_RU['description']}\n\n<b>Осталось минут: {await seconds_to_min_sec(time_left)}</b> \n\n{LEXICON_RU['next']} ",
            reply_markup=assistant_keyboard)




@router.message(Command(BotCommand(command="feedback", description="Оставить отзыв")))
async def feedback_handler(message: Message):
    # Создаем кнопку для Web App
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Открыть форму", web_app=WebAppInfo(url="https://tally.so/r/nPOeRd"))],
            [InlineKeyboardButton(text="Назад", callback_data='base')]  # Добавляем кнопку "Назад"
        ]
    )
    # Отправляем сообщение с кнопкой
    await message.answer("Чтобы оставить обратную связь или сообщить об ошибке, нажми кнопку ниже",
                         reply_markup=keyboard)


@router.message(Command(BotCommand(command="tariff", description="Информация о тарифах")))
async def tariff_handler(message: Message):
    # Создаем кнопку для Web App
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Посмотреть тарифы", web_app=WebAppInfo(url="https://insighter.io/tarifs"))],
            [InlineKeyboardButton(text="Назад", callback_data='base')]  # Добавляем кнопку "Назад"
        ]
    )
    # Отправляем сообщение с кнопкой
    await message.answer("Чтобы выбрать тариф, нажмите на кнопку ниже:", reply_markup=keyboard)


@router.message(Command(BotCommand(command="info", description="Информация о сервисе")))
async def info_handler(message: Message):
    # Создаем кнопку для Web App
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Читать", web_app=WebAppInfo(url="https://insighter.io/info"))],
            [InlineKeyboardButton(text="Назад", callback_data='base')]  # Добавляем кнопку "Назад"
        ]
    )
    # Отправляем сообщение с кнопкой
    await message.answer("В этом разделе мы собрали важную информацию о сервисе", reply_markup=keyboard)


@router.message(Command(BotCommand(command="pay", description="Информация о сервисе")))
async def pay_handler(message: Message):
    # Создаем кнопку для Web App
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Пополнить на сайте", web_app=WebAppInfo(url="https://insighter.io/tarifs"))],
            [InlineKeyboardButton(text="Пополнить в боте", callback_data='pay_in_bot')],
            [InlineKeyboardButton(text="Получить бесплатно", callback_data='referral_payment')],  # Добавляем кнопку "Назад"
            [InlineKeyboardButton(text="Назад", callback_data='base')]  # Добавляем кнопку "Назад"
        ]
    )
    # Отправляем сообщение с кнопкой
    await message.answer("Выбрать способ пополнения", reply_markup=keyboard)


@router.callback_query(F.data == "payed")
async def process_payed(callback: CallbackQuery, assistant_repository: MongoAssistantRepositoryORM,
                        user_repository: MongoUserRepoORM,
                        user_balance_repo: UserBalanceRepoORM):
    # attempts = await user_repository.get_user_attempts(tg_id=callback.from_user.id)
    time_left = await user_balance_repo.get_user_time_balance(tg_id=callback.from_user.id)
    assistant_keyboard = crete_inline_keyboard_assistants(assistant_repository, user_tg_id=callback.from_user.id)
    if callback.message.text:
        await callback.message.edit_text(
            text=f"<b>Осталось минут: {await seconds_to_min_sec(time_left)}</b>\n\n{LEXICON_RU['next']}",
            reply_markup=assistant_keyboard)
        await callback.answer()
    else:
        await callback.message.answer(
            text=f"<b>Осталось минут: {await seconds_to_min_sec(time_left)}</b>\n\n{LEXICON_RU['next']}",
            reply_markup=assistant_keyboard)
        await callback.answer()


@router.callback_query(F.data == "base")
async def process_payed(callback: CallbackQuery,
                        assistant_repository: MongoAssistantRepositoryORM,
                        user_repository: MongoUserRepoORM,
                        user_balance_repo: UserBalanceRepoORM):
    # attempts = await user_repository.get_user_attempts(tg_id=callback.from_user.id)
    time_left = await user_balance_repo.get_user_time_balance(tg_id=callback.from_user.id)
    assistant_keyboard = crete_inline_keyboard_assistants(assistant_repository, user_tg_id=callback.from_user.id)
    if callback.message.text:
        await callback.message.edit_text(
            text=f"<b>Осталось минут: {await seconds_to_min_sec(time_left)}</b>\n\n{LEXICON_RU['next']}",
            reply_markup=assistant_keyboard)
    else:
        await callback.message.answer(
            text=f"<b>Осталось минут:{await seconds_to_min_sec(time_left)}</b>\n\n{LEXICON_RU['next']}",
            reply_markup=assistant_keyboard)
