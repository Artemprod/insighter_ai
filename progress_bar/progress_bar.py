import aiohttp
from aiogram.exceptions import TelegramRetryAfter
from environs import Env
import asyncio


class ProgressBar:
    def __init__(self, chat_id: int):
        self._bot_token = None
        self.chat_id = chat_id
        self.progress_message_id = None
        self.running = False
        self.__telegram_server_uri = self.__load_server_uri()

    async def start(self, process_name, time):
        if self.running:
            await self.send_message("Прогресс-бар уже запущен.")
            return

        self._bot_token = self._load_bot_token()
        self.running = True
        asyncio.create_task(self._progress_bar_task(process_name, time))

    async def abort(self):
        self.running = False

    async def _progress_bar_task(self, process_name, time):
        print('попал в таск прогрес бар процесс:', process_name)
        self.running = True
        total_seconds = time
        empty_bar_char = '▱'
        filled_bar_char = '▰'
        total_length = 18
        update_interval = 4  # Обновление каждые 4 секунды
        print('Перед открыием сессии')
        async with aiohttp.ClientSession() as self._http_session:
            print('Открытая сессия', self._http_session)
            for i in range(1, total_seconds + 1):
                print('кол-во времени на проес бар', total_seconds + 1 )
                if not self.running:
                    print('после отрктия сесии но прерывание')
                    break
                print('после отрктия сесии')
                if i % update_interval == 0 or i == total_seconds:
                    print("попал в цикл отправки прогресс бара ", i)
                    progress = (i / total_seconds) * 100
                    filled_length = int(total_length * progress / 100)
                    bar = filled_bar_char * filled_length + empty_bar_char * (total_length - filled_length)
                    progress_text = self.create_progress_text(process_name, time, bar, progress)

                    try:
                        print('Тут по идеи должны быть отправка сообщения ')
                        await self.send_message(progress_text)
                    except TelegramRetryAfter as e:
                        print(f"Flood limit exceeded. Waiting for 10 seconds.")
                        wait_time = getattr(e, 'timeout', 10)
                        i += wait_time
                        if i >= total_seconds:
                            break  # Прекращаем, если пауза превышает оставшееся время
                        progress = (i / total_seconds) * 100
                        filled_length = int(total_length * progress / 100)
                        bar = filled_bar_char * filled_length + empty_bar_char * (total_length - filled_length)
                        progress_text = self.create_progress_text(process_name, time, bar, progress)
                        await asyncio.sleep(wait_time)
                        await self.send_message(progress_text)  # Отправляем обновленный прогресс

                await asyncio.sleep(1)

            await self.delete_message()
            self.progress_message_id = None
            self.running = False
            print('прогресс бар остановился')

    def create_progress_text(self, process_name, time, bar, progress):
        return f"<b>Процесс:</b> <i>{process_name}</i>\n" \
               f"<b>Расчетное время:</b> <i>{round(time / 60, 2)} мин. </i>\n\n" \
               f"Прогресс: [{bar}] <b>{progress:.1f}%</b>"

    #TODO Переписать. передовать бот токен вместе с сообщением
    async def send_message(self, text: str):
        if not self._http_session:
            return
        await self._ensure_bot_token()
        url = f"{self.__telegram_server_uri}/bot{self._bot_token}/sendMessage" if self.progress_message_id is None else f"{self.__telegram_server_uri}/bot{self._bot_token}/editMessageText"
        print(self.chat_id)
        print(url)
        data = {"chat_id": self.chat_id, "text": text, "parse_mode": "HTML", "disable_notification": True}
        if self.progress_message_id:
            data["message_id"] = self.progress_message_id
            print(data["message_id"])

        try:
            print("функция send_message перед открытием сесии для отправки")
            async with self._http_session.post(url, data=data) as response:
                print('сессия в функции открвлась вот она :', response)
                if not self.progress_message_id and response.status == 200:
                    response_data = await response.json()
                    if response_data.get("ok"):
                        self.progress_message_id = response_data["result"]["message_id"]
        except Exception as e:
            print(f"Ошибка при отправке сообщения: {e}")

    async def delete_message(self):
        await self._ensure_bot_token()
        if self.progress_message_id:
            url = f"{self.__telegram_server_uri}/bot{self._bot_token}/deleteMessage"
            data = {"chat_id": self.chat_id, "message_id": self.progress_message_id}
            try:
                async with self._http_session.post(url, data=data) as response:
                    if response.status == 200:
                        self.progress_message_id = None
            except Exception as e:
                print(f"Ошибка при удалении сообщения: {e}")

    async def _ensure_bot_token(self):
        if not self._bot_token:
            self._bot_token = self._load_bot_token()

    @staticmethod
    def _load_bot_token():
        env = Env()
        env.read_env(".env")
        return env("BOT_TOKEN")

    @staticmethod
    def __load_server_uri():
        env = Env()
        env.read_env(".env")
        return env("DOCKER_TELEGRAM_SERVER")
