import asyncio
import logging
from openai import AsyncOpenAI


import openai

from costume_excepyions.ai_exceptions import EmptyResponseArrayError
from main_process.ChatGPT.gpt_message import GPTMessage
from main_process.ChatGPT.gpt_options import GPTOptions


class GPTClient:
    def __init__(self, *,
                 options: GPTOptions):
        self.__model_name = options.model_name
        self.__max_message_count = options.max_message_count
        self.__max_tokens = options.max_token_count
        self.__temperature = options.temperature
        self.__max_return_tokens = options.max_return_tokens

        openai.api_key = options.api_key
        self.client = AsyncOpenAI()
        self.__lock = asyncio.Lock()



    async def complete(self, messages: list[GPTMessage],
                       system_message: GPTMessage,
                       ) -> str:
        if self.__max_message_count is None:
            msg_list = [
                system_message] if system_message else [] + messages  # [GPTMessage(content="Ты писатель",role='system')] else [GPTMessage(content="Напиши историю", role='user')]
        elif len(messages) > self.__max_message_count:
            msg_list = ([system_message] if system_message else []) + messages[-self.__max_message_count:]
        else:
            msg_list = ([system_message] if system_message else []) + messages

        gpt_args = {
            'model':
                self.__model_name,
            'messages': [{
                'role': message.role,
                'content': message.content}
                for message in msg_list],
            'temperature': self.__temperature,
            'max_tokens': self.__max_return_tokens
        }
        print('gpt args:', gpt_args)
        print('msg list', msg_list)
        logging.info('gpt args:', gpt_args)
        logging.info('msg list', msg_list)

        response = await self.__request(gpt_args)
        return response

    async def __request(self, gpt_args: dict) -> str:
        task = self.client.chat.completions.create(**gpt_args)



        if task is None:
            raise ValueError("Task is None!")

        response = await asyncio.create_task(task)

        if response.choices:
            response_choice = response.choices[0]  # Получаем первый диалоговый выбор.
            response_message = response_choice.message  # Извлекаем сообщение из выбранного диалога.
            response_text = response_message.content  # Поле 'content' содержит текст ответа.
            logging.info('response_text:', response_text)
        else:
            # Обработка случая, когда список 'choices' пуст.
            logging.exception('No choices returned in the response.')
            raise EmptyResponseArrayError('No choices returned in the response.')
        return response_text
