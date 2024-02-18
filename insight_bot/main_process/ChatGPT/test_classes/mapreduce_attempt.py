# class OneRequestGPTWorker(RequestGPTWorker):
#
#     async def make_gpt_request(self, assistant_id,
#                                income_text: str,
#                                additional_system_information: str = None,
#                                additional_user_information: str = None) -> str:
#         try:
#             system_massage, user_message = await self.generate_data(assistant_id=assistant_id,
#                                                                     income_text=income_text,
#                                                                     additional_system_information=additional_system_information,
#                                                                     additional_user_information=additional_user_information)
#         except Exception as e:
#             logging.exception("Failed to generate datda for for model")
#             raise GeneratingDataForModelError("Failed to generate datda for for model", exception=e)
#
#         gpt_client: GPTClient = await self.load_gpt()
#         try:
#             response = await gpt_client.complete(messages=[user_message],
#                                                  system_message=system_massage,
#                                                  )
#             logging.info(f"successful gpt api request. result is: \n {response} ")
#             return response
#
#         except Exception as e:
#             logging.exception(f"Somthing went wrong with gpt api request. Error {e}")
#             raise GptApiRequestError(f"Somthing went wrong with gpt api request. Error {e}",
#                                      exception=e)
#
#
# # noinspection PyCompatibility
# class BigDataGPTWorker(RequestGPTWorker):
#
#     def __init__(self, assistant_repositorysitory: MongoAssistantRepositoryORM,
#                  model_manager: GPTModelManager,
#                  tokenizer: TextTokenizer,
#                  ):
#         super().__init__(assistant_repositorysitory,
#                          model_manager)
#         self.__tokenizer = tokenizer
#         self.__text_spliter = tokenizer
#
#     async def __init_chunk_size(self):
#         chunk_size_in_tokens = int(0.6 * await self.model_manager.get_current_gpt_model_max_size())
#         chunk_size_in_characters = await self.__tokenizer.measure_characters_in_tokens(
#             tokens_count=chunk_size_in_tokens)
#         return chunk_size_in_characters
#
#     async def make_gpt_request(self, assistant_id, income_text: str,
#                                additional_system_information: str = None,
#                                additional_user_information: str = None):
#         # Инициализация размеров чанков перед выполнением основной логики
#
#         try:
#             documents = await self.split_long_text(income_text, assistant_id,
#                                                    additional_system_information,
#                                                    additional_user_information)
#             # Создание задач для асинхронного запроса для каждого документа
#             tasks = [self.__request(document) for document in documents]
#             result_docs = await asyncio.gather(*tasks)
#             # Обработка суммаризации документов
#             final_summary = self._final_summary()
#             return final_summary
#         except Exception as e:
#             logging.exception("Failed during GPT request processing", exc_info=e)
#
#     async def _final_summary(self, docs:ReadySummaryDocument):
#         chunk_size = await self.__init_chunk_size()
#         if
#
#
#
#
#     # 1 MAP разделить текст на части
#     async def split_long_text(self, income_text,
#                               assistant_id,
#                               additional_system_information,
#                               additional_user_information,
#                               ):
#         """
#         Function generatr small chuncks of text
#         :return:
#         """
#
#         # noinspection PyCompatibility
#         documents = await self.__split_text_to_chunks(text=income_text,
#
#                                                       assistant_id=assistant_id,
#                                                       additional_system_information=additional_system_information,
#                                                       additional_user_information=additional_user_information,
#                                                       )
#         return documents
#
#     # TODO Из этого можно сдедать продюсера для очереди потрибителия
#
#     async def __split_text_to_chunks(self,
#                                      text: str,
#                                      assistant_id: str,
#                                      additional_system_information: str,
#                                      additional_user_information: str,
#                                      chunk_overlap=None) -> list[SummaryDocument]:
#
#         # TODO вынестти параметры контекста в отдельный настройки на верхний уровень
#         chunk_size = await self.__init_chunk_size()
#         chunk_overlap = chunk_overlap if chunk_overlap else round(chunk_size * 0.3)
#         loop = asyncio.get_running_loop()
#         with ProcessPoolExecutor() as pool:
#             texts = await loop.run_in_executor(
#                 pool,
#                 self.crop_text_recursively,
#                 chunk_size, chunk_overlap, text
#             )
#             documents = []
#         try:
#             for number, text_chunk in enumerate(texts):
#                 system_massage, user_message = await self.generate_data(assistant_id=assistant_id,
#                                                                         income_text=text_chunk,
#                                                                         additional_system_information=additional_system_information,
#                                                                         additional_user_information=additional_user_information)
#                 documents.append(SummaryDocument(
#                     system_massage=system_massage,
#                     user_message=user_message,
#                     number=number))
#             return documents
#         except Exception as e:
#             logging.exception("Failed to make chuncks", e)
#
#     @staticmethod
#     def crop_text_recursively(chunk_size, chunk_overlap, text):
#         text_splitter = RecursiveCharacterTextSplitter(
#             chunk_size=chunk_size, chunk_overlap=chunk_overlap
#         )
#         texts = text_splitter.split_text(text)
#         return texts
#
#     # 2 Для каждой части сделать генерацию преобразование к gpt
#     async def __request(self,
#                         document: SummaryDocument) -> ReadySummaryDocument:
#
#         gpt_client: GPTClient = await self.load_gpt()
#         try:
#             response = await gpt_client.complete(messages=[document.user_message],
#                                                  system_message=document.system_massage,
#                                                  )
#             logging.info(f"successful gpt api request. result is: \n {response} ")
#             document = await self.__make_document(summarized_text=response,
#                                                   number=document.number)
#             return document
#         except Exception as e:
#             logging.exception(f"Somthing went wrong with gpt api request. Error {e}")
#             raise GptApiRequestError(f"Somthing went wrong with gpt api request. Error {e}",
#                                      exception=e)
#
#     @staticmethod
#     async def __make_document(summarized_text,
#                               number) -> ReadySummaryDocument:
#         return ReadySummaryDocument(
#             content=summarized_text,
#             number=number
#         )
#
#     # 3 Объеденить результаты
#     async def __reduce_result(self):
#         """
#         Input - sorted documents reduce in one text
#         :return:
#         """
#         ...