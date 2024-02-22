import datetime
import os

from aiogram import Router, Bot, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.types import ContentType
from api.progress_bar.command import ProgressBarClient
from DB.Mongo.mongo_db import MongoAssistantRepositoryORM, MongoUserRepoORM, UserDocsRepoORM, UserBalanceRepoORM
from api.gpt import GPTAPIrequest

from keyboards.calback_factories import AssistantCallbackFactory
from keyboards.inline_keyboards import crete_inline_keyboard_assistants, \
    crete_inline_keyboard_back_from_loading, crete_inline_keyboard_payed
from lexicon.LEXICON_RU import LEXICON_RU

from main_process.process_pipline import PipelineQueues, PipelineData
from services.service_functions import load_assistant, \
    generate_text_file, estimate_gen_summary_duration, \
    from_pipeline_data_object, estimate_media_duration_in_minutes, compare_user_minutes_and_file, seconds_to_min_sec
from states.summary_from_audio import FSMSummaryFromAudioScenario

# Повесить мидлварь только на этот роутер
router = Router()


@router.callback_query(AssistantCallbackFactory.filter())
async def processed_gen_answer(callback: CallbackQuery,
                               callback_data: AssistantCallbackFactory,
                               state: FSMContext,
                               assistant_repository: MongoAssistantRepositoryORM,
                               user_repository: MongoUserRepoORM,
                               ):
    # Проверяем, есть ли текст в сообщении
    if callback.message.text:
        message = await callback.message.edit_text(
            text=LEXICON_RU.get('instructions', 'как дела ?'),
            reply_markup=crete_inline_keyboard_back_from_loading())

    else:
        message = await callback.message.answer(
            text=LEXICON_RU.get('instructions', 'как дела ?'),
            reply_markup=crete_inline_keyboard_back_from_loading())
    # записываем имя асистента пользователью
    assistant_name = await assistant_repository.get_assistant_name(assistant_id=callback_data.assistant_id)
    await user_repository.add_assistant_call_to_user(user_tg_id=callback.from_user.id, assistant_name=assistant_name)
    await state.update_data(assistant_id=callback_data.assistant_id,
                            instruction_message_id=message.message_id)
    await state.set_state(FSMSummaryFromAudioScenario.load_file)
    await callback.answer()


@router.message(FSMSummaryFromAudioScenario.load_file, ~F.content_type.in_({ContentType.VOICE,
                                                                            ContentType.AUDIO,
                                                                            ContentType.VIDEO,
                                                                            ContentType.DOCUMENT
                                                                            }))
async def wrong_file_format(message: Message,
                            bot: Bot):
    await bot.delete_message(chat_id=message.chat.id,
                             message_id=message.message_id)

    await bot.send_message(chat_id=message.chat.id,
                           text=LEXICON_RU['wrong_format'].format(income_file_format=message.content_type,
                                                                  actual_formats=LEXICON_RU['actual_formats']))


@router.message(FSMSummaryFromAudioScenario.load_file, F.content_type.in_({ContentType.VOICE,
                                                                           ContentType.AUDIO,
                                                                           ContentType.VIDEO,
                                                                           ContentType.DOCUMENT

                                                                           }))
