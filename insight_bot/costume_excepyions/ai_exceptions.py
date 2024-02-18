class TokenCapacityMeasurement(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.__message = message

    def __str__(self):
        return f'{self.__message}'


class CharactersInTokenMeasurement(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.__message = message

    def __str__(self):
        return f'{self.__message}'


class GptApiRequestError(Exception):
    def __init__(self, message, exception=None):
        super().__init__(message)
        self.__message = message
        self.exception = exception

    def __str__(self):
        return f'{self.__message}, exception:{self.exception}'


class EmptyResponseArrayError(Exception):
    def __init__(self, message, exception=None):
        super().__init__(message)
        self.__message = message
        self.exception = exception

    def __str__(self):
        return f'{self.__message}, exception:{self.exception}'


class LoadingLongRequestMethodError(Exception):
    def __init__(self, message, exception=None):
        super().__init__(message)
        self.__message = message
        self.exception = exception

    def __str__(self):
        return f'{self.__message}, exception:{self.exception}'


class LoadingShortRequestMethodError(Exception):
    def __init__(self, message, exception=None):
        super().__init__(message)
        self.__message = message
        self.exception = exception

    def __str__(self):
        return f'{self.__message}, exception:{self.exception}'


class CompileRequestError(Exception):
    def __init__(self, message, exception=None):
        super().__init__(message)
        self.__message = message
        self.exception = exception

    def __str__(self):
        return f'{self.__message}, exception:{self.exception}'


class GeneratingDataForModelError(Exception):
    def __init__(self, message, exception=None):
        super().__init__(message)
        self.__message = message
        self.exception = exception

    def __str__(self):
        return f'{self.__message}, exception:{self.exception}'


class GeneratingDocumentsError(Exception):
    def __init__(self, message, exception=None):
        super().__init__(message)
        self.__message = message
        self.exception = exception

    def __str__(self):
        return f'{self.__message}, exception:{self.exception}'


class LoadingShorthandsTranscriberError(Exception):
    def __init__(self, message=None, exception=None):
        super().__init__(message)
        self.__message = message
        self.exception = exception

    def __str__(self):
        return f'{self.__message}, exception:{self.exception}'


class LoadingLongTranscriberError(Exception):
    def __init__(self, message=None, exception=None):
        super().__init__(message)
        self.__message = message
        self.exception = exception

    def __str__(self):
        return f'{self.__message}, exception:{self.exception}'

class MediaSizeError(Exception):
    def __init__(self, message=None, exception=None):
        super().__init__(message)
        self.__message = message
        self.exception = exception

    def __str__(self):
        return f'{self.__message}, exception:{self.exception}'

class TranscribitionError(Exception):
    def __init__(self, message=None,
                 exception=None):
        super().__init__(message)
        self.__message = message
        self.exception = exception

    def __str__(self):
        return f'{self.__message}, exception:{self.exception}'
class ShortMediaTranscribitionError(Exception):
    def __init__(self, message=None,
                 exception=None):
        super().__init__(message)
        self.__message = message
        self.exception = exception

    def __str__(self):
        return f'{self.__message}, exception:{self.exception}'

class AsyncTranscribitionError(Exception):
    def __init__(self, message=None,
                 exception=None):
        super().__init__(message)
        self.__message = message
        self.exception = exception

    def __str__(self):
        return f'{self.__message}, exception:{self.exception}'