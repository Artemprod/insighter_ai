from environs import Env
from dataclasses import dataclass


@dataclass
class System_type:
    system_type: str

@dataclass
class OpenAI_KEY:
    key: str


@dataclass
class TelegramBot:
    tg_bot_token: str


@dataclass
class MongoDB:
    bd_name: str
    # для пользования на локальной машине
    local_port: int
    local_host: int | str
    # для пользования на сервере в доккере
    docker_port: int
    docker_host: int | str


@dataclass
class RedisStorage:
    # для пользования на локальной машине
    main_bot_local_port: int
    main_bot_local_host: int | str

    # для пользования на сервере в доккере
    main_bot_docker_port: int
    main_bot_docker_host: int | str


@dataclass
class TelegramServer:
    URI: str

@dataclass
class Config:
    Bot: TelegramBot
    ChatGPT: OpenAI_KEY
    data_base: MongoDB
    redis_storage: RedisStorage
    telegram_server: TelegramServer
    system: System_type



def load_bot_config(path) -> Config:
    env: Env = Env()
    env.read_env(path)
    bot = TelegramBot(
        tg_bot_token=env('TELEGRAM_BOT_TOKEN')
    )
    telegram_server = TelegramServer(
        URI=env('DOCKER_TELEGRAM_SERVER_OYSIDE_ONE_LOCATION'),
    )
    open_ai_key = OpenAI_KEY(
        key=env('OPENAI_API_KEY'))

    return Config(
        system=System_type(system_type=env('SYSTEM')),
        Bot=bot,
        ChatGPT=open_ai_key,
        telegram_server=telegram_server,
        data_base=MongoDB(bd_name=env('DATABASE'),
                          local_port=env('MONGO_DB_LOCAL_PORT'),
                          local_host=env('MONGO_DB_LOCAL_HOST'),
                          docker_port=(env('MONGO_DB_DOCKER_PORT')),
                          docker_host=(env('MONGO_DB_DOCKER_HOST')),
                          ),
        redis_storage=(RedisStorage(
            main_bot_local_port=env('REDIS_MAIN_BOT_LOCAL_PORT'),
            main_bot_local_host=env('REDIS_MAIN_BOT_LOCAL_HOST'),

            main_bot_docker_port=env('REDIS_MAIN_BOT_DOCKER_PORT'),
            main_bot_docker_host=env('REDIS_MAIN_BOT_DOCKER_HOST'),

        )
        )
    )
