from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message,  CallbackQuery

from DB.Mongo.mongo_db import MongoAssistantRepositoryORM
from DB.Mongo.mongo_enteties import Assistant
from keyboards.callback_fabric import AssistantRedactCallbackFactory, AssistantDeleteCallbackFactory, \
    AssistantRedactOptionCallbackFactory
from keyboards.inline_keyboards import crete_inline_keyboard_assistants_actions, \
    crete_inline_keyboard_redact_actions, crete_inline_keyboard_options

router = Router()


class FSMRedactAssistant(StatesGroup):
    take_new_value = State()


class FSMCreateNewAssistant(StatesGroup):
    assistant = State()
    name = State()
    button_name = State()
    assistant_prompt = State()
    user_prompt = State()
    user_prompt_for_chunks = State()


@router.callback_query(F.data == 'show_all')
async def processed_show_all_assistants(callback: CallbackQuery,
                                        assistant_repository: MongoAssistantRepositoryORM):
    await callback.answer()
    all_assistants = assistant_repository.get_all_assistants()
    for assistant in all_assistants:
        info = f'<b>Название: </b>\n<i>{assistant.name}</i>\n\n' \
               f'<b>Системный промпт ( инструкци ассистента):</b> \n<i>{assistant.assistant_prompt}</i>\n\n' \
               f'<b>Пользовательский промпт ( иснструкции для работы :</b>\n<i>{assistant.user_prompt}</i>\n\n' \
               f'<b>Пользовательский промпт для кусков (  :</b>\n<i>{assistant.user_prompt_for_chunks}</i>\n\n' \
               f'<b>Дата создания ассистента:</b>\n <i>{assistant.created_at}</i>\n'

        await callback.message.answer(text=info, reply_markup=crete_inline_keyboard_assistants_actions(assistant))


@router.callback_query(AssistantRedactCallbackFactory.filter())
async def processed_redact_assistant(callback: CallbackQuery,
                                     callback_data: AssistantRedactCallbackFactory,
                                     assistant_repository: MongoAssistantRepositoryORM
                                     ):
    await callback.answer()
    assistant_id = callback_data.assistant_id
    assistant = assistant_repository.get_one_assistant(assistant_id)
    info = f'<b>Название: </b>\n<i>{assistant.name}</i>\n\n' \
           f'<b>Системный промпт ( инструкци ассистента):</b> \n<i>{assistant.assistant_prompt}</i>\n\n' \
           f'<b>Пользовательский промпт ( иснструкции для работы :</b>\n<i>{assistant.user_prompt}</i>\n\n' \
           f'<b>Пользовательский промпт для кусков (  :</b>\n<i>{assistant.user_prompt_for_chunks}</i>\n\n'\
           f'<b>Дата создания ассистента:</b>\n <i>{assistant.created_at}</i>\n'
    keyboard = crete_inline_keyboard_redact_actions(assistant_repository, assistant_id=assistant_id)
    await callback.message.edit_text(text=info, reply_markup=keyboard)


@router.callback_query(AssistantRedactOptionCallbackFactory.filter())
async def processed_redact_assistant_field(callback: CallbackQuery,
                                           callback_data: AssistantRedactOptionCallbackFactory,
                                           state: FSMContext
                                           ):
    await callback.answer()
    fil_dic = {
        "name": "Заголовок",
        "assistant_prompt": "Системный промпт",
        "user_prompt": "Рабочий промпт",
        "user_prompt_for_chunks": "Рабочий промпт для кусков",
    }
    field = callback_data.assistant_field

    filed_name = fil_dic[field]
    await callback.message.edit_text(f'Введи новое {filed_name}')
    await state.update_data(assistant_field=field,
                            assistant_field_name=filed_name,
                            assistant_id=callback_data.assistant_id)
    await state.set_state(FSMRedactAssistant.take_new_value)


@router.message(FSMRedactAssistant.take_new_value)
async def processed_take_new_value(message: Message,

                                   assistant_repository: MongoAssistantRepositoryORM,
                                   state: FSMContext):
    data = await state.get_data()
    field = data.get('assistant_field')
    filed_name = data.get('assistant_field_name')
    assistant_id = data.get('assistant_id')
    new_value = message.text
    assistant_repository.update_assistant_fild(assistant_id=assistant_id,
                                         assistant_fild=field,
                                         new_value=new_value)
    new_assistant = assistant_repository.get_one_assistant(assistant_id)
    info = f'<b>Название: </b>\n<i>{new_assistant.name}</i>\n\n' \
           f'<b>Системный промпт ( инструкци ассистента):</b> \n<i>{new_assistant.assistant_prompt}</i>\n\n' \
           f'<b>Пользовательский промпт ( иснструкции для работы :</b>\n<i>{new_assistant.user_prompt}</i>\n\n' \
           f'<b>Пользовательский промпт для кусков (  :</b>\n<i>{new_assistant.user_prompt_for_chunks}</i>\n\n'

    option_keyboard = crete_inline_keyboard_options()
    await message.answer(text=f'{filed_name} изменено:\n\n'
                              f'{info}', reply_markup=option_keyboard)
    await state.clear()


