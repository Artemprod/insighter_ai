import asyncio
import logging

from datetime import datetime
from typing import Callable

import tiktoken
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ContentType, Audio
from aiogram import Bot

from DB.Mongo.mongo_db import MongoAssistantRepositoryORM
from DB.Mongo.mongo_enteties import Assistant
from api.gpt import GPTAPIrequest
import os
from abc import ABC, abstractmethod

from enteties.pipline_data import PipelineData

import re
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer



class IMediaFileManager(ABC):

    async def get_media_file(self, *args, **kwargs) -> str:
        pass


def get_relative_path(path):
    """
  Возвращает относительный путь от корня до указанного пути.

  Args:
    path: Полный путь к файлу или каталогу.

  Returns:
    Относительный путь.
  """

    parts = path.split("/")
    return "/".join(parts[len(parts) - 1:])


async def get_media_file_path(user_media_dir: str, file_id: str, file_extension: str) -> str:
    os.makedirs(user_media_dir, exist_ok=True)
    return os.path.join(user_media_dir, f"{file_id}.{file_extension}")


async def download_media_file(bot: Bot, file_path: str, destination: str) -> str:
    await bot.download_file(file_path, destination=destination)
    return destination


async def remove_file_async(file_path):
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, os.remove, file_path)


def ensure_directory_exists(path):
    """
    Ensure that a directory exists, and create it if it doesn't.
    """
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)
        print(f"Каталог создан: {path}")
    else:
        print(f"Каталог уже существует: {path}")


async def load_assistant(state: FSMContext,
                         Gpt_assistant: GPTAPIrequest,
                         assistant_repository: MongoAssistantRepositoryORM) -> GPTAPIrequest:
    data = await state.get_data()
    assistant_id = data.get('assistant_id')
    asisitent_prompt: Assistant = await assistant_repository.get_one_assistant(assistant_id=assistant_id)
    Gpt_assistant.system_assistant = asisitent_prompt
    return Gpt_assistant


async def gen_doc_file_path(media_folder: str, sub_folder: str, message_event: Message) -> str:
    doc_directory = os.path.join(media_folder, sub_folder)
    doc_filename = f'{message_event.chat.id}_{datetime.now().strftime("%d_%B_%Y_%H_%M_%S")}.txt'
    doc_path = os.path.join(doc_directory, doc_filename)
    os.makedirs(doc_directory, exist_ok=True)
    return doc_path


def generate_title(transcript, num_words=3):
    """
    Функция генерирует название для документа с транскрипцией аудио.

    Args:
      transcript: Текст транскрипции аудио.
      num_words: Количество слов в названии.

    Returns:
      Строка сгенерированного названия.
    """
    # Преобразование текста к нижнему регистру
    transcript = transcript.lower()

    # Удаление пунктуации
    transcript = re.sub(r'[^\w\s]|\n', ' ', transcript)

    # Лемматизация слов
    lemmatizer = WordNetLemmatizer()
    words = [lemmatizer.lemmatize(word) for word in word_tokenize(transcript)]

    # Удаление стоп-слов
    stop_words = set(stopwords.words('russian'))
    words = [word for word in words if word not in stop_words]

    # Подсчет частоты встречаемости слов
    word_counts = {}
    for word in words:
        word_counts[word] = word_counts.get(word, 0) + 1

    # Выбор наиболее часто встречающихся слов
    top_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:num_words]

    # Формирование названия из слов
    title = ' '.join([word for word, count in top_words])

    # Возвращение названия
    return title


async def generate_text_file(content: str,
                             message_event: Message) -> tuple:
    file_name = f'Документ от {datetime.now().strftime("%d %B %Y")}.txt'
    # Кодируем содержимое в байты
    file_bytes = content.encode('utf-8')
    return file_bytes, file_name


async def from_pipeline_data_object(
        message: Message,
        bot: Bot,
        assistant_id: str,
        fsm_state: FSMContext,
        additional_system_information=None,
        additional_user_information=None,
) -> PipelineData:
    """
   Creates a PipelineData object from the provided inputs.
   """
    return PipelineData(
        telegram_message=message,
        telegram_bot=bot,
        assistant_id=assistant_id,
        fsm_bot_state=fsm_state,
        additional_system_information=additional_system_information,
        additional_user_information=additional_user_information,
    )


async def form_content(summary: str,
                       transcribed_text: str) -> str:
    return f'Самари:\n {summary} \n\n Транскрибация аудио:\n {transcribed_text}'


async def estimate_transcribe_duration(message: Message):
    media = message.content_type

    async def estimate_download_file_duration(media_type) -> float:
        file_size = media_type.file_size / (1024 * 1024)
        print()
        if file_size > 30:
            second_per_mb = 4
        else:
            second_per_mb = 4
        return file_size * second_per_mb if file_size > 0 else file_size * second_per_mb

    async def estimate_transcribe_file_duration(media_type) -> float:
        second_per_second = 12
        prediction = media_type.duration / second_per_second
        return prediction

    if media == 'document':
        download_file_duration = await estimate_download_file_duration(media_type=message.document)
        return int((download_file_duration + 6))

    elif media == 'music' or media == "audio" or media == 'voice':
        download_file_duration = await estimate_download_file_duration(media_type=message.audio)
        transcribe_duration = await estimate_transcribe_file_duration(media_type=message.audio)
        return int((download_file_duration + transcribe_duration + 6))

    elif media == 'video':
        download_file_duration = await estimate_download_file_duration(media_type=message.video)
        transcribe_duration = await estimate_transcribe_file_duration(media_type=message.video)
        print()
        return int((download_file_duration + transcribe_duration + 6))
    else:
        pass


# TODO вынести все сервесные функции
async def estimate_gen_summary_duration(text: str) -> int:
    tokens = await num_tokens_from_string(encoding_name="cl100k_base",
                                          string=text)
    token_per_second = 14
    return int((tokens / token_per_second) * 0.5)


async def num_tokens_from_string(string: str,
                                 encoding_name: str = 'cl100k_base') -> int:
    """Returns the number of tokens in a text string."""
    try:
        encoding = tiktoken.get_encoding(encoding_name)
        num_tokens = len(encoding.encode(string))
        return num_tokens
    except Exception as e:
        logging.exception(e)


if __name__ == '__main__':
    # Пример использования функции
    container_id = "bf88eef88779"
    container_file_path = "/var/lib/telegram-bot-api/6970555880:AAFrBj3go_TXClpcQzDOs50DwHCFAUD6QlM/music/file_3.mp3"
    host_file_path = r"C:\Users\artem\OneDrive\Рабочий стол\text\file_3.mp3"

    # if copy_file_from_container(container_id, container_file_path, host_file_path):
    #     print("Файл успешно скопирован.")
    # else:
    #     print("Ошибка копирования файла.")
    with open(r"C:\Users\artem\OneDrive\Рабочий стол\Тестовые данные\TXTshort.txt", encoding="utf-8") as f:
        d = f.read()
        print(generate_title(d))
