import asyncio
from abc import ABC, abstractmethod

import os
from functools import partial

import nltk
import tiktoken
from concurrent.futures import ProcessPoolExecutor

from langchain.chains import LLMChain, StuffDocumentsChain, ReduceDocumentsChain, MapReduceDocumentsChain
from langchain.text_splitter import RecursiveCharacterTextSplitter, NLTKTextSplitter
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

from DB.Mongo.mongo_db import MongoAssistantRepositoryORM
from DB.Mongo.mongo_enteties import Assistant
from costume_excepyions.ai_exceptions import CharactersInTokenMeasurement, GptApiRequestError, \
    LoadingLongRequestMethodError, LoadingShortRequestMethodError, CompileRequestError, GeneratingDataForModelError, \
    TokenCapacityMeasurement
from logging_module.log_config import insighter_logger

from main_process.ChatGPT.gpt_enteties import AssistantInWork
from main_process.ChatGPT.gpt_message import GPTMessage, GPTRole
from main_process.ChatGPT.gpt_models_information import GPTModelManager
from main_process.ChatGPT.gpt_options import GPTOptions
from main_process.ChatGPT.openai_chat_complain import GPTClient
from main_process.func_decorators import ameasure_time


class TextTokenizer:
    MODELS = {"gpt-3.5-turbo-0613",
              "gpt-3.5-turbo-16k-0613",
              "gpt-4-0314",
              "gpt-4-32k-0314",
              "gpt-4-0613",
              "gpt-4-32k-0613"}

    TOKENS_PER_MESSAGE_RU = 3

    @staticmethod
    def num_tokens_from_string(string: str, encoding_name: str = 'cl100k_base') -> int:
        """Returns the number of tokens in a text string."""
        try:
            encoding = tiktoken.get_encoding(encoding_name)
            num_tokens = len(encoding.encode(string))
            return num_tokens
        except Exception as e:
            insighter_logger.exception(e)

    def num_tokens_from_messages(self, messages, model="gpt-4-0314"):
        """Return the number of tokens used by a list of messages."""
        try:
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            insighter_logger.exception("Warning: model not found. Using cl100k_base encoding.")
            encoding = tiktoken.get_encoding("cl100k_base")
        if model in TextTokenizer.MODELS:
            tokens_per_message = TextTokenizer.TOKENS_PER_MESSAGE_RU
            tokens_per_name = 1
        elif model == "gpt-3.5-turbo-0301":
            tokens_per_message = TextTokenizer.TOKENS_PER_MESSAGE_RU + 1  # every message follows <|start|>{role/name}\n{content}<|end|>\n
            tokens_per_name = -1  # if there's a name, the role is omitted
        elif "gpt-3.5-turbo" in model:
            insighter_logger.info(
                "Warning: gpt-3.5-turbo may update over time. Returning num tokens assuming gpt-3.5-turbo-0613.")
            return self.num_tokens_from_messages(messages, model="gpt-3.5-turbo-0613")
        elif "gpt-4" in model:
            insighter_logger.info("Warning: gpt-4 may update over time. Returning num tokens assuming gpt-4-0613.")
            return self.num_tokens_from_messages(messages, model="gpt-4-0613")
        else:
            raise NotImplementedError(
                f"""num_tokens_from_messages() is not implemented for model {model}. See https://github.com/openai/openai-python/blob/main/chatml.md for information on how messages are converted to tokens."""
            )
        num_tokens = 0
        for message in messages:
            num_tokens += tokens_per_message
            for key, value in message.items():
                num_tokens += len(encoding.encode(value))
                if key == "name":
                    num_tokens += tokens_per_name
        num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
        return num_tokens

    @staticmethod
    def split_text_into_parts(string, max_tokens):
        encoding = tiktoken.get_encoding("cl100k_base")
        tokens = encoding.encode(string)
        token_parts = [tokens[i:i + max_tokens] for i in range(0, len(tokens), max_tokens)]
        parts = [encoding.decode(i) for i in token_parts]
        return parts

    async def measure_text_capacity(self, text: str) -> int:
        """
        Measure text tokens in text
        It seems to be computation work that should be run in PoolExecuter in a parent function
        :param text:
        :return:
        """
        loop = asyncio.get_running_loop()
        with ProcessPoolExecutor(max_workers=os.cpu_count()) as pool:
            try:
                text_size = await loop.run_in_executor(
                    pool, self.num_tokens_from_string, text
                )
                insighter_logger.info(f"Measure token capacity it equals {text_size}")
                return text_size
            except Exception as e:
                insighter_logger.exception("cant measure token capacity")
                raise TokenCapacityMeasurement(f"cant measure amount of token.\n An error {e} have came around")

    async def measure_characters_in_tokens(self,
                                           tokens_count: int) -> int:
        """
        Measure text tokens in text
        It seems to be computation work that should be run in PoolExecuter in a parent function
        :param tokens_count:
        :param text:
        :return:
        """
        loop = asyncio.get_running_loop()
        with ProcessPoolExecutor(max_workers=os.cpu_count()) as pool:
            try:
                characters = await loop.run_in_executor(
                    pool, self.tokens_to_characters_gpt4_russian, tokens_count
                )
                insighter_logger.info(f"characters in token {characters}")
                return characters
            except Exception as e:
                insighter_logger.exception("cant measure characters ")
                raise CharactersInTokenMeasurement(
                    f"cant measure amount of characters in tokens .\n An error {e} have came around")

    # TODO сделать динамическую подгрузку среднего кол-во символов в токене чстобы бы редактировать
    @staticmethod
    def tokens_to_characters_gpt4_russian(tokens_count: int,
                                          average_chars_per_token: float = 2) -> int:
        """
        Приблизительно переводит количество токенов в количество символов для русскоязычного текста в модели GPT-4.

        :param tokens_count: Количество токенов.
        :param average_chars_per_token: Среднее количество символов на один токен. Для GPT-4 и русского языка предполагаем среднее значение около 3.5.
        :return: Ориентировочное количество символов.
        """
        # Расчет количества символов, основанный на среднем значении символов на токен, умножаем количество токенов на среднее количество символов
        characters_count = int(tokens_count * average_chars_per_token)
        return characters_count


