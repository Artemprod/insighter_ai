# import asyncio
# import logging
# import string
# from abc import abstractmethod
# from concurrent.futures import ThreadPoolExecutor
#
# import spacy
# from typing import List, Optional
# import nltk
# from nltk.corpus import stopwords
# from nltk.tokenize import word_tokenize
# from string import punctuation
# from pymorphy2 import MorphAnalyzer
#
# class TextPreprocessor:
#     @abstractmethod
#     async def do_preprocessing(self):
#         pass
#
#
# class SpacyTextPreprocessor:
#     def __init__(self, language="ru"):
#         self.language = language
#         self.model_name = "ru_core_news_sm" if language == "ru" else "en_core_web_sm"
#         self._nlp = None
#
#     def _load_model(self):
#         if self._nlp is None:
#             try:
#                 self._nlp = spacy.load(self.model_name, disable=["parser", "ner"])
#             except IOError:
#                 insighter_logger.exception(f"Model {self.model_name} not installed. Please install using 'spacy.cli.download'")
#                 raise
#         return self._nlp
#
#     async def preprocess_text(self, text):
#         nlp = self._load_model()
#         # Использование существующего цикла событий и контекстного менеджера для ThreadPoolExecutor
#         doc = await asyncio.get_event_loop().run_in_executor(None, lambda: nlp(text))
#         result = " ".join([
#             token.lemma_ for token in doc if not token.is_stop and token.pos_ in ["NOUN", "VERB", "ADJ", "ADV"]
#         ])
#         return result
#
#
# class RussianTextPreprocessor:
#     def __init__(self):
#         self.stopwords = set(stopwords.words("russian")) | set(punctuation)
#         self.morph = MorphAnalyzer()
#
#     def preprocess_text(self, text: str) -> str:
#         tokens = word_tokenize(text.lower())
#         lemmas = [self.morph.parse(token)[0].normal_form for token in tokens if token not in self.stopwords]
#         return " ".join(lemmas)
#
#
# class TextPreprocessorAggregator:
#     def __init__(self, language="ru"):
#         self.spacy_preprocessor = SpacyTextPreprocessor(language)
#         self.russian_preprocessor = RussianTextPreprocessor()
#
#     async def preprocess_text(self, text: str) -> str:
#         try:
#             return await self.spacy_preprocessor.preprocess_text(text)
#         except Exception as e:
#             logging.warning(f"Spacy preprocessing failed: {e}, switching to RussianTextPreprocessor")
#             try:
#                 return await asyncio.get_event_loop().run_in_executor(None, lambda: self.russian_preprocessor.preprocess_text(text))
#             except Exception as ee:
#                 insighter_logger.exception(f"RussianTextPreprocessor failed: {ee}")
#
#         insighter_logger.exception("All preprocessing methods failed. Returning original text.")
#         return text
#
#
# if __name__ == "__main__":
#     async def main():
#         preprocessor = TextPreprocessorAggregator("ru")
#
#         with open(r"C:\Users\artem\OneDrive\Рабочий стол\Меня видно Видно. 3-2 раза. Так, я .txt", 'r',
#                   encoding="utf-8") as f:
#             text = f.read()
#         processed_text = await preprocessor.preprocess_text(text)
#         print(processed_text)
#
#
#     asyncio.run(main())