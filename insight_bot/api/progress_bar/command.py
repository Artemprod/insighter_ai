import aiohttp
from aiohttp import ClientConnectorError
from environs import Env


class ProgressBarClient:
    def __init__(self):
        self.server_url = self.__load_server_url()

    async def start(self, chat_id: int, time: int, process_name: str):
        data = {"chat_id": chat_id, "time": time, "process_name": process_name}
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(f"{self.server_url}/start", json=data) as response:
                    return await response.json()
            except ClientConnectorError:
                return 500

    async def stop(self, chat_id: int):
        data = {"chat_id": chat_id}
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(f"{self.server_url}/abort", json=data) as response:
                    return await response.json()
            except ClientConnectorError:
                return 500

    @staticmethod
    def __load_server_url():
        env = Env()
        env.read_env()
        return env("PROGRESS_BAR_SERVER_URL")
