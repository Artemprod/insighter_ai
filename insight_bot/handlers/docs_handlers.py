from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, FSInputFile, CallbackQuery

from DB.Mongo.mongo_db import UserDocsRepoORM

from keyboards.calback_factories import DocumentsCallbackFactory
from keyboards.inline_keyboards import crete_inline_keyboard_show_docks, \
    crete_inline_keyboard_back_from_docks
from lexicon.LEXICON_RU import LEXICON_RU

router = Router()


class FSMGetMyDocs(StatesGroup):
    get_my_docks = State()
    show_doc = State()


@router.callback_query(F.data == 'my_docs')
async def processed_show_my_docks(callback: CallbackQuery,
                                  state: FSMContext
                                  ):
    keyboard = await crete_inline_keyboard_show_docks(user_tg_id=callback.from_user.id)
    if callback.message.text:
        await callback.message.edit_text(
            text=LEXICON_RU.get('documents_tittle', 'как дела ?'), reply_markup=keyboard)
        await callback.answer()
    else:
        await callback.message.answer(text=LEXICON_RU.get('documents_tittle', 'как дела ?'), reply_markup=keyboard)
        await callback.answer()


@router.callback_query(DocumentsCallbackFactory.filter())
async def processed_chose_dock(callback: CallbackQuery,
                               callback_data: DocumentsCallbackFactory,
                               state: FSMContext,
                               document_repository: UserDocsRepoORM

                               ):
    document = await document_repository.get_doc_by_date(tg_id=callback.from_user.id, date=callback_data.document_date)
    back_keyboard = crete_inline_keyboard_back_from_docks()
    msg = f"""
<b>Текст документа</b>\n\n
<b>Трансрибация</b> ( часть текста ):{document.get('transcription', 'Нету транскрипции')[:600]} <b>...</b>\n\n
<b>Саммари</b>: :{document.get('summary', 'Нету саммари')}
    """
    await callback.message.edit_text(
        text=f'{msg}', reply_markup=back_keyboard)
    await callback.answer()
