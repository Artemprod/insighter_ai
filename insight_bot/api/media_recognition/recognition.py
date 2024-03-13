
import logging
from datetime import time
import time
import tiktoken
from mutagen import File
import openai
import os
from pydub import AudioSegment
import asyncio

from retry import retry

from insiht_bot_container import config_data, logger
from logging_module.log_config import insighter_logger


class WhisperRecognitionAPI:
    gpt_model_3: str = "gpt-3.5-turbo-1106"
    gpt_model_4: str = "gpt-4"
    gpt_model_3_16: str = "gpt-3.5-turbo-16k-0613"
    whisper_model = "whisper-1"
    api_key = None
    # output_folder = r"D:\python projects\non_comertial\insighter\insight_bot\api\media_recognition\temp_files"
    output_folder = os.path.normpath(os.path.abspath('temp_files'))

    def __init__(self):
        openai.api_key = WhisperRecognitionAPI.api_key
        self.bad_word_prompt = "Эм..Ага, так, да,да..."
        self.punctuation_prompt = "Добрый день, спасибо что пришли! Сегодня..."
        self._load_api()

    @classmethod
    def _load_api(cls):
        """Загружает api key для класса, при условии что ключь находиться в env"""
        if cls.api_key is None:
            cls.api_key = config_data.ChatGPT.key
            insighter_logger.info("API ключ загружен.")

    async def transcribe_file(self, file_path) -> str:
        """в зависимости от длинны входящего файла либо нарезает либо делает сразу запрос"""
        start_time = time.time()

        audio_size = await self.get_file_size_mb(file_path)
        if audio_size > 24:
            try:
                result = await self.transcribe_large_files(file_path)       
                await self.del_temp_files()
                return result
            except Exception as e:
                insighter_logger.exception(f"Something went wrong during long transcribing file with Whisper. \n Error: {e}")
                raise e
        try:
            result = await self.get_api_request(file_path)
            insighter_logger.info(result)
            end_time = time.time()
            insighter_logger.info("время транспирации:", end_time - start_time)
            print(f"Время выполнения: {end_time - start_time} секунд")
            return result
        except Exception as e:
            insighter_logger.exception(f"Something went wrong during transcribing file with Whisper. \n Error: {e}")
            raise e

    @retry(PermissionError, tries=5, delay=1)
    async def del_temp_files(self):
        files = os.listdir(self.output_folder)
        for file in files:
            path = f'{self.output_folder}/{file}'
            try:
                os.remove(path)
                insighter_logger.info("файл удален:", path)
            except Exception as e:
                insighter_logger.exception(e, "Ошибка удаления файла")

    async def get_api_request(self, file_path, prompt=''):
        """Given a prompt, transcribe the audio file."""
        transcript = openai.audio.transcriptions.create(
            file=open(file_path, "rb"),
            model=WhisperRecognitionAPI.whisper_model,
            prompt=f'{self.punctuation_prompt}, {self.bad_word_prompt}, {prompt}',
        )
        return transcript.text

    #TODO Переделать в асинхронную функцию
    async def transcribe_large_files(self, file_path) -> str:
        """Транскрибирует большие файлы, разбивая их на части.
            Для учета контекста используеться 224 последних токена для сохранения контекста
            для сохранения пунктуации в промпте используется фразы с запятыми
            для сохранения слов паразитов использовать в промпте "эм, да, ща..." и так далее
        """
        try:
            files = await self.slice_big_audio(file_path)
            total_transcription = ""
            for filename in files:
                file_path = os.path.normpath(os.path.join(WhisperRecognitionAPI.output_folder, filename))
                transcribed_text = await self.get_api_request(file_path=file_path, prompt=total_transcription[-500:])
                total_transcription += transcribed_text + "\n"
                insighter_logger.info("Кусок текста готов")
            return total_transcription
        except Exception as e:
            insighter_logger.exception(f"Ошибка при транскрибации больших файлов: {e}")
            return ""


    async def get_file_size_mb(self, file_path):
        """
        Определяет размер файла в мегабайтах.

        Args:
        file_path (str): Путь к файлу.

        Returns:
        float: Размер файла в мегабайтах.
        """
        size_bytes = os.path.getsize(file_path)
        size_mb = size_bytes / (1024 * 1024)  # Преобразование из байтов в мегабайты
        return size_mb



    async def define_format(self, file_path):
        """
            Определяет формат аудиофайла.

            Args:
            file_path (str): Путь к аудиофайлу.

            Returns:
            str: Формат файла.
            """
        audio = File(file_path)
        if audio is not None:
            return audio.mime[0].split('/')[1]  # Возвращает тип файла после '/'
        else:
            insighter_logger.info("Неизвестный формат")
            return "None"

    async def slice_big_audio(self, audio_file_path):
        """Разделяет большой аудифайл на куски и переводит вформат mp3"""
        list_of_otput_files = []
        format = await self.define_format(audio_file_path)
        audio = AudioSegment.from_file(audio_file_path, format=format)
        segment_length = 10 * 60 * 1000
        if not os.path.exists(WhisperRecognitionAPI.output_folder):
            os.makedirs(WhisperRecognitionAPI.output_folder)

        # Разделите и экспортируйте аудио на сегменты
        for i in range(0, len(audio), segment_length):
            segment = audio[i:i + segment_length]
            chunk_file_name = f"chunk_{i // segment_length}.mp3"
            segment.export(os.path.join(WhisperRecognitionAPI.output_folder, chunk_file_name), format="mp3")
            list_of_otput_files.append(chunk_file_name)
        return list_of_otput_files

    @staticmethod
    async def num_tokens_from_string(string: str) -> int:
        """возвращает количесвто токенов в тексте """
        encoding = tiktoken.get_encoding(WhisperRecognitionAPI.gpt_model_3)
        num_tokens = len(encoding.encode(string))
        return num_tokens







async def main(file):
    task = asyncio.create_task(WhisperRecognitionAPI().transcribe_file(file))
    result = await task
    print(result)

if __name__ == '__main__':
    # start_time = datetime.datetime.now()
    # audio_path = r"D:\Python_projects\insighter\[Calculus глава 3] Формулы производных через геометрию [TubeRipper.com].webm"
    # # output_folder = r"C:\Users\artem\OneDrive\Рабочий стол\text\chunks"
    # asyncio.run(main(audio_path))
    print()
