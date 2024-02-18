class PathDoesntExistError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.__message = message

    def __str__(self):
        return f'{self.__message}'

class WrongCodecError(Exception):
    def __init__(self, message=None):
        super().__init__(message)
        self.__message = message

    def __str__(self):
        return f'{self.__message}'
class TelegramServerVolumePathExistingError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.__message = message

    def __str__(self):
        return f'{self.__message}'

class TelegramServerFileCantBeFoundError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.__message = message

    def __str__(self):
        return f'{self.__message}'