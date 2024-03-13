import logging

from environs import Env

from DB.Mongo.mongo_db import TransactionRepoORM, UserBalanceRepoORM, TariffRepoORM, MongoAssistantRepositoryORM

from keyboards.inline_keyboards import crete_inline_keyboard_assistants
from lexicon.LEXICON_RU import MESSAGES, TARIFFS, REFERRAL_MESSAGE, LEXICON_RU
from aiogram.enums import ContentType
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, PreCheckoutQuery, LabeledPrice, BotCommand, InlineKeyboardMarkup, \
    InlineKeyboardButton

from services.service_functions import seconds_to_min_sec

# Повесить мидлварь только на этот роутер
router = Router()
env: Env = Env()
env.read_env('.env')
PAYMENTS_PROVIDER_TOKEN = env('PAYMENTS_PROVIDER_TOKEN')

# Вход в состояне покупки
@router.callback_query(F.data == 'referral_payment')
async def referral_payment_command(callback: CallbackQuery,
                              bot: Bot,
                              tariff_repository: TariffRepoORM
                              ):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[

            [InlineKeyboardButton(text="Назад", callback_data='base')]  # Добавляем кнопку "Назад"

        ]
    )
    if callback.message.text:
        await callback.message.edit_text(
            text=REFERRAL_MESSAGE,
            reply_markup=keyboard)
    else:
        await callback.message.answer(
            text=REFERRAL_MESSAGE,
            reply_markup=keyboard)


@router.callback_query(F.data == 'pay_in_bot')
async def process_buy_command(callback: CallbackQuery,
                              bot: Bot,
                              tariff_repository: TariffRepoORM
                              ):
    tariffs = {
        TARIFFS['base']: await tariff_repository.get_base_tariff(),
        TARIFFS['standard']: await tariff_repository.get_standard_tariff(),
        TARIFFS['premium']: await tariff_repository.get_premium_tariff(),
    }

    if PAYMENTS_PROVIDER_TOKEN.split(':')[1] == 'TEST':
        await bot.send_message(callback.message.chat.id, MESSAGES['pre_buy_demo_alert'])

    await bot.send_invoice(callback.message.chat.id,
                           title=MESSAGES['base_title'],
                           description=MESSAGES['base'],
                           provider_token=PAYMENTS_PROVIDER_TOKEN,
                           currency='rub',
                           is_flexible=False,  # True если конечная цена зависит от способа доставки
                           prices=[LabeledPrice(label=tariffs['base'].label,
                                                amount=tariffs['base'].price * 100)],
                           start_parameter=MESSAGES['start_parameter'],
                           payload=TARIFFS['base']
                           )

    await bot.send_invoice(callback.message.chat.id,
                           title=MESSAGES['standard_title'],
                           description=MESSAGES['standard'],
                           provider_token=PAYMENTS_PROVIDER_TOKEN,
                           currency='rub',
                           is_flexible=False,  # True если конечная цена зависит от способа доставки
                           prices=[LabeledPrice(label=tariffs['standard'].label,
                                                amount=tariffs['standard'].price * 100)],
                           start_parameter=MESSAGES['start_parameter'],
                           payload=TARIFFS['standard']
                           )
    await bot.send_invoice(callback.message.chat.id,
                           title=MESSAGES['premium_title'],
                           description=MESSAGES['premium'],
                           provider_token=PAYMENTS_PROVIDER_TOKEN,
                           currency='rub',
                           is_flexible=False,  # True если конечная цена зависит от способа доставки
                           prices=[LabeledPrice(label=tariffs['premium'].label,
                                                amount=tariffs['premium'].price * 100)],
                           start_parameter=MESSAGES['start_parameter'],
                           payload=TARIFFS['premium']
                           )





@router.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout_query: PreCheckoutQuery, bot: Bot):
    # TODO обработка неудачного платежа нужна
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=False, error_message="Платеж не прошел")


@router.message(F.content_type == ContentType.SUCCESSFUL_PAYMENT)
async def process_successful_payment(message: Message,
                                     bot: Bot,
                                     transaction_repository: TransactionRepoORM,
                                     user_balance_repo: UserBalanceRepoORM,
                                     tariff_repository: TariffRepoORM,
                                     assistant_repository: MongoAssistantRepositoryORM):
    print('successful_payment:')
    successful_payment = message.successful_payment
    # Сохраняю трансакцию
    try:
        await transaction_repository.save_transaction(
            tg_user_id=message.from_user.id,
            name=message.from_user.full_name,
            amount=successful_payment.total_amount / 100,
            tariff=successful_payment.invoice_payload,
            status=True,
            currency=successful_payment.currency,
            invoice_payload=successful_payment.invoice_payload,
            provider_payment_charge_id=successful_payment.provider_payment_charge_id,
            telegram_payment_charge_id=successful_payment.telegram_payment_charge_id,
        )
    except Exception as e:
        insighter_logger.exception(f'Faild to ssave transaction sorry {e}')

    tariffs = {
        TARIFFS['base']: tariff_repository.get_base_tariff,
        TARIFFS['standard']: tariff_repository.get_standard_tariff,
        TARIFFS['premium']: tariff_repository.get_premium_tariff,
    }
    try:
        tariff = await tariffs[successful_payment.invoice_payload]()
        # начисляю минуты пользователю
        await user_balance_repo.add_user_time_balance(tg_id=message.from_user.id,
                                                      time=tariff.minutes * 60)
    except Exception as e:
        insighter_logger.exception(f'Failed to add minutes {e}')

    total_amount = message.successful_payment.total_amount // 100
    currency = message.successful_payment.currency
    time_left = await user_balance_repo.get_user_time_balance(tg_id=message.from_user.id)
    assistant_keyboard = crete_inline_keyboard_assistants(assistant_repository,
                                                          user_tg_id=message.from_user.id)

    await message.answer(
        text=f"<b>Осталось минут: {await seconds_to_min_sec(time_left)}</b>\n\n{LEXICON_RU['next']}",
        reply_markup=assistant_keyboard)
    # Убедитесь, что MESSAGES содержит правильный ключ и формат строки
    await bot.send_message(
        message.chat.id,
        MESSAGES['successful_payment'].format(
            total_amount=total_amount,
            currency=currency
        )
    )
