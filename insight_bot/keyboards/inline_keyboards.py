from aiogram.utils.keyboard import InlineKeyboardBuilder

from DB.Mongo.mongo_db import MongoAssistantRepositoryORM
from DB.Mongo.mongo_enteties import Assistant
from insiht_bot_container import document_repository
from keyboards.calback_factories import AssistantCallbackFactory, DocumentsCallbackFactory


def crete_inline_keyboard_assistants(assistant_repository: MongoAssistantRepositoryORM,
                                     user_tg_id):

    assistants_list: Assistant = assistant_repository.get_all_assistants()
    kp_builder: InlineKeyboardBuilder = InlineKeyboardBuilder()
    for assistant in assistants_list:
        kp_builder.button(
            text=f'{assistant.button_name}',
            callback_data=AssistantCallbackFactory(
                assistant_id=assistant.assistant_id
            ).pack()
        )

    if document_repository.check_docs_in_user(user_tg_id):
        kp_builder.button(
            text='История запросов',
            callback_data='my_docs'
        )

    kp_builder.adjust(2)
    return kp_builder.as_markup()


def crete_inline_keyboard_payed():
    kp_builder: InlineKeyboardBuilder = InlineKeyboardBuilder()
    kp_builder.button(
        text='Оплатил',
        callback_data='payed'
    )
    kp_builder.adjust(1)
    return kp_builder.as_markup()


async def crete_inline_keyboard_show_docks(user_tg_id):
    documents = await document_repository.get_all_users_docs(tg_id=user_tg_id)

    kp_builder: InlineKeyboardBuilder = InlineKeyboardBuilder()
    for key, value in documents.items():
        kp_builder.button(
            text=f'{value.get("date")}',
            callback_data=DocumentsCallbackFactory(
                document_date=key
            ).pack()
        )

    kp_builder.button(
        text='Назад',
        callback_data='base'
    )

    kp_builder.adjust(1)
    return kp_builder.as_markup()


def crete_inline_keyboard_back_from_docks():
    kp_builder: InlineKeyboardBuilder = InlineKeyboardBuilder()

    kp_builder.button(
        text='Назад',
        callback_data='my_docs'
    )

    kp_builder.adjust(1)
    return kp_builder.as_markup()

def crete_inline_keyboard_back_from_loading():
    kp_builder: InlineKeyboardBuilder = InlineKeyboardBuilder()

    kp_builder.button(
        text='Назад',
        callback_data='base'
    )

    kp_builder.adjust(1)
    return kp_builder.as_markup()
