import asyncio

import datetime as dt_t
import math
from datetime import datetime

import ffmpeg
import tiktoken
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram import Bot

from DB.Mongo.mongo_db import MongoAssistantRepositoryORM, UserBalanceRepoORM
from DB.Mongo.mongo_enteties import Assistant
from api.gpt import GPTAPIrequest
import os
from abc import ABC

from costume_excepyions.system_exceptions import SystemTypeError
from enteties.pipline_data import PipelineData

import re
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer

from insiht_bot_container import server_file_manager, config_data, file_format_manager, text_invoker
from lexicon.LEXICON_RU import LEXICON_RU
from logging_module.log_config import insighter_logger
from main_process.file_manager import ServerFileManager
from states.summary_from_audio import FSMSummaryFromAudioScenario


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
        file_duration: float,
        file_path: str,
        file_type: str,
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
        file_duration=file_duration,
        additional_system_information=additional_system_information,
        additional_user_information=additional_user_information,
        process_time={},
        file_path=file_path,
        file_type=file_type
    )


async def generate_telegram_user_link(username,
                                      user_tg_id) -> str:
    """
    Функция генерирует ссылку на Telegram пользователя.

    Args:
        user: Объект `types.User` от aiogram.

    Returns:
        Ссылка на Telegram пользователя.
    """

    if username:
        return f"https://t.me/{username}"
    else:
        return f"tg://user?id={user_tg_id}"


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

    elif media == 'music' or media == "audio":
        download_file_duration = await estimate_download_file_duration(media_type=message.audio)
        transcribe_duration = await estimate_transcribe_file_duration(media_type=message.audio)
        return int((download_file_duration + transcribe_duration + 6))

    elif media == 'voice':
        download_file_duration = await estimate_download_file_duration(media_type=message.voice)
        transcribe_duration = await estimate_transcribe_file_duration(media_type=message.voice)
        return int((download_file_duration + transcribe_duration + 6))

    elif media == 'video':
        download_file_duration = await estimate_download_file_duration(media_type=message.video)
        transcribe_duration = await estimate_transcribe_file_duration(media_type=message.video)
        print()
        return int((download_file_duration + transcribe_duration + 6))
    else:
        pass


async def compare_user_minutes_and_file(user_tg_id, file_duration, user_balance_repo: UserBalanceRepoORM):
    user_time_balance = await user_balance_repo.get_user_time_balance(tg_id=user_tg_id)
    return user_time_balance - file_duration


async def estimate_media_duration_in_minutes(bot: Bot,
                                             message: Message):
    file_path_coro = None
    system_type = config_data.system.system_type
    if system_type == "docker":
        file_path_coro = server_file_manager.get_media_file(message=message, bot=bot)
    elif system_type == "local":
        file_path_coro = ServerFileManager().get_media_file(message=message,
                                                            bot=bot)
    file_path = await file_path_coro
    file_duration = await get_media_duration_in_seconds(file_path)
    return file_duration


async def get_media_duration_in_seconds(filepath):
    """
    Извлекает длину медиафайла (видео или аудио) из метаданных и возвращает её в секундах.

    Args:
        filepath: Путь к медиафайлу.

    Returns:
        Длительность медиафайла в секундах.
    """
    probe = await asyncio.to_thread(ffmpeg.probe, filepath)
    format_info = probe['format']
    duration_sec = float(format_info['duration'])

    print(f"Длина медиафайла: {duration_sec:.2f} секунд(ы)")
    return duration_sec


async def seconds_to_min_sec(seconds):
    # Округляем секунды до большего
    seconds_rounded = math.ceil(seconds)

    # Создаем объект timedelta
    td = dt_t.timedelta(seconds=seconds_rounded)

    # Получаем общее количество минут и оставшиеся секунды
    total_minutes = td.seconds // 60
    remaining_seconds = td.seconds % 60

    # Формируем строку с часами и минутами
    return f"{total_minutes}:{remaining_seconds:02d}"


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
        insighter_logger.exception(e)


# async def calculate_gpt_cost(input_text,
#                              response_text,
#                              model='gpt-3.5-turbo-16k-0613'):
#     model_cost_mapping = {
#         "gpt-4": 0.03,
#         "gpt-4-completion": 0.06,
#         "gpt-3.5-turbo": 0.002,
#         "gpt-3.5-turbo-16k-0613": 0.002,
#     }
#
#     # Получаем кодировку для модели с использованием tiktoken
#     encoding = tiktoken.encoding_for_model(model)
#
#     # Подсчитываем количество токенов для входного и выходного текста
#     prompt_tokens = len(encoding.encode(input_text))
#     completion_tokens = len(encoding.encode(response_text))
#
#     # Определяем цену за токен исходя из модели
#     base_cost_per_token = model_cost_mapping.get(model, None)
#     if base_cost_per_token is None:
#         raise ValueError(f"Unknown model: {model}. Please provide a valid OpenAI model name.")
#
#     # Считаем общую стоимость, учитывая количество токенов для запроса и ответа
#     total_cost = ((prompt_tokens + completion_tokens) * base_cost_per_token) / 1000  # предполагаем цену за 1000 токенов
#     return round(total_cost, 6)