# TODO вынести в отдельный модуль потому что тут только диспечер
class RequestGPTWorker:
    def __init__(self,
                 assistant_repositorysitory: MongoAssistantRepositoryORM,
                 model_manager: GPTModelManager):
        self.__assistant_repositorysitory = assistant_repositorysitory
        self.model_manager = model_manager

    async def make_gpt_request(self, assistant_id,
                               income_text: str,
                               additional_system_information: str,
                               additional_user_information: str) -> str:
        raise NotImplementedError("Gpt request method not implemented")

    async def load_assistant(self,
                             assistant_id) -> Assistant:
        """
        Function loads asssistant prormts and used in call gpt request method
        :param assistant_id:
        :param user_id:
        :return: asssistant
        """
        assistant_prompt: Assistant = await self.__assistant_repositorysitory.get_one_assistant(
            assistant_id=assistant_id)
        return assistant_prompt

    async def load_gpt(self) -> GPTClient:
        options = await self.load_gpt_options()
        client = GPTClient(options=options)
        return client

    async def load_gpt_options(self) -> GPTOptions:
        # Выполняем асинхронные задачи параллельно и ждем их результатов
        api_key, model_version, model_max_size, model_context_length, model_temperature, max_return_tokens = await asyncio.gather(
            self.model_manager.get_gpt_api_key(),
            self.model_manager.get_current_gpt_model_in_use_from_env(),
            self.model_manager.get_current_gpt_model_max_size(),
            self.model_manager.get_current_context_length(),
            self.model_manager.get_gpt_model_tempreture(),
            self.model_manager.get_max_return_tokens()
        )

        # Создаем и возвращаем объект GPTOptions с полученными данными
        options = GPTOptions(
            api_key=api_key,
            model_name=model_version,
            max_message_count=model_context_length,
            max_token_count=model_max_size,
            temperature=model_temperature,
            max_return_tokens=max_return_tokens
        )
        return options

    async def generate_data(self,
                            assistant_id,
                            income_text,
                            additional_system_information,
                            additional_user_information):

        # Выполняем асинхронные задачи параллельно и ждем их результатов

        assistant = await self.load_assistant(assistant_id=assistant_id)
        system_massage, user_message = await asyncio.gather(
            self.create_one_system_message(system_prompt=assistant.assistant_prompt,
                                           additional_system_information=additional_system_information),
            self.create_one_user_message(user_prompt=assistant.user_prompt,
                                         income_text=income_text,
                                         additional_user_information=additional_user_information)

        )
        return system_massage, user_message

    async def create_one_system_message(self, system_prompt: str,
                                        additional_system_information: str) -> GPTMessage:

        prompt = await self.insert_additional_information_if_exists(prompt=system_prompt,
                                                                    information=additional_system_information)
        message = GPTMessage(role=GPTRole.SYSTEM, content=prompt)
        return message

    async def create_one_user_message(self, user_prompt: str,
                                      income_text: str,
                                      additional_user_information: str) -> GPTMessage:
        prompt = await self.insert_additional_information_if_exists(prompt=user_prompt,
                                                                    information=additional_user_information)
        message = GPTMessage(role=GPTRole.USER, content=f' {prompt}. Вот текст записи: -> "{income_text}" ')
        return message

    @staticmethod
    async def insert_additional_information_if_exists(prompt: str, information: str = None) -> str:
        if information and '{information}' in prompt:
            return prompt.format(information=information)
        else:
            return prompt


