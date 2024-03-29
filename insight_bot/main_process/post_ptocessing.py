import re


class PostProcessor:
    @staticmethod
    async def clean_gibberish(text):
        """
        Метод для удаления неоднородных бессмысленных последовательностей символов из текста.
        """
        # Удаляем несмысловые последовательности символов в словах, сохраняя целостность чисел.
        # Особое внимание уделяем последовательностям символов, повторяющихся более двух раз.
        text = re.sub(r'\b(?!\d+)\w*[^A-Za-zА-Яа-я0-9\s]{2,}\w*\b', '', text)
        # Удаление длинных последовательностей одинаковых символов в словах
        text = re.sub(r'(.)\1{2,}', r'\1', text)

        return text

    async def remove_redundant_repeats(self, text):
        """
        Метод для очистки текста от повторяющихся паттернов и символов,
        включая удаление бессмысленных последовательностей символов в словах.
        """
        text = await self.clean_gibberish(text)  # Сначала очистим текст от бессмысленных последовательностей

        # Удаляем повторяющиеся символы, оставляя только один (например, "ааа" -> "а").
        text = re.sub(r'(.)\1+', r'\1', text)

        return text