async def get_openai_model_cost_table(model_name='gpt-3.5-turbo', is_completion=False):
    model_cost_mapping = {
        "gpt-4": 0.03,
        "gpt-4-0314": 0.03,
        "gpt-4-completion": 0.06,
        "gpt-4-0314-completion": 0.06,
        "gpt-4-32k": 0.06,
        "gpt-4-32k-0314": 0.06,
        "gpt-4-32k-completion": 0.12,
        "gpt-4-32k-0314-completion": 0.12,
        "gpt-3.5-turbo": 0.002,
        "gpt-3.5-turbo-0301": 0.002,
        "gpt-3.5-turbo-16k-0613": 0.002,
        "text-ada-001": 0.0004,
        "ada": 0.0004,
        "text-babbage-001": 0.0005,
        "babbage": 0.0005,
        "text-curie-001": 0.002,
        "curie": 0.002,
        "text-davinci-003": 0.02,
        "text-davinci-002": 0.02,
        "code-davinci-002": 0.02,
    }
    cost = model_cost_mapping.get(
        model_name.lower()
        + ("-completion" if is_completion and model_name.startswith("gpt-4") else ""),
        None,
    )
    if cost is None:
        raise ValueError(
            f"Unknown model: {model_name}. Please provide a valid OpenAI model name."
            "Known models are: " + ", ".join(model_cost_mapping.keys())
        )
    return cost


async def calculate_gpt_cost_with_tiktoken(input_text,
                                           response_text,
                                           model='gpt-3.5-turbo-16k-0613'):
    # Получаем кодировку для модели
    encoding = tiktoken.encoding_for_model(model)

    # Получаем стоимость токена для модели и завершающего ответа
    prompt_cost_per_token = await get_openai_model_cost_table(model_name=model, is_completion=False)
    completion_cost_per_token = await get_openai_model_cost_table(model_name=model, is_completion=True)

    # Подсчитываем количество токенов
    prompt_tokens = len(encoding.encode(input_text))
    completion_tokens = len(encoding.encode(response_text))

    # Рассчитываем общую стоимость
    prompt_cost = (prompt_tokens * prompt_cost_per_token) / 1000
    completion_cost = (completion_tokens * completion_cost_per_token) / 1000

    total_cost = prompt_cost + completion_cost
    return round(total_cost, 6)


async def calculate_whisper_cost(duration_sec,
                                 model='base',
                                 quality='standard'):
    """
    Функция для расчета стоимости использования Whisper API в зависимости
    от модели, длительности и качества аудио.

    :param model: Модель Whisper ('base', 'advanced').
    :param quality: Качество аудио ('standard', 'high').
    :return: Возвращает общую стоимость обработки аудио.

        duration_sec:
    """

    model_multiplier = {
        'base': 1,
        'advanced': 1.5  # Предположим, что продвинутая модель дороже на 50%
    }

    quality_multiplier = {
        'standard': 1,
        'high': 1.2  # Предположим, что высокое качество дороже на 20%
    }

    # Базовая ставка за минуту
    base_rate_per_sec = 0.0001  # $0.0001 за секунду

    # Рассчитываем множители модели и качества
    model_mult = model_multiplier.get(model, 1)
    quality_mult = quality_multiplier.get(quality, 1)

    # Итоговая стоимость
    total_cost = duration_sec * base_rate_per_sec * model_mult * quality_mult

    return round(total_cost, 4)  # Округляем до четырех знаков после запятой


async def format_filter(message,
                        bot,
                        state):
    system = config_data.system.system_type
    print(system)
    if system == "docker":
        file_path_coro = server_file_manager.get_media_file(message=message, bot=bot)
    elif system == "local":
        file_path_coro = ServerFileManager().get_media_file(message=message,
                                                            bot=bot)

    else:
        insighter_logger.exception("Unknown system, add new system")
        raise SystemTypeError("Unknown system, add new system")

    begin_message = await bot.send_message(chat_id=message.chat.id,
                                           text=f"Определяю формат файла...")
    try:
        file_path = await file_path_coro
        income_file_format = await file_format_manager.define_format(file_path=file_path)

        if income_file_format in text_invoker.formats.make_list_of_formats():
            await bot.delete_message(message_id=begin_message.message_id, chat_id=begin_message.chat.id)
            return file_path, income_file_format
        else:
            await bot.delete_message(message_id=begin_message.message_id, chat_id=begin_message.chat.id)
            message = await bot.send_message(chat_id=message.chat.id,
                                             text=LEXICON_RU['wrong_format'].format(
                                                 income_file_format=income_file_format,
                                                 actual_formats=LEXICON_RU['actual_formats'])
                                             )
            await state.update_data(instruction_message_id=message.message_id)
            await state.set_state(FSMSummaryFromAudioScenario.load_file)
            return None
    except Exception as e:
        insighter_logger.exception(e)
        await bot.delete_message(message_id=begin_message.message_id, chat_id=begin_message.chat.id)
        message = await bot.send_message(chat_id=message.chat.id,
                                         text=LEXICON_RU['error_message'])

        await state.update_data(instruction_message_id=message.message_id)
        await state.set_state(FSMSummaryFromAudioScenario.load_file)


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
