import asyncio
import os.path

from aiogram import Bot, Dispatcher

from aiogram.client.telegram import TelegramAPIServer
from aiogram.fsm.storage.redis import RedisStorage
from redis import Redis
from handlers import command_handler, docs_handlers, process_file_handler
from insiht_bot_container import assistant_repository, config_data, user_repository, document_repository, progress_bar, \
    queue_pipeline, pipeline_process

from keyboards.main_menu import set_main_menu
from aiogram.client.session.aiohttp import AiohttpSession

from midleware.attempts import CheckAttemptsMiddleware


async def create_bot() -> None:
    root_dir = os.path.normpath(os.path.abspath(os.path.dirname(__file__)))

    config = config_data
    session = AiohttpSession(
        api=TelegramAPIServer.from_base(config.telegram_server.URI)
    )

    redis = Redis(host=config.redis_storage.main_bot_docker_host,
                  port=config.redis_storage.main_bot_docker_port)
    storage: RedisStorage = RedisStorage(redis=redis)

    bot: Bot = Bot(token=config.Bot.tg_bot_token, parse_mode='HTML', session=session)

    # Добовляем хэгдлеры в диспечтер через роутеры
    dp: Dispatcher = Dispatcher(storage=storage,
                                root_dir=root_dir,
                                assistant_repository=assistant_repository,
                                user_repository=user_repository,
                                document_repository=document_repository,
                                process_queue=queue_pipeline,
                                progress_bar=progress_bar,
                                )

    dp.include_router(command_handler.router)
    dp.include_router(process_file_handler.router)
    dp.include_router(docs_handlers.router)
    dp.update.outer_middleware(CheckAttemptsMiddleware(user_repository=user_repository))

    await set_main_menu(bot)
    await bot.delete_webhook(drop_pending_updates=True)
    # Запускаем прослушку бота
    await dp.start_polling(bot)


async def create_pipline_processes() -> None:
    await pipeline_process.run_process()


async def main():
    bot_task = asyncio.create_task(create_bot())
    pipline_task = asyncio.create_task(create_pipline_processes())
    await bot_task
    await pipline_task

if __name__ == '__main__':
    # Запускаем бота
    asyncio.run(main())
