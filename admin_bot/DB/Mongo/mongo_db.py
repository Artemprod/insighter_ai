import datetime
import hashlib

import os
import random
from mongoengine import connect
from DB.Mongo.mongo_enteties import Assistant, User



class MongoORMConnection:
    def __init__(self, mongo,
                 system_type):
        system_type = system_type
        if system_type == "local":
            connect(db=mongo.bd_name,
                    host=mongo.local_host,
                    port=int(mongo.local_port))
        elif system_type == "docker":
            connect(db=mongo.bd_name,
                    host=mongo.docker_host,
                    port=int(mongo.local_port))


class MongoAssistantRepositoryORM:

    @staticmethod
    def get_all_assistants():
        return Assistant.objects()

    @staticmethod
    def get_one_assistant(assistant_id: str):
        return Assistant.objects(assistant_id=assistant_id).get()

    def create_new_assistants(self, assistant: Assistant):
        as_id = self.generate_id()
        assistant.assistant_id = as_id
        assistant.created_at = datetime.datetime.now()
        try:
            assistant.save()
            print("Сохранено")
            return as_id
        except Exception as e:
            print('что то пошло не так при создании нового асистента ')
            return False

    @staticmethod
    def update_assistant_fild(assistant_id, assistant_fild, new_value):
        assistant_object: Assistant = Assistant.objects(assistant_id=assistant_id).get()
        assistant_object[assistant_fild] = new_value
        try:
            assistant_object.save()
            return True
        except Exception as e:
            print('что то пошло не так при изменение нового поля ')
            return False

    @staticmethod
    def delete_assistant(assistant_id: str):
        assistant_object: Assistant = Assistant.objects(assistant_id=assistant_id).get()
        try:
            assistant_object.delete()
            print("Удалено")
        except Exception as e:
            print('Ошибка удаления', e)

    @staticmethod
    def generate_id(length=10):
        if length > 10 or length < 1:
            raise ValueError("Length must be between 1 and 10")

        # Генерируем случайные байты
        random_bytes = os.urandom(16)

        # Создаем хеш объект SHA-256
        hash_object = hashlib.sha256(random_bytes)

        # Получаем хеш в виде шестнадцатеричной строки и усекаем ее до требуемой длины
        short_hash = hash_object.hexdigest()[:length]
        for _ in range(3):
            short_hash += str(random.randint(0, 9))
        return str(short_hash)


if __name__ == '__main__':
    # c = MongoORMConnection(config_data.data_base)
    # assistant = Assistant(
    #     assistant="product_manager",
    #     name="Асистент продатк менеджера",
    #     button_name="Инсайт по интервью",
    #     assistant_prompt="""Ты опытный senior product manager, который постоянно проводит и анализируем огромное количество проблемных интервью""",
    #     user_prompt="""Сейчас я пришлю файл с расшифровкой проблемного интервью. Твоя задача выделить самое важное из ответов респондента, составить список ключевых проблем пользователя, составить список инсайтов.  В конце необходимо составить саммари этого проблемного интервью.""",
    #     created_at=datetime.datetime.now(),
    # )
    #
    # assistant_2 = Assistant(
    #     assistant="product_manager",
    #     name="Асистент продатк менеджера",
    #     button_name="Инсайт по интервью",
    #     assistant_prompt="""Ты опытный senior product manager, который постоянно проводит и анализируем огромное количество проблемных интервью""",
    #     user_prompt="""Сейчас я пришлю файл с расшифровкой проблемного интервью. Твоя задача выделить самое важное из ответов респондента, составить список ключевых проблем пользователя, составить список инсайтов.  В конце необходимо составить саммари этого проблемного интервью.""",
    #     created_at=datetime.datetime.now(),
    # )
    # repo = MongoAssistantRepositoryORM()
    # repo.create_new_assistants(assistant)
    # repo.create_new_assistants(assistant_2)
    # repo.get_all_assistants()
    print()
