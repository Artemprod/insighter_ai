
import logging
import os
from main_process.file_format_manager import FileFormatDefiner

import asyncio
from pydub import AudioSegment
from functools import partial

class MediaFileManager:
    def __init__(self,
                 file_format_manager: FileFormatDefiner):
        self.__format_manager = file_format_manager

    @staticmethod
    async def get_file_size_mb(file_path):
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

    async def export_segment_async(self, segment, saving_path, media_format="mp3"):
        loop = asyncio.get_running_loop()
        try:
            result = await loop.run_in_executor(
                None,
                partial(self.export_segment, segment, saving_path, media_format)
            )
            return result
        except Exception as e:
            logging.exception(f"Failed to export segment: {e}")
            return None

    @staticmethod
    def export_segment(segment, saving_path, media_format="mp3"):
        segment.export(saving_path, format=media_format)
        print(f"Exported segment to {saving_path}")
        return saving_path

    async def process_audio_segments(self, audio_file_path, output_directory_path):
        media_format = await self.__format_manager.define_format(file_path=audio_file_path)
        audio = AudioSegment.from_file(audio_file_path, format=media_format)
        semaphore = asyncio.Semaphore(10)  # Control concurrency
        segment_length = 10 * 60 * 1000  # 10 minutes in milliseconds
        tasks = [self.limit_task(semaphore, self.export_segment_async,
                                 audio[i:i + segment_length],
                                 os.path.join(output_directory_path, f"chunk_{i // segment_length}.{media_format}"),
                                 media_format)
                 for i in range(0, len(audio), segment_length)]

        return await asyncio.gather(*tasks)

    async def limit_task(self, semaphore, func, *args, **kwargs):
        async with semaphore:
            result = await func(*args, **kwargs)
            return result



    # async def slice_big_audio(self,
    # audio_file_path,
    #                           output_directory_path: str,
    #                           ):
    #     """Разделяет большой аудифайл на куски и переводит вформат mp3"""
    #     media_format = await self.__format_manager.define_format(file_path=audio_file_path)
    #     audio = AudioSegment.from_file(audio_file_path, format=media_format)
    #     # TODO Вынести параметры сигментации в верхний уровень
    #     segment_length = 10 * 60 * 100
    #     tasks = []
    #     # Crop audio to segments
    #     for i in range(0, len(audio), segment_length):
    #         segment = audio[i:i + segment_length]
    #
    #         #TODO Разобраться как не конверитировать формата не коверитировать в таком формате
    #         chunk_file_name: str = f"chunk_{i // segment_length}.mp3"
    #         saving_path = os.path.join(output_directory_path, chunk_file_name)
    #         tasks.append(asyncio.create_task(self.__run_export_segment_in_pool(segment=segment,
    #                                                                            saving_path=saving_path)))
    #     result = await asyncio.gather(*tasks)
    #     return result
    #
    # @staticmethod
    # async def export_segment(segment,
    #                      saving_path):
    #     try:
    #         segment.export(saving_path, format="mp3")
    #         return saving_path
    #     except Exception as e:
    #         logging.exception(f"failed to export piece of audio segment. Exception {e}")

    # async def __run_export_segment_in_pool(self, segment,
    #                                        saving_path):
    #     loop = asyncio.get_event_loop()
    #     with ProcessPoolExecutor(max_workers=os.cpu_count()) as pool:
    #         work = loop.run_in_executor(
    #             pool, self.export_segment,
    #             segment,
    #             saving_path,
    #         )
    #         try:
    #             result = await work
    #             logging.info("Successfully crop media")
    #             print(result)
    #             return saving_path
    #         except Exception as e:
    #             logging.exception(e)
    #     try:
    #
    #         return saving_path
    #     except Exception as e:
    #         logging.exception(e)


