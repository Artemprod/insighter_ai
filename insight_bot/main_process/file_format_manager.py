import asyncio
import logging
import os
from os import path
from abc import ABC, abstractmethod
import magic
import filetype
from costume_excepyions.format_exceptions import UnknownFormatRecognitionError
from costume_excepyions.path_exceptions import PathDoesntExistError, WrongCodecError
from logging_module.log_config import insighter_logger
from main_process.func_decorators import ameasure_time


class FileFormatDefiner(ABC):
    @abstractmethod
    async def define_format(self,
                            file_path) -> str:
        pass


class TelegramServerFileFormatDefiner(FileFormatDefiner):
    @ameasure_time
    async def define_format(self,
                            file_path) -> str:
        file_path = path.normpath(file_path)
        magic_task = asyncio.create_task(self.__magic_define_format(file_path=file_path),
                                         name="define format by magic")

        try:
            result = await magic_task
            return result.split('/')[-1]
        except (PathDoesntExistError, WrongCodecError):
            insighter_logger.exception('magic_task failed to handle a work')
            insighter_logger.info('start kind task...')
            kind_task = asyncio.create_task(self.__kind_define_format(file_path=file_path),
                                            name="define format by kind")
            try:
                result = await kind_task
                return result

            except UnknownFormatRecognitionError:
                insighter_logger.exception('magic_task failed to handle a work')
                insighter_logger.info('start simple string task...')
                string_task = asyncio.create_task(self.__simple_string_define_format(file_path=file_path),
                                                  name="define format by simple string recogntion")
                try:
                    result = await string_task
                    return result
                except UnknownFormatRecognitionError:
                    insighter_logger.exception('all format methods are failed, try another')
                    #TODO Добавить отправку сообщения что формат файла не подхиодит отправ




    async def __magic_define_format(self, file_path) -> str:
        path_to_file = os.path.abspath(file_path)
        if path.exists(path_to_file):
            try:
                result = magic.from_file(path_to_file, mime=True)
            except UnicodeDecodeError:
                raise WrongCodecError()
            if not "No such file or directory" and "cannot open" in result:
                return result
            raise PathDoesntExistError("i can't open this file because No such file or directory")
        else:
            insighter_logger.error(f'path {path_to_file} doesnt exist')
            raise PathDoesntExistError(f'path {path_to_file}  doesnt exist')

    @staticmethod
    async def __kind_define_format(file_path):
        kind = filetype.guess(file_path)
        if kind is None:
            insighter_logger.error('Unknown format ,kind cant managed to retrieve information ')
            raise UnknownFormatRecognitionError('Неизвестный формат')
        else:
            insighter_logger.info('successfully work of Kind \n\n File MIME type: %s' % kind.mime)
            return kind.extension

    @staticmethod
    async def __simple_string_define_format(file_path) -> str:

        file_name = file_path.split('\\')[-1]
        file_format = file_name.split('.')[-1]
        if file_format:
            return file_format
        raise UnknownFormatRecognitionError('cant find a proper format by string')



async def main():
    path_f = r"C:\Users\artem\OneDrive\Рабочий стол\Collection-of-tasks-in-mathematics-for-those-entering-the-technical-universities-under-the-editorship-of-M.I.Skanavi.pdf"
    a = TelegramServerFileFormatDefiner()
    result_2 = await a.define_format(path_f)

    print(result_2)


if __name__ == '__main__':
    asyncio.run(main())
