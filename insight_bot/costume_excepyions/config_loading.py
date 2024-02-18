class APIKeyLoadError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.__message = message

    def __str__(self):
        return f'{self.__message}'

class WhisperLanguageLoadError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.__message = message

    def __str__(self):
        return f'{self.__message}'

class ContextLengthLoadingError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.__message = message

    def __str__(self):
        return f'{self.__message}'


class ModelVersionLoadingError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.__message = message

    def __str__(self):
        return f'{self.__message}'

class ModelTempretureLoadingError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.__message = message

    def __str__(self):
        return f'{self.__message}'