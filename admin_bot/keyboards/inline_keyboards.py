from aiogram.utils.keyboard import InlineKeyboardBuilder

from DB.Mongo.mongo_db import MongoAssistantRepositoryORM
from DB.Mongo.mongo_enteties import Assistant
from keyboards.callback_fabric import AssistantRedactCallbackFactory, AssistantDeleteCallbackFactory, \
    AssistantRedactOptionCallbackFactory
from keyboards.callback_fabric import AssistantCallbackFactory


def crete_inline_keyboard_all_assistants(assistant_repository: MongoAssistantRepositoryORM):
    assistants_list: Assistant = assistant_repository.get_all_assistants()
    kp_builder: InlineKeyboardBuilder = InlineKeyboardBuilder()
    for assistant in assistants_list:
        kp_builder.button(
            text=f'{assistant.button_name}',
            callback_data=AssistantCallbackFactory(
                assistant=assistant.assistant
            ).pack()
        )

    kp_builder.adjust(2)
    return kp_builder.as_markup()




def crete_inline_keyboard_options():
    kp_builder: InlineKeyboardBuilder = InlineKeyboardBuilder()
    kp_builder.button(
        text='Показать всех ассистентов',
        callback_data='show_all'
    )
    kp_builder.button(
        text='Создать нового ассистента',
        callback_data='create_new'
    )

    kp_builder.adjust(1)
    return kp_builder.as_markup()


def crete_inline_keyboard_assistants_actions(assistant: Assistant):
    kp_builder: InlineKeyboardBuilder = InlineKeyboardBuilder()
    kp_builder.button(
        text='Редактировать ассистента',
        callback_data=AssistantRedactCallbackFactory(
            assistant_id=assistant.assistant_id,
        ).pack()
    )
    kp_builder.button(
        text='Удалить ассистента',
        callback_data=AssistantDeleteCallbackFactory(
            assistant_id=assistant.assistant_id,

        ).pack()
    )
    kp_builder.button(
        text='Создать нового ассистента',
        callback_data='create_new'
    )
    kp_builder.adjust(2)
    return kp_builder.as_markup()


def crete_inline_keyboard_redact_actions(assistant_repository: MongoAssistantRepositoryORM, assistant_id: str):
    assistant: Assistant = assistant_repository.get_one_assistant(assistant_id=assistant_id)
    assistant_fields = [field_name for field_name in assistant._fields_ordered if
                        field_name != "id"
                        and field_name != "created_at"
                        and field_name != "assistant_id"
                        and field_name != "button_name"
                        and field_name != "assistant"]
    print()
    fil_dic = {
        "name": "Заголовок",
        "assistant_prompt": "Системный промпт",
        "user_prompt": "Рабочий промпт",
        "user_prompt_for_chunks": "Промпт для кусков",
    }

    kp_builder: InlineKeyboardBuilder = InlineKeyboardBuilder()
    for field_name in assistant_fields:
        kp_builder.button(
            text=f'{fil_dic[field_name]}',
            callback_data=AssistantRedactOptionCallbackFactory(
                assistant_id=assistant_id,
                assistant_field=field_name,
            ).pack()
        )

    kp_builder.adjust(2)
    return kp_builder.as_markup()


