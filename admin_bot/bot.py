# _____ADMIN BOT
import asyncio
import os.path

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage, Redis
from handlers import command_handler, user_handler
from admin_insight_bot_container import assistant_repository, config_data
from keyboards.main_menu import set_main_menu


async def main() -> None:
    root_dir = os.path.normpath(os.path.abspath(os.path.dirname(__file__)))
    config = config_data

    redis = Redis(host=config.redis_storage.admin_bot_docker_host,
                  port=config.redis_storage.admin_bot_docker_port)
    storage: RedisStorage = RedisStorage(redis=redis)

    bot: Bot = Bot(token=config.AdminBot.tg_bot_token, parse_mode='HTML')

    # Добовляем хэгдлеры в диспечтер через роутеры
    dp: Dispatcher = Dispatcher(storage=storage,
                                 root_dir=root_dir,
                                assistant_repository=assistant_repository)
    dp.include_router(command_handler.router)
    dp.include_router(user_handler.router)
    await set_main_menu(bot)
    await bot.delete_webhook(drop_pending_updates=True)

    # Запускаем прослушку бота
    await dp.start_polling(bot)


if __name__ == '__main__':
    # Запускаем бота
    asyncio.run(main())
