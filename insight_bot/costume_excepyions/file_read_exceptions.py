class UnknownPDFreadFileError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.__message = message


    def __str__(self):
        return f'{self.__message}'

class MediaFileLoadError(Exception):
    def __init__(self,
                 message=None,
                 exception=None):
        super().__init__(message)
        self.__message = message
        self.exception = exception

    def __str__(self):
        return f'{self.__message}, exception:{self.exception}'