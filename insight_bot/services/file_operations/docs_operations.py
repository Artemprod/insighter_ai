


# class FileHandler:
#     async def read_file(self, file_path):
#         raise NotImplementedError
#
#
# class PdfFileHandler(FileHandler):
#     async def read_file(self, file_path):
#         content = ""
#         with open(file_path, "rb") as file:
#             pdf = PdfReader(file)
#             for page in pdf.pages:
#                 content += page.extract_text() if page.extract_text() else ""
#         return content
#
#
# class TxtFileHandler(FileHandler):
#     async def read_file(self, file_path):
#         async with aiofiles.open(file_path, 'rb') as rawfile:
#             rawdata = await rawfile.read()
#             result = chardet.detect(rawdata)
#             encoding = result['encoding']
#
#         async with aiofiles.open(file_path, 'r', encoding=encoding) as t:
#             content = await t.read()
#         return content
#
#
# class WebmFileHandler(FileHandler):
#     async def read_file(self, file_path):
#         return 'video'
#
#
# class FileProcessorFactory:
#     @staticmethod
#     async def __get_file_handler(file_path):
#         _, file_extension = os.path.splitext(file_path)
#         file_extension = file_extension.lower()
#
#         if file_extension == '.pdf':
#             return PdfFileHandler()
#         elif file_extension == '.txt':
#             return TxtFileHandler()
#         elif file_extension == '.webm':
#             return WebmFileHandler()
#         else:
#             raise ValueError("Unsupported file format")
#
#     async def execute_processor_command(self, file_path):
#         processor = await self.__get_file_handler(file_path)
#         result = await processor.read_file(file_path)
#         return result
#
#
# if __name__ == '__main__':
#     print()
#     # Пример использования
#     # file_format = 'pdf' # или 'txt'
#     # file_handler = await FileProcessorFactory.get_file_handler(file_format)
#     # content = await file_handler.read_file(file_on_disk)
#     # answer = await work_assistant.conversation(content)
#     # await message.answer(text=answer)
