import asyncio
from insiht_bot_container import config_data

from aiogram import Bot, Dispatcher


async def logout_bot():
    config = config_data
    bot = Bot(token=config.Bot.tg_bot_token)
    try:
        await bot.log_out()
        print("Бот успешно отключен от официального сервера Telegram.")
    except Exception as e:
        print(f"Произошла ошибка: {e}")
    finally:
        await bot.session.close()


if __name__ == '__main__':
    asyncio.run(logout_bot())
