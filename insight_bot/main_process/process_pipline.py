import asyncio

import time
from asyncio import Queue


from aiofiles import os as asyncos
import aiogram

from DB.Mongo.mongo_db import UserDocsRepoORM
from api.progress_bar.command import ProgressBarClient
from config.bot_configs import Config


from enteties.pipline_data import PipelineData

from lexicon.LEXICON_RU import LEXICON_RU
from logging_module.log_config import insighter_logger

from main_process.ChatGPT.gpt_dispatcher import GPTDispatcher
from main_process.file_format_manager import FileFormatDefiner
from main_process.file_manager import TelegramMediaFileManager
from main_process.post_ptocessing import PostProcessor

from main_process.text_invoke import TextInvokeFactory
from services.service_functions import estimate_transcribe_duration
from states.summary_from_audio import FSMSummaryFromAudioScenario

from enteties.queue_entity import PipelineQueues


#TODO Разнести логику пайплана и чат бота
class ProcesQueuePipline:
    def __init__(self,
                 queue_pipeline: PipelineQueues,
                 database_document_repository: UserDocsRepoORM,
                 server_file_manager: TelegramMediaFileManager,
                 text_invoker: TextInvokeFactory,
                 post_processor: PostProcessor,
                 format_definer: FileFormatDefiner,
                 progress_bar: ProgressBarClient,
                 ai_llm_request: GPTDispatcher,
                 config_data: Config):
        self.__database_document_repository = database_document_repository
        self.__server_file_manager = server_file_manager
        self.__text_invoker = text_invoker
        self.__post_processor = post_processor
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
        data.process_time.setdefault('produce_file_path', dict())
        data.process_time['produce_file_path']['start_time'] = time.time()
        insighter_logger.info('запуск в пайплане первый воркер', data)
        message: aiogram.types.Message = data.telegram_message

        try:
            progres_bar_duration = await estimate_transcribe_duration(message=message)
            if progres_bar_duration is not None:
                await self.progress_bar.start(chat_id=message.from_user.id, time=progres_bar_duration,
                                              process_name='распознавание файла ...')

            await invoke_text_queue.put(data)
            income_items_queue.task_done()
            document_id: str = await self.__database_document_repository.create_new_doc(
                tg_id=data.telegram_message.from_user.id)
            # save document id in pipline_data
            data.debase_document_id = document_id
            data.process_time['produce_file_path']['finished_time'] = time.time()
            data.process_time['produce_file_path']['total_time'] = \
                data.process_time['produce_file_path']['finished_time'] - \
                data.process_time['produce_file_path']['start_time']

        except Exception as e:
            await data.telegram_bot.send_message(chat_id=data.telegram_message.chat.id,
                                                 text=LEXICON_RU['error_message'])
            insighter_logger.exception(e)


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
            data.process_time.setdefault('invoke_text', dict())
            data.process_time['invoke_text']['start_time'] = time.time()
            insighter_logger.info(f"Получил данные для извлечения текста {data}")
            path_to_file = data.file_path
            insighter_logger.info("Путь до файла", path_to_file)
            if path_to_file:
                invoked_text = None
                try:
                    invoked_text = await self.__text_invoker.invoke_text(path_to_file)
                except Exception as e:
                    insighter_logger.exception(e, "Cant invoke text", self.__dict__)
                    await data.fsm_bot_state.set_state(FSMSummaryFromAudioScenario.load_file)
                    await data.telegram_bot.send_message(chat_id=data.telegram_message.chat.id,
                                                         text=LEXICON_RU['error_message'])
                    insighter_logger.exception(e)
                if invoked_text:
                    post_processed_text = await self.__post_processor.remove_redundant_repeats(text=invoked_text)
                    data.transcribed_text = post_processed_text
                    # TODO: Подумать как вынести ( тут зависимости от реализации )
                    try:
                        document_id = data.debase_document_id
                        await self.__database_document_repository.save_new_transcribed_text(
                            tg_id=data.telegram_message.chat.id,
                            doc_id=document_id,
                            transcribed_text=invoked_text)
                        # delete user uploaded file from server
                        await asyncos.remove(path_to_file)
                    except Exception as e:
                        insighter_logger.exception(e, "cant save recognized text in piplene ", self.__dict__)
                        await data.fsm_bot_state.set_state(FSMSummaryFromAudioScenario.load_file)
                        await data.telegram_bot.send_message(chat_id=data.telegram_message.chat.id,
                                                             text=LEXICON_RU['error_message'])

                    finally:
                        insighter_logger.info(f"Провел извлевчение {data}")
                        await gen_answer_queue.put(data)
                        await transcribed_text_sender_queue.put(data)
                        invoke_text_queue.task_done()
                        data.process_time['invoke_text']['finished_time'] = time.time()
                        data.process_time['invoke_text']['total_time'] = \
                            data.process_time['invoke_text']['finished_time'] - \
                            data.process_time['invoke_text']['start_time']
                else:
                    insighter_logger.exception(AttributeError, 'No recognized text')
                    await data.fsm_bot_state.set_state(FSMSummaryFromAudioScenario.load_file)
                    await data.telegram_bot.send_message(chat_id=data.telegram_message.chat.id,
                                                         text=LEXICON_RU['error_message'])



            else:
                insighter_logger.exception(AttributeError, "No path to file")
                await data.fsm_bot_state.set_state(FSMSummaryFromAudioScenario.load_file)
                await data.telegram_bot.send_message(chat_id=data.telegram_message.chat.id,
                                                     text=LEXICON_RU['error_message'])



    async def generate_summary_answer(self,
                                      gen_answer_queue: Queue,
                                      result_dispatching_queue: Queue):
        while True:
            data: PipelineData = await gen_answer_queue.get()
            data.process_time.setdefault('generate_summary_answer', dict())
            data.process_time['generate_summary_answer']['start_time'] = time.time()
            insighter_logger.info(f'Получил данные для генерации текста {data}')
            insighter_logger.info(f'Вот препроцессинг текст {data.preprocessed_text}')
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
                        insighter_logger.exception(e, "cant save summary text in database", self.__dict__)
                    finally:
                        await result_dispatching_queue.put(data)
                        gen_answer_queue.task_done()
                        data.process_time['generate_summary_answer']['finished_time'] = time.time()
                        data.process_time['generate_summary_answer']['total_time'] = \
                        data.process_time['generate_summary_answer']['finished_time'] - \
                        data.process_time['generate_summary_answer']['start_time']
                else:
                    insighter_logger.exception(AttributeError, 'No summary')
                    await data.fsm_bot_state.set_state(FSMSummaryFromAudioScenario.load_file)
                    await data.telegram_bot.send_message(chat_id=data.telegram_message.chat.id,
                                                         text=LEXICON_RU['error_message'])



            else:
                insighter_logger.exception(AttributeError, "No text")
                await data.fsm_bot_state.set_state(FSMSummaryFromAudioScenario.load_file)
                await data.telegram_bot.send_message(chat_id=data.telegram_message.chat.id,
                                                     text=LEXICON_RU['error_message'])


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
            insighter_logger.info("async pipline process start")

        except Exception as e:
            insighter_logger.info(e)
            insighter_logger.exception(e)
