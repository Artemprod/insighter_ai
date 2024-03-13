from environs import Env
from loguru import logger
from notifiers.logging import NotificationHandler
from logtail import LogtailHandler


def load_loguru():
    env: Env = Env()
    env.read_env('.env')
    LOGTAIL_SOURCE_TOKEN = env('LOGTAIL_INSIGTER_SOURCE')

    ALLERT_BOT_TOKEN = env('LOGER_BOT_TOKEN')
    TELEGRAM_NOTIFIERS_CHAT_IDS = [int(chat_id) for chat_id in env('TELEGRAM_CHAT_IDS').split(',')]

    for chat_id in TELEGRAM_NOTIFIERS_CHAT_IDS:
        params = {
            "token": ALLERT_BOT_TOKEN,
            "chat_id": chat_id,

        }

        logger.add(NotificationHandler("telegram", defaults=params),  level="ERROR")

    logtail_handler = LogtailHandler(source_token=LOGTAIL_SOURCE_TOKEN)
    logger.add(
        logtail_handler,
        format="{message}",
        level="INFO",
        backtrace=False,
        diagnose=False,
    )

    #
    # logger.add("debug.json", format="{time} {level} {message}", level="DEBUG",
    #            rotation="9:00", compression="zip", serialize=True)
    return logger


insighter_logger = load_loguru()

if __name__ == '__main__':

    def divide(a, b):
        insighter_logger.info('Старт функции', divide.__name__)
        return a / b


    def main():
        insighter_logger.info('Старт функции', main.__name__)
        try:
            divide(1, 0)
        except ZeroDivisionError:
            insighter_logger.exception("Деление на нноль")


    main()