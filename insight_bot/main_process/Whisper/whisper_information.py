
from environs import Env

from costume_excepyions.config_loading import ModelVersionLoadingError, APIKeyLoadError, WhisperLanguageLoadError


class WhisperModelManager:

    def get_current_whisper_model_in_use_from_env(self) -> str:
        """
        Method loads actual whisper model fro api
        :return:
        """
        env: Env = Env()
        env.read_env()
        try:
            return env("WHISPER_MODEL_VERSION")
        except Exception as e:
            insighter_logger.exception(f"Failed to load model version. Error {e} in class {self.__dict__}")
            raise ModelVersionLoadingError(f"Failed to load model version. Error {e} in class {self.__dict__}")

    def get_gpt_api_key(self):
        env = Env()
        env.read_env(".env")
        try:
            return env("OPENAI_API_KEY")
        except Exception as e:
            insighter_logger.exception(f"Failed to load open ai key. Error {e} in class {self.__dict__}")
            raise APIKeyLoadError(f"Failed to load open ai key. Error {e} in class {self.__dict__}")

    def get_whisper_language(self):
        env = Env()
        env.read_env(".env")
        try:
            return env("WHISPER_LANGUAGE")
        except Exception as e:
            insighter_logger.exception(f"Failed to load language. Error {e} in class {self.__dict__}")
            raise WhisperLanguageLoadError(f"Failed to load language. Error {e} in class {self.__dict__}")

    def get_temperature(self):
        env = Env()
        env.read_env(".env")
        try:
            return env("WHISPER_MODEL_TEMPERATURE")
        except Exception as e:
            insighter_logger.exception(f"Failed to load language. Error {e} in class {self.__dict__}")
            raise WhisperLanguageLoadError(f"Failed to load language. Error {e} in class {self.__dict__}")