async def processed_load_file(message: Message, bot: Bot,
                              state: FSMContext, assistant_repository: MongoAssistantRepositoryORM,
                              user_repository: MongoUserRepoORM,
                              progress_bar: ProgressBarClient,
                              process_queue: PipelineQueues,
                              user_balance_repo: UserBalanceRepoORM
                              ):
    data = await state.get_data()
    assistant_id = data.get('assistant_id')
    instruction_message_id = int(data.get('instruction_message_id'))

    file_duration = await estimate_media_duration_in_minutes(bot=bot, message=message)
    #Проверяем есть ли минуты
    checking = await compare_user_minutes_and_file(user_tg_id=message.from_user.id, file_duration=file_duration,
                                                   user_balance_repo=user_balance_repo)
    print(checking)
    if checking >= 0:
        # await check_if_i_can_load()
        if instruction_message_id:
            await bot.delete_message(chat_id=message.chat.id,
                                     message_id=instruction_message_id)

        # Form data to summary pipline
        pipline_object = await from_pipeline_data_object(message=message,
                                                         bot=bot,
                                                         assistant_id=assistant_id,
                                                         fsm_state=state,
                                                         file_duration=file_duration,
                                                         additional_system_information=None,
                                                         additional_user_information=None)

        # Start pipline process
        await process_queue.income_items_queue.put(pipline_object)
        await state.set_state(FSMSummaryFromAudioScenario.get_result)
        # Переход в новый стату вызов функции явно
        await processed_do_ai_conversation(message=message, state=state,
                                           user_repository=user_repository, bot=bot,
                                           assistant_repository=assistant_repository,
                                           progress_bar=progress_bar,
                                           process_queue=process_queue,
                                           user_balance_repo=user_balance_repo
                                           )
    else:
        с = await seconds_to_min_sec(abs(checking))
        print(с)
        keyboard = crete_inline_keyboard_payed()
        await message.bot.send_message(message.chat.id,
                                       f"Не хватает {await seconds_to_min_sec(abs(checking))} минут для самари. Чтобы пополнить напиши в личку "
                                       f"или оплати в раздели тарифы /tariff")
        await message.answer_contact(phone_number="+79896186869", first_name="Александр",
                                     last_name="Чернышов", reply_markup=keyboard)
        print()


@router.message(FSMSummaryFromAudioScenario.get_result)
async def processed_do_ai_conversation(message: Message, bot: Bot,
                                       state: FSMContext,
                                       assistant_repository: MongoAssistantRepositoryORM,
                                       user_repository: MongoUserRepoORM,
                                       progress_bar: ProgressBarClient,
                                       process_queue: PipelineQueues,
                                       user_balance_repo: UserBalanceRepoORM
                                       ):
    transcribed_text_data: PipelineData = await process_queue.transcribed_text_sender_queue.get()
    if transcribed_text_data.transcribed_text:
        file_in_memory, file_name = await generate_text_file(content=transcribed_text_data.transcribed_text,
                                                             message_event=message)

        await bot.send_document(chat_id=transcribed_text_data.telegram_message.chat.id,
                                document=BufferedInputFile(file=file_in_memory,
                                                           filename=file_name),
                                caption=LEXICON_RU.get('transcribed_document_caption')
                                )
        await progress_bar.stop(chat_id=transcribed_text_data.telegram_message.from_user.id)
        process_queue.transcribed_text_sender_queue.task_done()
    predicted_duration_for_summary = await estimate_gen_summary_duration(text=transcribed_text_data.transcribed_text)
    await progress_bar.start(chat_id=transcribed_text_data.telegram_message.from_user.id,
                             time=predicted_duration_for_summary,
                             process_name="написание саммари")
    result: PipelineData = await process_queue.result_dispatching_queue.get()

    if result.summary_text:
        await progress_bar.stop(chat_id=result.telegram_message.from_user.id)
        await user_repository.delete_one_attempt(tg_id=result.telegram_message.from_user.id)
        await bot.send_message(chat_id=result.telegram_message.chat.id,
                               text=result.summary_text)

        await user_balance_repo.update_time_balance(tg_id=result.telegram_message.from_user.id,
                                                    time_to_subtract=result.file_duration
                                                    )

        time_left = await user_balance_repo.get_user_time_balance(tg_id=result.telegram_message.from_user.id)
        await bot.send_message(chat_id=result.telegram_message.chat.id,
                               text=f"<b>Осталось минут: {await seconds_to_min_sec(time_left)}</b>  \n\n {LEXICON_RU['next']}",
                               reply_markup=crete_inline_keyboard_assistants(assistant_repository,
                                                                             user_tg_id=result.telegram_message.from_user.id))

        await state.clear()
        process_queue.result_dispatching_queue.task_done()
