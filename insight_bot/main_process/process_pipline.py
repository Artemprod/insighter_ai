import asyncio
import logging
from asyncio import Queue
from typing import Optional

from aiofiles import os as asyncos
import aiogram
from dataclasses import dataclass
from DB.Mongo.mongo_db import UserDocsRepoORM
from api.progress_bar.command import ProgressBarClient
from config.bot_configs import Config
from costume_excepyions.format_exceptions import EncodingDetectionError, NotSupportedFormatError
from costume_excepyions.system_exceptions import SystemTypeError
from enteties.pipline_data import PipelineData
from lexicon.LEXICON_RU import LEXICON_RU

from main_process.ChatGPT.gpt_dispatcher import GPTDispatcher
from main_process.file_format_manager import FileFormatDefiner
from main_process.file_manager import TelegramMediaFileManager, ServerFileManager

from main_process.text_invoke import TextInvokeFactory
from services.service_functions import estimate_transcribe_duration
from states.summary_from_audio import FSMSummaryFromAudioScenario

from enteties.queue_entity import PipelineQueues


class ProcesQueuePipline:
    def __init__(self,
                 queue_pipeline: PipelineQueues,
                 database_document_repository: UserDocsRepoORM,
                 server_file_manager: TelegramMediaFileManager,
                 text_invoker: TextInvokeFactory,
                 format_definer: FileFormatDefiner,
                 progress_bar: ProgressBarClient,
                 ai_llm_request: GPTDispatcher,
                 config_data:Config):
        self.__database_document_repository = database_document_repository
        self.__server_file_manager = server_file_manager
        self.__text_invoker = text_invoker
        self.__ai_llm_request = ai_llm_request
        self.__queue_pipeline = queue_pipeline
        self.__format_definer = format_definer
        self.progress_bar = progress_bar
        self.__config_data = config_data

    async def file_path_producer(self,
                                 income_items_queue: asyncio.Queue,
                                 invoke_text_queue: asyncio.Queue):
        """
        Раздает пути. На вход получает запрос на выход отдает пути до фалов
        :param income_items_queue:
        :param invoke_text_queue:
        :return:
        """

        data: PipelineData = await income_items_queue.get()
        print('запуск в пайплане первый воркер', data)
        message: aiogram.types.Message = data.telegram_message
        bot: aiogram.Bot = data.telegram_bot
        # TODO Использую локальнубю систему сохранения файлов для сервера раскоменить
        system = self.__config_data .system.system_type
        print(system)
        if system == "docker":
            file_path_coro = self.__server_file_manager.get_media_file(message=message, bot=bot)
        elif system == "local":
            file_path_coro = ServerFileManager().get_media_file(message=message,
                                                                bot=bot)
        else:
            logging.error("Unknown system, add new system")
            raise SystemTypeError("Unknown system, add new system")

        begin_message = await data.telegram_bot.send_message(chat_id=data.telegram_message.chat.id,
                                                             text=f"Определяю формат файла...")
        try:
            file_path = await file_path_coro
            income_file_format = await self.__format_definer.define_format(file_path=file_path)
            if income_file_format in self.__text_invoker.formats.make_list_of_formats():
                data.file_path = file_path
                print(f"Производитель путей файлов: добавил {data}")
                # TODO Переделать логику пока грязно
                await bot.delete_message(message_id=begin_message.message_id, chat_id=begin_message.chat.id)
                progres_bar_duration = await estimate_transcribe_duration(message=message)
                if progres_bar_duration is not None:
                    await self.progress_bar.start(chat_id=message.from_user.id, time=progres_bar_duration,
                                                  process_name='распознавание файла ...')

                await invoke_text_queue.put(data)
                income_items_queue.task_done()
            else:
                await bot.delete_message(message_id=begin_message.message_id, chat_id=begin_message.chat.id)
                message = await data.telegram_bot.send_message(chat_id=data.telegram_message.chat.id,
                                                               text=LEXICON_RU['wrong_format'].format(
                                                                   income_file_format=income_file_format,
                                                                   actual_formats=LEXICON_RU['actual_formats'])
                                                               )
                await data.fsm_bot_state.update_data(instruction_message_id=message.message_id)
                await data.fsm_bot_state.set_state(FSMSummaryFromAudioScenario.load_file)
        except Exception as e:
            await data.telegram_bot.send_message(chat_id=data.telegram_message.chat.id,
                                                 text=LEXICON_RU['error_message'])
            logging.exception(e)
            raise e

    async def invoke_text(self,
                          invoke_text_queue: Queue,
                          gen_answer_queue: Queue,
                          transcribed_text_sender_queue: Queue):
        """
        получает на входт ссылку на файл в фаоловой системе на выходе текст. Передает словарь с данными о пользователе и тексте
        :param gen_answer_queue:
        :param transcribed_text_sender_queue:
        :param invoke_text_queue:
        :param preprocess_text_queue:
        :return:
        """
        while True:
            data: PipelineData = await invoke_text_queue.get()
            print(f"Получил данные для извлечения текста {data}")
            path_to_file = data.file_path
            print("Путь до файла", path_to_file)
            if path_to_file:
                invoked_text = None
                try:
                    invoked_text = await self.__text_invoker.invoke_text(path_to_file)
                except EncodingDetectionError as e:
                    logging.exception(e)
                if invoked_text:
                    data.transcribed_text = invoked_text
                    # TODO: Подумать как вынести ( тут зависимости от реализации )
                    try:
                        document_id: str = await self.__database_document_repository.create_new_doc(
                            tg_id=data.telegram_message.from_user.id)
                        # save document id in pipline_data
                        data.debase_document_id = document_id
                        await self.__database_document_repository.save_new_transcribed_text(
                            tg_id=data.telegram_message.chat.id,
                            doc_id=document_id,
                            transcribed_text=invoked_text)
                        # delete user uploaded file from server
                        await asyncos.remove(path_to_file)
                    except Exception as e:
                        logging.exception(e, "cant save recognized text in piplene ", self.__dict__)
                    finally:
                        print(f"Провел извлевчение {data}")
                        await gen_answer_queue.put(data)
                        await transcribed_text_sender_queue.put(data)
                        invoke_text_queue.task_done()
                else:
                    logging.error('No recognized text')
                    return None
            else:
                logging.exception(AttributeError, "No path to file")
                await data.telegram_bot.send_message(chat_id=data.telegram_message.chat.id,
                                                     text=LEXICON_RU['error_message'])
                logging.exception(AttributeError)
                raise AttributeError

    async def generate_summary_answer(self,
                                      gen_answer_queue: Queue,
                                      result_dispatching_queue: Queue):
        while True:
            data: PipelineData = await gen_answer_queue.get()
            print(f'Получил данные для генерации текста {data}')
            print(f'Вот препроцессинг текст {data.preprocessed_text}')
            # text_to_summary = data.preprocessed_text
            text_to_summary = data.transcribed_text
            if text_to_summary:
                summary = await self.__ai_llm_request.compile_request(
                    assistant_id=data.assistant_id,
                    income_text=text_to_summary,
                    additional_system_information=data.additional_system_information,
                    additional_user_information=data.additional_user_information,
                )
                if summary:
                    data.summary_text = summary
                    try:
                        # save summary into database
                        await self.__database_document_repository.save_new_summary_text(
                            tg_id=data.telegram_message.from_user.id,
                            doc_id=data.debase_document_id,
                            summary_text=summary)
                    except Exception as e:
                        logging.exception(e, "cant save summary text in database", self.__dict__)
                    finally:
                        await result_dispatching_queue.put(data)
                        gen_answer_queue.task_done()
                else:
                    logging.error("No summary")
                    return None

            else:
                logging.exception(AttributeError, "No text")
                await data.telegram_bot.send_message(chat_id=data.telegram_message.chat.id,
                                                     text=LEXICON_RU['error_message'])
                raise AttributeError


    @staticmethod
    def create_tasks(number_of_workers,
                     coro,
                     *args):
        tasks = []
        for _ in range(number_of_workers):
            task = asyncio.create_task(coro(*args))
            tasks.append(task)
        return tasks

    async def run_process(self):
        queue_pipeline = self.__queue_pipeline

        producer_tasks = self.create_tasks(10, self.file_path_producer,
                                           queue_pipeline.income_items_queue,
                                           queue_pipeline.text_invoke_queue)

        invoke_text_tasks = self.create_tasks(10, self.invoke_text,
                                              queue_pipeline.text_invoke_queue,
                                              queue_pipeline.text_gen_answer_queue,
                                              queue_pipeline.transcribed_text_sender_queue)

        gen_text_tasks = self.create_tasks(10, self.generate_summary_answer,
                                           queue_pipeline.text_gen_answer_queue,
                                           queue_pipeline.result_dispatching_queue)

        tasks = producer_tasks + invoke_text_tasks + gen_text_tasks

        try:
            await asyncio.gather(*tasks)

        except Exception as e:
            logging.info(e)
            logging.exception(e)
