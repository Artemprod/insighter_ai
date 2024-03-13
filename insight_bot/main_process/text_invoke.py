import asyncio

import os
from abc import ABC, abstractmethod

import chardet

import aiofiles
from PyPDF2 import PdfReader
from os import path
from environs import Env
from costume_excepyions.file_read_exceptions import UnknownPDFreadFileError
from concurrent.futures import ProcessPoolExecutor
from costume_excepyions.format_exceptions import  \
    EncodingDetectionError
from logging_module.log_config import insighter_logger

from main_process.Whisper.whisper_dispatcher import  MediaRecognitionFactory
from main_process.file_format_manager import FileFormatDefiner
from dataclasses import dataclass


class TextInvoker(ABC):
    @abstractmethod
    async def invoke_text(self, file_path):
        pass


class ITextInvokeFactory(ABC):

    @abstractmethod
    async def invoke_text(self, file_path):
        pass


class IPdfFileHandler(TextInvoker):
    async def invoke_text(self, file_path):
        raise NotImplementedError('Method invoke_text() must be implemented asynchronously')


class ITxtFileHandler(TextInvoker):
    async def invoke_text(self, file_path):
        raise NotImplementedError('Method invoke_text() must be implemented asynchronously')


class IVideoFileHandler(TextInvoker):
    async def invoke_text(self, file_path):
        raise NotImplementedError('Method invoke_text() must be implemented asynchronously')


class IAudioFileHandler(TextInvoker):
    async def invoke_text(self, file_path):
        raise NotImplementedError('Method transcribe_file() must be implemented asynchronously')


class PdfFileHandler(IPdfFileHandler):
    @staticmethod
    def get_text(file_path):
        with open(file_path, "rb") as file:
            try:
                pdf = PdfReader(file)
                content_pieces = [page.extract_text() if page.extract_text() else "" for page in pdf.pages]
                content = "".join(content_pieces)
                return content
            except UnknownPDFreadFileError:
                insighter_logger.exception("Something went wrong during invoking text from PDF in corutine function")
                raise UnknownPDFreadFileError

    async def invoke_text(self, file_path):
        file_path = path.normpath(file_path)
        loop = asyncio.get_running_loop()
        with ProcessPoolExecutor(max_workers=os.cpu_count()) as pool:
            try:
                result = await loop.run_in_executor(
                    pool, self.get_text, file_path
                )
                return result
            except UnknownPDFreadFileError:
                insighter_logger.exception("Something went wrong during invoking text from PDF in invoke function")
            except Exception as e:
                insighter_logger.exception(f"Unknown Error named: {e}")


class TxtFileHandler(ITxtFileHandler):
    async def invoke_text(self, file_path):
        task = asyncio.create_task(self.__detect_encoding_fast(file_path))
        try:
            encoding = await task
            async with aiofiles.open(file_path, 'r', encoding=encoding) as t:
                content = await t.read()
            return content
        except EncodingDetectionError:
            insighter_logger.exception('Unknown encoding detection error')

    @staticmethod
    async def __detect_encoding_fast(
            file_path,
            sample_size=1024):
        async with aiofiles.open(file_path, 'rb') as f:
            sample = await f.read(sample_size)
        try:
            result = chardet.detect(sample)
            encoding = result['encoding']
            insighter_logger.info("Successful encoding detection: %s", encoding)
            return encoding
        except Exception as e:  # На практике следует уточнить тип исключения
            insighter_logger.exception("Unknown encoding detection error: %s", e)
            raise EncodingDetectionError(f"Unknown encoding detection error: {e}")


class VideoFileHandler(IVideoFileHandler):

    def __init__(self,
                 ai_transcriber: MediaRecognitionFactory):
        self.__recognizer = ai_transcriber

    async def invoke_text(self, file_path):
        try:
            result = await self.__recognizer.compile_transcription(file_path=file_path)
            insighter_logger.info(f"Text from VIDEO successfully invoked. \n The result: \n {result}")
            return result
        except Exception as e:
            insighter_logger.exception(f"something went wrong in text from Video invoking process. Error: {e}")


class AudioFileHandler(IAudioFileHandler):
    def __init__(self, ai_transcriber: MediaRecognitionFactory):
        self.__recognizer = ai_transcriber

    async def invoke_text(self, file_path):
        try:
            result = await self.__recognizer.compile_transcription(file_path=file_path)
            insighter_logger.info(f"Text from AUDIO successfully invoked. \n The result: \n {result}")
            return result
        except Exception as e:
            insighter_logger.exception(f"something went wrong in text from Video invoking process. Error: {e}")


