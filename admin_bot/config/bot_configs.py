from typing import Union

from environs import Env
from dataclasses import dataclass



@dataclass
class AdminTelegramBot:
    tg_bot_token: str


@dataclass
class MongoDB:
    bd_name: str
    # для пользования на локальной машине
    local_port: int
    local_host: Union[int, str]
    # для пользования на сервере в доккере
    docker_port: int
    docker_host: Union[int, str]


@dataclass
class RedisStorage:
    # для пользования на локальной машине

    admin_bot_local_port: int
    admin_bot_local_host: Union[int, str]
    # для пользования на сервере в доккере

    admin_bot_docker_port: int
    admin_bot_docker_host: Union[int, str]

@dataclass
class System_type:
    system_type: str

@dataclass
class Config:
    data_base: MongoDB
    redis_storage: RedisStorage
    AdminBot: AdminTelegramBot
    system: System_type


def load_bot_config(path) -> Config:
    env: Env = Env()
    env.read_env(path)


    return Config(
        system=System_type(system_type=env('SYSTEM')),
        AdminBot=AdminTelegramBot(tg_bot_token=env('ADMIN_TELEGRAM_BOT_TOKEN')),
        data_base=MongoDB(bd_name=env('DATABASE'),
                          local_port=env('MONGO_DB_LOCAL_PORT'),
                          local_host=env('MONGO_DB_LOCAL_HOST'),
                          docker_port=(env('MONGO_DB_DOCKER_PORT')),
                          docker_host=(env('MONGO_DB_DOCKER_HOST')),
                          ),
        redis_storage=(RedisStorage(

            admin_bot_local_port=env('REDIS_ADMIN_BOT_LOCAL_PORT'),
            admin_bot_local_host=env('REDIS_ADMIN_BOT_LOCAL_HOST'),

            admin_bot_docker_port=env('REDIS_ADMIN_BOT_DOCKER_PORT'),
            admin_bot_docker_host=env('REDIS_ADMIN_BOT_DOCKER_HOST'),
        )
        )
    )
