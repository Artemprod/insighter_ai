import datetime
import hashlib
import logging
import os
import random
from mongoengine import connect
from DB.Mongo.mongo_enteties import Assistant, User


class MongoORMConnection:
    def __init__(self, mongo, system_type):
        system_type = system_type
        if system_type == "local":
            connect(db=mongo.bd_name,
                    host=mongo.local_host,
                    port=int(mongo.local_port))
        elif system_type == "docker":
            connect(db=mongo.bd_name,
                    host=mongo.docker_host,
                    port=int(mongo.local_port))



#TODO переписать все асинхронно с использованием асинхронной библиотекк mongoengine
class MongoAssistantRepositoryORM:

    @staticmethod
    def get_all_assistants():
        return Assistant.objects()

    @staticmethod
    async def get_one_assistant(assistant_id: str):
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


class MongoUserRepoORM:
    @staticmethod
    async def get_user_attempts(tg_id):
        user: User = User.objects(tg_id=tg_id).get()
        attempts = user.attempts
        return attempts

    @staticmethod
    async def check_user_in_db(tg_id):
        return User.objects(tg_id=tg_id).first() is not None

    @staticmethod
    async def save_new_user(tg_username,
                            name,
                            tg_id,
                            attempts=3):
        new_user: User = User(
            tg_username=tg_username,
            name=name,
            tg_id=tg_id,
            attempts=attempts,
            documents={},
            registration_date=datetime.datetime.now(),
            payment_history={f'{datetime.datetime.now()}': 0},
        )
        print()
        try:
            new_user.save()
            logging.info(f'Новый пользователь сохранен в базе {tg_username}, {name}, {tg_id}')
            print(f'Новый пользователь сохранен в базе {tg_username}, {name}, {tg_id}')
        except Exception as e:
            logging.error(e, f"Ошибка в сохранение новго пользователя {tg_username}, {name}, {tg_id}")
            print(e, f"Ошибка в сохранение новго пользователя {tg_username}, {name}, {tg_id}")

    @staticmethod
    def add_attempts(tg_id, new_value):
        user: User = User.objects(tg_id=tg_id).get()
        user.attempts = new_value
        try:
            user.save()
            logging.info(f'Попытки добавлены для {user.tg_username}, {user.name}, {user.tg_id}')
            print(f'Попытки добавлены для {user.tg_username}, {user.name}, {user.tg_id}')
        except Exception as e:
            logging.error(e, f"Ошибка в обновлении попыток {user.tg_username}, {user.name}, {user.tg_id}")
            print(e, f"Ошибка в обновлении попыток  {user.tg_username}, {user.name}, {user.tg_id}")

    @staticmethod
    async def delete_one_attempt(tg_id):
        user: User = User.objects(tg_id=tg_id).get()
        if user.attempts != 0:
            user.attempts -= 1
            try:
                user.save()
                logging.info(f'Попытка вычтена {user.tg_username}, {user.name}, {user.tg_id}')
                print(f'Попытка вычтена {user.tg_username}, {user.name}, {user.tg_id}')
            except Exception as e:
                logging.error(e, f"Ошибка в вычитаниее попыток {user.tg_username}, {user.name}, {user.tg_id}")
                print(e, f"Ошибка в вычитаниее попыток {user.tg_username}, {user.name}, {user.tg_id}")
        else:
            logging.info(f'0 попыток нужно дбавить  {user.tg_username}, {user.name}, {user.tg_id}')
            print(f'0 попыток нужно дбавить {user.tg_username}, {user.name}, {user.tg_id}')
            return None


class UserDocsRepoORM:
    @staticmethod
    async def get_all_users_docs(tg_id):
        user: User = User.objects(tg_id=tg_id).get()
        docks = user.documents
        if len(docks) > 0:
            return docks

    @staticmethod
    async def get_doc_by_date(tg_id, date) -> dict:
        user: User = User.objects(tg_id=tg_id).get()
        docks = user.documents
        return docks.get(f'{date}', 'по этой дате ничего нету')

    @staticmethod
    def check_docs_in_user(tg_id):
        user: User = User.objects(tg_id=tg_id).get()
        docks = user.documents
        return len(docks) > 0

    @staticmethod
    async def load_doc_by_id(tg_id: int, doc_id: str):
        user: User = User.objects(tg_id=tg_id).get()
        doc = user.documents.get(doc_id)
        if doc is None:
            raise ValueError(f"Документ с ID {doc_id} не найден")
        return doc

    async def create_new_doc(self, tg_id) -> str:
        document = {
            "date": datetime.datetime.now().strftime("%d_%B_%Y_%H_%M_%S"),
        }
        doc_id = await self.generate_new_doc_id()
        user: User = User.objects(tg_id=tg_id).get()
        user.documents.setdefault(doc_id, document)
        try:
            user.save()
            logging.info(f"Новый документ {doc_id} создан")
            return doc_id
        except Exception as e:
            logging.error(e)
            raise  # Пробрасываем исключение

    @staticmethod
    async def save_new_transcribed_text(tg_id, doc_id, transcribed_text):
        user: User = User.objects(tg_id=tg_id).get()
        doc = user.documents.get(doc_id)
        if doc is None:
            raise ValueError(f"Документ с ID {doc_id} не найден")
        doc['transcription'] = transcribed_text
        try:
            user.save()
            logging.info("Транскрибированный текст сохранен")
        except Exception as e:
            logging.error(e)
            raise

    @staticmethod
    async def load_transcribed_text(tg_id, doc_id):
        user: User = User.objects(tg_id=tg_id).get()
        doc: dict = user.documents.get(doc_id)
        if doc is None:
            raise ValueError(f"Документ с ID {doc_id} не найден")
        transcribed_text = doc.get('transcription', None)
        if transcribed_text is None:
            raise ValueError(f"Документ с ID {doc_id} не найден")
        return transcribed_text

    @staticmethod
    async def save_new_summary_text(tg_id, doc_id, summary_text):
        user: User = User.objects(tg_id=tg_id).get()
        doc = user.documents.get(doc_id)
        if doc is None:
            raise ValueError(f"Документ с ID {doc_id} не найден")
        doc['summary'] = summary_text
        try:
            user.save()
            logging.info("Саммари текст сохранен")
        except Exception as e:
            logging.error(e)
            raise

    @staticmethod
    async def generate_new_doc_id(length=20):
        if length > 20 or length < 1:
            raise ValueError("Length must be between 1 and 20")
        random_bytes = os.urandom(16)
        hash_object = hashlib.sha256(random_bytes)
        return hash_object.hexdigest()[:length]


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
