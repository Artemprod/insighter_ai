import functools
import logging
from datetime import time
import time
import os
import asyncio
from abc import ABC

import aiofiles.tempfile

from costume_excepyions.ai_exceptions import LoadingShorthandsTranscriberError, \
    LoadingLongTranscriberError, MediaSizeError, TranscribitionError, ShortMediaTranscribitionError, \
    AsyncTranscribitionError

from logging_module.log_config import insighter_logger
from main_process.Whisper.openai_whisper_complain import WhisperClient
from main_process.Whisper.whisper_information import WhisperModelManager
from main_process.file_format_manager import TelegramServerFileFormatDefiner
from main_process.func_decorators import ameasure_time
from main_process.media_file_manager import MediaFileManager






class MediaFileTranscriber(ABC):
    def __init__(self,
                 whisper_client: WhisperClient):
        self.whisper_client = whisper_client

    async def transcribe_media(self, file) -> str:
        raise NotImplementedError


# noinspection PyTypeChecker
class ShortMediaFilesTranscriber(MediaFileTranscriber):

    async def transcribe_media(self,
                               file) -> str:

        task = asyncio.create_task(self.whisper_client.whisper_compile(
            file_path=file))
        try:
            recognized_text = await task
            insighter_logger.info("Successfully transcribe file")
            return recognized_text
        except Exception as e:
            insighter_logger.exception(f"Failed to transcribe short media file. exception {e}")
            raise ShortMediaTranscribitionError(exception=e)


class LongMediaFilesTranscriber(MediaFileTranscriber):

    def __init__(self,
                 whisper_client: WhisperClient,
                 media_file_manager: MediaFileManager):
        super().__init__(whisper_client)
        self.__media_file_manager = media_file_manager

    @ameasure_time
    async def transcribe_media(self,
                               file):

        async with aiofiles.tempfile.TemporaryDirectory() as directory:

            task = asyncio.create_task(self.__do_request(
                audio_file_path=file,
                output_directory_path=directory,
            ))
            try:
                result = await task
                insighter_logger.info(f"Successfully transcribe text. Result: {result}")
                return result
            except Exception as e:
                insighter_logger.exception(e)

    async def __do_request(self,
                           audio_file_path: str,
                           output_directory_path: aiofiles.tempfile.TemporaryDirectory):

        try:
            slice_task = asyncio.create_task(
                self.__media_file_manager.process_audio_segments(audio_file_path=audio_file_path,
                                                          output_directory_path=output_directory_path))
            files: list[str] = await slice_task
            tasks = []
            for number, file in enumerate(files):
                tasks.append(asyncio.create_task(self.whisper_client.whisper_compile(file_path=file)))
            try:
                result = await asyncio.gather(*tasks)
                total_transcription = ' '.join(result)
                return total_transcription
            except Exception as e:
                insighter_logger.exception(f"Failed to manage async transcribe. Exception {e}")
                raise AsyncTranscribitionError("Faild to manage async trancribe", exception=e)
        except Exception as e:
            insighter_logger.exception(f"Failed to transcribe: {e}")
            return ""

            # try:
            #     transcribed_text = await self.whisper_client.whisper_compile(file_path=file,
            #                                                                  )
            #     total_transcription += transcribed_text + "\n"
            #     insighter_logger.info(f"{number} piece of text is ready ... ")
            # except EmptyResponseArrayError:
            #     insighter_logger.exception(EmptyResponseArrayError)
            #     #TODO придумать как обработвать
            #     continue


class MediaRecognitionFactory:

    def __init__(
            self,
            media_file_manager: MediaFileManager,
            short_media_transcriber: ShortMediaFilesTranscriber,
            long_media_transcriber: LongMediaFilesTranscriber):
        self.__media_file_manager = media_file_manager
        self.__long_media_transcriber = long_media_transcriber
        self.__short_media_transcriber = short_media_transcriber

    async def compile_transcription(self,
                                    file_path: str) -> str:
        """
               Return text
               :param file_path:
               :return:
        """

        try:
            request_method = await self.__factory_method(file_path=file_path)
            result = await request_method.transcribe_media(file=file_path)
            insighter_logger.info(f"successful transcribe text. Result is:"
                         f" \n {result}")
            return result
        except Exception as e:
            insighter_logger.exception(f'Failed to make request, exception is: {e}')
            raise TranscribitionError(exception=e)

    async def __factory_method(self,
                               file_path: str) -> MediaFileTranscriber:
        audio_size = await self.__media_file_manager.get_file_size_mb(file_path)
        # TODO вынести настройки размера модеоли
        if audio_size < 24:
            try:
                return self.__short_media_transcriber
            except Exception as e:
                insighter_logger.exception(f"faild to load class of short trancriber {e}")
                raise LoadingShorthandsTranscriberError(exception=e)
        elif audio_size >= 24:
            try:
                return self.__long_media_transcriber
            except Exception as e:
                insighter_logger.exception(f"faild to load class of long trancriber {e}")
                raise LoadingLongTranscriberError(exception=e)
        else:
            raise MediaSizeError(message="File size equal 0")


async def main():
    # task = asyncio.create_task(WhisperRecognitionAPI().transcribe_file(file))
    # result = await task
    # print(result)
    path = r"C:\Users\artem\Downloads\audio1830177390.m4a"
    a = WhisperClient(whisper_manager=WhisperModelManager())
    # r = await a.whisper_compile(file_path=path)
    # print(r)

    m = MediaFileManager(
        file_format_manager=TelegramServerFileFormatDefiner())
    s = ShortMediaFilesTranscriber(whisper_client=a)
    l = LongMediaFilesTranscriber(whisper_client=a,
                                  media_file_manager=m)

    f = MediaRecognitionFactory(media_file_manager=m,
                                short_media_transcriber=s,
                                long_media_transcriber=l)

    res = await f.compile_transcription(file_path=path)
    print(res)


if __name__ == '__main__':
    # start_time = datetime.datetime.now()
    # audio_path = r"D:\Python_projects\insighter\[Calculus глава 3] Формулы производных через геометрию [TubeRipper.com].webm"
    # # output_folder = r"C:\Users\artem\OneDrive\Рабочий стол\text\chunks"
    asyncio.run(main())

    print()
