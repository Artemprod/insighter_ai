from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from DB.Mongo.mongo_db import MongoAssistantRepositoryORM
from DB.Mongo.mongo_enteties import Assistant
from insiht_bot_container import document_repository
from keyboards.calback_factories import AssistantCallbackFactory, DocumentsCallbackFactory

LEXICON_BUT = {'backward': '<<',
               'forward': '>>'}


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


async def create_inline_keyboard_show_docs(user_tg_id,
                                           docs_per_page=5,
                                           current_page=1):
    documents = await document_repository.get_all_users_docs(tg_id=user_tg_id)

    # Сортировка документов, если необходимо
    sorted_docs = sorted(documents.items(), key=lambda item: item[1].get("date", ""))

    # Расчет общего числа страниц
    total_pages = len(sorted_docs) // docs_per_page + (0 < len(sorted_docs) % docs_per_page)

    # Определение документов для текущей страницы
    page_docs = sorted_docs[(current_page - 1) * docs_per_page: current_page * docs_per_page]

    # Создание экземпляра строителя клавиатуры
    kp_builder = InlineKeyboardBuilder()
    doc_buttons: list[InlineKeyboardButton] = []
    # Добавление кнопок для документов текущей страницы
    for key, value in page_docs:
        doc_buttons.append(InlineKeyboardButton(
            text=f'{value.get("date")}',
            callback_data=DocumentsCallbackFactory(
                document_date=key
            ).pack())
        )
    kp_builder.row(*doc_buttons, width=1)

    if not len(sorted_docs) < docs_per_page:
        back_button = forward_button = InlineKeyboardButton(text="⏹️", callback_data="none")

        # Добавление навигационных кнопок
        if current_page > 1:
            back_button = InlineKeyboardButton(text="⬅️ Назад", callback_data=f"page_{current_page - 1}")
        # # Кнопка с номером страницы, не требующая callback_data для действия

        if current_page < total_pages:
            forward_button = InlineKeyboardButton(text="Вперед ➡️", callback_data=f"page_{current_page + 1}")
        current_page_info = InlineKeyboardButton(text=f"Стр. {current_page} из {total_pages}", callback_data=f"none")
        kp_builder.row(back_button, forward_button, width=2)
        kp_builder.row(current_page_info, width=1)

        back_button = InlineKeyboardButton(
            text='главное меню',
            callback_data='base'
        )
        kp_builder.row(back_button, width=1)
        return kp_builder.as_markup()
    else:
        back_button = InlineKeyboardButton(
            text='главное меню',
            callback_data='base'
        )
        kp_builder.row(back_button, width=1)
        return kp_builder.as_markup()


def crete_inline_keyboard_back_from_docks():
    kp_builder: InlineKeyboardBuilder = InlineKeyboardBuilder()

    kp_builder.button(
        text='Назад',
        callback_data='my_docs'
    )

    kp_builder.adjust(1)
    return kp_builder.as_markup()


def create_pagination_keyboard(*buttons: str) -> InlineKeyboardMarkup:
    # Инициализируем билдер
    kb_builder = InlineKeyboardBuilder()
    # Добавляем в билдер ряд с кнопками
    kb_builder.row(*[InlineKeyboardButton(
        text=LEXICON_BUT[button] if button in LEXICON_BUT else button,
        callback_data=button) for button in buttons]
                   )
    # Возвращаем объект инлайн-клавиатуры
    return kb_builder.as_markup()


def crete_inline_keyboard_back_from_loading():
    kp_builder: InlineKeyboardBuilder = InlineKeyboardBuilder()

    kp_builder.button(
        text='Назад',
        callback_data='base'
    )

    kp_builder.adjust(1)
    return kp_builder.as_markup()