@dataclass
class FORMATS:
    VIDEO_FORMATS: list[str]
    AUDIO_FORMATS: list[str]


    def __init__(self):
        self.__load_formats_from_env()

    def __load_formats_from_env(self) -> None:
        env: Env = Env()
        env.read_env('.env')
        self.VIDEO_FORMATS = env('VIDEO_FORMATS')
        self.AUDIO_FORMATS = env('AUDIO_FORMATS')
        if isinstance(env('VIDEO_FORMATS'), str):  # Проверка формата строки
            self.VIDEO_FORMATS = env('VIDEO_FORMATS').split(',')
        if isinstance(env('AUDIO_FORMATS'), str):
            self.AUDIO_FORMATS = env('AUDIO_FORMATS').split(',')

    def make_list_of_formats(self) -> list[str]:  # Указываем возвращаемый тип
        all_formats = self.VIDEO_FORMATS + self.AUDIO_FORMATS
        return all_formats


class TextInvokeFactory(ITextInvokeFactory):

    def __init__(self,
                 format_definer: FileFormatDefiner,
                 pdf_handler: IPdfFileHandler,
                 txt_handler: ITxtFileHandler,
                 video_handler: IVideoFileHandler,
                 audio_handler: IAudioFileHandler,
                 formats:FORMATS
                 ):
        self._format_definer = format_definer
        self._video_handler = video_handler
        self._audio_handler = audio_handler
        self._txt_handler = txt_handler
        self._pdf_handler = pdf_handler
        self.formats = formats

    async def invoke_text(self,
                          file_path: str) -> str:

        try:
            invoker = await self.__create_invoker(file_path)
        except EncodingDetectionError as e:
            insighter_logger.exception(e, 'Failf to invoke text')
            raise EncodingDetectionError

        try:
            text = await invoker.invoke_text(file_path)
            insighter_logger.info("text invoked")
            return text
        except Exception as e:
            insighter_logger.exception(e, 'Failf to invoke text')
            raise e

    async def __create_invoker(self, file_path):

        income_file_format = await self._format_definer.define_format(file_path=file_path)
        if income_file_format in self.formats.VIDEO_FORMATS:
            return self._video_handler
        elif income_file_format in self.formats.AUDIO_FORMATS:
            return self._audio_handler
        else:
            # TODO логировать все новые файлы
            insighter_logger.exception(f"This file format {income_file_format} havent supported")
            raise EncodingDetectionError(f"This file format {income_file_format} havent supported")
        # TODO Выдать что формат не правильный вывести в сообщение бот ( точно правильное место )


async def main():
    # pdf = PdfFileHandler()
    # path_pdf = r"C:\Users\artem\Downloads\тестовый документ.pdf"
    # result = await pdf.invoke_text(path_pdf)
    # print(result)
    # video_path = r"C:\Users\artem\Downloads\День 0 C++ - Как я собираюсь готовится к собеседованию в Яндекс.mp4"
    # trans = WhisperRecognitionAPI()
    # result = await VideoFileHandler(trans).invoke_text(video_path)
    # print(result)
    # txt = TxtFileHandler()
    # text_path = r"C:\Users\artem\Downloads\Telegram Desktop\Промпт_для_исследования_Инсайтер.txt"
    # result = await txt.invoke_text(text_path)
    # print(result)
    # pdf = PdfFileHandler()
    # text = TxtFileHandler()
    # video = VideoFileHandler(ai_transcriber=WhisperRecognitionAPI())
    # audio = AudioFileHandler(ai_transcriber=WhisperRecognitionAPI())
    # foramt_def = TelegramServerFileFormatDefiner()
    # factory = TextInvokeFactory(format_definer=foramt_def,
    #                             pdf_handler=pdf,
    #                             txt_handler=text,
    #                             video_handler=video,
    #                             audio_handler=audio)
    # path_f = r"C:\Users\artem\Downloads\Telegram Desktop\ПЕРЕГОВОРНАЯ - Мерлин – 2024-01-23.ogg"
    # invoker = await factory.create_invoker(file_path=path_f)
    print()


if __name__ == '__main__':
    asyncio.run(main())