class OneRequestGPTWorker(RequestGPTWorker):

    async def make_gpt_request(self, assistant_id,
                               income_text: str,
                               additional_system_information: str = None,
                               additional_user_information: str = None) -> str:
        try:
            system_massage, user_message = await self.generate_data(assistant_id=assistant_id,
                                                                    income_text=income_text,
                                                                    additional_system_information=additional_system_information,
                                                                    additional_user_information=additional_user_information)
        except Exception as e:
            insighter_logger.exception("Failed to generate datda for for model")
            raise GeneratingDataForModelError("Failed to generate datda for for model", exception=e)

        gpt_client: GPTClient = await self.load_gpt()
        try:
            response = await gpt_client.complete(messages=[user_message],
                                                 system_message=system_massage,
                                                 )
            insighter_logger.info(f"successful gpt api request ")
            return response

        except Exception as e:
            insighter_logger.exception(f"Somthing went wrong with gpt api request. Error {e}")
            raise GptApiRequestError(f"Somthing went wrong with gpt api request. Error {e}",
                                     exception=e)


# noinspection PyCompatibility
class BigDataGPTWorker(RequestGPTWorker):

    def __init__(self, assistant_repositorysitory: MongoAssistantRepositoryORM,
                 model_manager: GPTModelManager,
                 tokenizer: TextTokenizer,
                 ):
        super().__init__(assistant_repositorysitory,
                         model_manager)
        self.__tokenizer = tokenizer
        self.__text_spliter = tokenizer

    async def __init_chunk_size(self):
        # TODO вынести все константы в конфиги JSON
        chunk_size_in_tokens = int(0.6 * await self.model_manager.get_current_gpt_model_max_size())
        chunk_size_in_characters = await self.__tokenizer.measure_characters_in_tokens(
            tokens_count=chunk_size_in_tokens)

        return chunk_size_in_characters

    async def __init_NLTK_text_spliter(self) -> NLTKTextSplitter:
        chunk_size = await self.__init_chunk_size()
        chunk_overlap = round(chunk_size * 0.3)
        try:
            nltk.data.find('tokenizers/punkt')
            print("nltk.download('punkt') уже установлен")
            text_spliter = NLTKTextSplitter(chunk_size=chunk_size,
                                            chunk_overlap=chunk_overlap)
            return text_spliter
        except LookupError as e:
            insighter_logger.exception(f'"nltk.download("punkt") is not  installed" exeption {e}')
            insighter_logger.info('start_downloading version nltk.download("popular")')
            nltk.download('popular')
            text_spliter = NLTKTextSplitter(chunk_size=chunk_size,
                                            chunk_overlap=chunk_overlap)
            return text_spliter

    async def __init_recursive_text_spliter(self) -> RecursiveCharacterTextSplitter:
        chunk_size = await self.__init_chunk_size()
        chunk_overlap = round(chunk_size * 0.15)
        return RecursiveCharacterTextSplitter(chunk_size=chunk_size,
                                              chunk_overlap=chunk_overlap)

    @staticmethod
    async def get_text_chunks_langchain(
            text):
        return [Document(page_content=text)]

    @ameasure_time
    async def make_gpt_request(
            self,
            assistant_id: str,
            income_text: str,
            additional_system_information: str = None,
            additional_user_information: str = None):
        assistant: AssistantInWork = await self.generate_data(assistant_id=assistant_id,
                                                              additional_system_information=additional_system_information,
                                                              additional_user_information=additional_user_information)
        task = asyncio.create_task(self.__make_long_text(
            string=income_text,
            assistant_in_work=assistant
        ))
        try:
            result = await task
            insighter_logger.info("Successfully genereate LLM answer from long text")
            return result
        except Exception as e:
            insighter_logger.exception(e)

    async def __init_model_parametrs(self):
        model = await self.model_manager.get_current_gpt_model_in_use_from_env()
        temperature = await self.model_manager.get_gpt_model_tempreture()
        return model, temperature

    async def __make_map_reduce(self, assistant_in_work):
        model, temperature = await self.__init_model_parametrs()
        llm = ChatOpenAI(temperature=temperature,
                         model_name=model)
        # Map
        map_template = f"""
                {assistant_in_work.system_prompt}
                {assistant_in_work.additional_system_information if assistant_in_work.additional_system_information else ""}
                {assistant_in_work.additional_user_information if assistant_in_work.additional_user_information else ""}
                {assistant_in_work.user_prompt_for_chunks}:
                ->{'{docs}'}
                ответ на русском :"""
        map_prompt = PromptTemplate.from_template(map_template)
        map_chain = LLMChain(llm=llm, prompt=map_prompt)
        # Reduce
        reduce_template = f""" 
                {assistant_in_work.system_prompt}
                {assistant_in_work.additional_system_information if assistant_in_work.additional_system_information else ""}
                {assistant_in_work.additional_user_information if assistant_in_work.additional_user_information else ""}
                {assistant_in_work.main_user_prompt}:
                ->{'{docs}'}
                ответ на русском:"""
        reduce_prompt = PromptTemplate.from_template(reduce_template)
        # Run chain
        reduce_chain = LLMChain(llm=llm, prompt=reduce_prompt)
        # Takes a list of documents, combines them into a single string, and passes this to an LLMChain
        combine_documents_chain = StuffDocumentsChain(
            llm_chain=reduce_chain, document_variable_name="docs"
        )
        # Combines and iteravely reduces the mapped documents
        reduce_documents_chain = ReduceDocumentsChain(
            # This is final chain that is called.
            combine_documents_chain=combine_documents_chain,
            # If documents exceed context for `StuffDocumentsChain`
            collapse_documents_chain=combine_documents_chain,
            # The maximum number of tokens to group documents into.
            token_max=await self.model_manager.get_current_gpt_model_max_size(),
        )

        # Combining documents by mapping a chain over them, then combining results
        map_reduce_chain = MapReduceDocumentsChain(
            # Map chain
            llm_chain=map_chain,
            # Reduce chain
            reduce_documents_chain=reduce_documents_chain,
            # The variable name in the llm_chain to put the documents in
            document_variable_name="docs",
            # Return the results of the map steps in the output
            return_intermediate_steps=False,
        )

        return map_reduce_chain

    async def split_text(self,
                         string):
        text_splitter = await self.__init_recursive_text_spliter()
        get_doc_chunks = await self.get_text_chunks_langchain(string)
        split_docs = text_splitter.split_documents(get_doc_chunks)
        return split_docs

    async def __make_long_text(self, string, assistant_in_work: AssistantInWork):
        split_docs_task = asyncio.create_task(self.split_text(string))
        map_reduce_chain_task = asyncio.create_task(self.__make_map_reduce(assistant_in_work=assistant_in_work))
        split_docs, map_reduce_chain = await asyncio.gather(split_docs_task, map_reduce_chain_task)
        loop = asyncio.get_running_loop()
        try:
            result = await loop.run_in_executor(
                None,  # Использует ThreadPoolExecutor по умолчанию
                partial(map_reduce_chain.run,
                        split_docs)
            )
            return result
        except Exception as e:
            insighter_logger.exception("Ошибка при выполнении __make_long_text:", exc_info=e)

    @ameasure_time
    async def generate_data(self,
                            assistant_id,
                            additional_system_information,
                            additional_user_information,
                            income_text=None) -> AssistantInWork:
        # Выполняем асинхронные задачи параллельно и ждем их результатов

        assistant: Assistant = await self.load_assistant(assistant_id=assistant_id)
        system_prompt = assistant.assistant_prompt
        user_prompt_for_chunks = assistant.user_prompt_for_chunks
        main_user_prompt = assistant.user_prompt

        return AssistantInWork(
            system_prompt=system_prompt,
            user_prompt_for_chunks=user_prompt_for_chunks,
            main_user_prompt=main_user_prompt,
            additional_system_information=additional_system_information,
            additional_user_information=additional_user_information,
        )