@router.callback_query(AssistantDeleteCallbackFactory.filter())
async def processed_delete_assistant(callback: CallbackQuery,
                                     callback_data: AssistantDeleteCallbackFactory,
                                     assistant_repository: MongoAssistantRepositoryORM,
                                     ):
    await callback.answer()
    asistent: Assistant = assistant_repository.get_one_assistant(assistant_id=callback_data.assistant_id)
    assistant_repository.delete_assistant(assistant_id=callback_data.assistant_id)
    keyboard = crete_inline_keyboard_options()
    await callback.message.edit_text(text=f"{asistent.name} Удалено",reply_markup=keyboard)


# ______________________________________________

@router.callback_query(F.data == 'create_new')
async def processed_create_new_enter_point(callback: CallbackQuery,
                                           state: FSMContext):
    await callback.message.answer('введи название на английском')
    await state.set_state(FSMCreateNewAssistant.assistant)


@router.message(FSMCreateNewAssistant.assistant)
async def processed_create_new_assistant_name_english(message: Message,
                                                      state: FSMContext):
    await message.answer('введи название ассистента')
    new_value = message.text
    await state.update_data(assistant=new_value)
    await state.set_state(FSMCreateNewAssistant.name)


@router.message(FSMCreateNewAssistant.name)
async def processed_create_new_assistant_name(message: Message,
                                              state: FSMContext):
    await message.answer('введи название которое будет отображаться на кнопке на русском ')
    new_value = message.text
    await state.update_data(name=new_value)
    await state.set_state(FSMCreateNewAssistant.button_name)


@router.message(FSMCreateNewAssistant.button_name)
async def processed_create_new_assistant_button_name(message: Message,
                                                     state: FSMContext):
    await message.answer('введи системный промпт ассистента ')
    new_value = message.text
    await state.update_data(button_name=new_value)
    await state.set_state(FSMCreateNewAssistant.assistant_prompt)


@router.message(FSMCreateNewAssistant.assistant_prompt)
async def processed_create_new_assistant_assistant_prompt(message: Message,
                                                          state: FSMContext):
    await message.answer('введи общий рабочий промпт ( работате на маленький текст и для общего саммари )  ')
    new_value = message.text
    await state.update_data(assistant_prompt=new_value)
    await state.set_state(FSMCreateNewAssistant.user_prompt)


@router.message(FSMCreateNewAssistant.user_prompt)
async def processed_create_new_assistant_user_prompt(message: Message,
                                                          state: FSMContext):
    await message.answer('введи рабочий промпт для кусков (это если текст большой саммари каждого куска )   ')
    new_value = message.text
    await state.update_data(user_prompt=new_value)
    await state.set_state(FSMCreateNewAssistant.user_prompt_for_chunks)

@router.message(FSMCreateNewAssistant.user_prompt_for_chunks)
async def processed_create_new_assistant_user_prompt_for_chunks(message: Message,
                                                     state: FSMContext,assistant_repository:MongoAssistantRepositoryORM):
    new_value = message.text
    await state.update_data(user_prompt_for_chunks=new_value)
    data = await state.get_data()
    new_assistant = Assistant(
        assistant=data.get('assistant', 'нету данных'),
        name=data.get('name', 'нету данных'),
        button_name=data.get('button_name', 'нету данных'),
        assistant_prompt=data.get('assistant_prompt', 'нету данных'),
        user_prompt=data.get('user_prompt', 'нету данных'),
        user_prompt_for_chunks=data.get('user_prompt_for_chunks', 'нету данных'),

    )
    save_id = assistant_repository.create_new_assistants(new_assistant)
    keyboard = crete_inline_keyboard_options()
    if save_id:
        new_assistant_get = assistant_repository.get_one_assistant(save_id)
        info = f'<b>Название: </b>\n<i>{new_assistant_get.name}</i>\n\n' \
               f'<b>Системный промпт ( инструкци ассистента):</b> \n<i>{new_assistant_get.assistant_prompt}</i>\n\n' \
               f'<b>Пользовательский промпт ( иснструкции для работы :</b>\n<i>{new_assistant_get.user_prompt}</i>\n\n'\
               f'<b>Пользовательский промпт для кусков (  :</b>\n<i>{new_assistant_get.user_prompt_for_chunks}</i>\n\n'

        await message.answer(text="новый асситет сохранен")
        await message.answer(text=f"<b>вот твой новый ассистент</b> \n\n"
                                  f"{info}",reply_markup=keyboard)

    else:
        await message.answer(text="что то пошло не так",reply_markup=keyboard)
    await state.clear()
