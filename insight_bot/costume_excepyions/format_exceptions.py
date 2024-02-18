class UnknownFormatRecognitionError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.__message = message

    def __str__(self):
        return f'{self.__message}'


class NotSupportedFormatError(Exception):
    def __init__(self, message=None):
        super().__init__(message)
        self.__message = message

    def __str__(self):
        return f'Format is not supported{self.__message}'


class EncodingDetectionError(Exception):
    def __init__(self, message=None):
        super().__init__(message)
        self.__message = message

    def __str__(self):
        return f'{self.__message}'

class TelegramCantFindFileError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.__message = message

    def __str__(self):
        return f'{self.__message}'