class IGPTDispatcher(ABC):
    @abstractmethod
    async def compile_request(self, *args, **kwargs):
        pass


# noinspection PyCompatibility
class GPTDispatcher(IGPTDispatcher):

    def __init__(self,
                 token_sizer: TextTokenizer,
                 model_manager: GPTModelManager,
                 one_request_gpt: OneRequestGPTWorker,
                 long_request_gpt: BigDataGPTWorker,
                 ):
        self.__token_sizer = token_sizer
        self.model_manager = model_manager
        self.__one_request_gpt = one_request_gpt
        self.__long_request_gpt = long_request_gpt

    async def compile_request(self, assistant_id,
                              income_text: str,
                              additional_system_information: str = None,
                              additional_user_information: str = None) -> str:
        """
        Run a request to chat GPT depending on text's token size
        if token capacity larger than GPT model maximum capacity ir uses long realization if less usual
        :param additional_user_information:
        :param additional_system_information:
        :param income_text:
        :param assistant_id:
        :param text:
        :return:
        """
        try:
            request_method = await self.__factory_method(income_text=income_text)
            result = await request_method.make_gpt_request(assistant_id=assistant_id,
                                                           income_text=income_text,
                                                           additional_system_information=additional_system_information,
                                                           additional_user_information=additional_user_information,
                                                           )
            insighter_logger.info("successful api request from dispatcher")
            return result
        except GptApiRequestError as e:
            insighter_logger.exception(f'Failed to make request, exception is: {e.exception}')
            raise CompileRequestError

    async def __factory_method(self, income_text: str):
        text_token_capacity = await self.__token_sizer.measure_text_capacity(text=income_text)
        model_size = await self.model_manager.get_current_gpt_model_max_size()
        # if token capacity of text greater or equal than model size. Use partial request
        if model_size - text_token_capacity <= 0:
            try:
                return self.__long_request_gpt
            except Exception as e:
                insighter_logger.exception("Failed to load long request method")
                raise LoadingLongRequestMethodError(message="Failed to load usual long request method", exception=e)
        # if token capacity of text less than model size. Usual Gpt api request
        else:
            try:
                return self.__one_request_gpt
            except Exception as e:
                insighter_logger.exception("Failed to load usual short request method")
                raise LoadingShortRequestMethodError(message="Failed to load usual short request method", exception=e)


class GPTDispatcherOnlyLonghain(IGPTDispatcher):
    def __init__(self,

                 long_request_gpt: BigDataGPTWorker,
                 ):

        self.__long_request_gpt = long_request_gpt

    async def compile_request(self, assistant_id,
                              income_text: str,
                              additional_system_information: str = None,
                              additional_user_information: str = None):
        """
        Run a request to chat GPT depending on text's token size
        if token capacity larger than GPT model maximum capacity ir uses long realization if less usual
        :param additional_user_information:
        :param additional_system_information:
        :param income_text:
        :param assistant_id:
        :param text:
        :return:
        """
        try:

            result = await self.__long_request_gpt.make_gpt_request(assistant_id=assistant_id,
                                                                    income_text=income_text,
                                                                    additional_system_information=additional_system_information,
                                                                    additional_user_information=additional_user_information,
                                                                    )
            insighter_logger.info("successful api request from dispatcher")
            return result
        except GptApiRequestError as e:
            insighter_logger.exception(f'Failed to make request, exception is: {e.exception}')
            raise CompileRequestError
