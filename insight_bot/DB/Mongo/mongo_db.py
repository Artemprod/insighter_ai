import asyncio
import datetime
import hashlib
import logging
import os
import random

from environs import Env
from mongoengine import connect
from DB.Mongo.mongo_enteties import Assistant, User, Tariff, Transactions
from config.bot_configs import MongoDB


from lexicon.LEXICON_RU import TARIFFS
from logging_module.log_config import insighter_logger


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


# TODO переписать все асинхронно с использованием асинхронной библиотекк mongoengine
class MongoAssistantRepositoryORM:

    @staticmethod
    def get_all_assistants():
        return Assistant.objects()

    @staticmethod
    async def get_one_assistant(assistant_id: str):
        return Assistant.objects(assistant_id=assistant_id).get()

    @staticmethod
    async def get_assistant_name(assistant_id: str) -> str:
        assistant = Assistant.objects(assistant_id=assistant_id).get()
        return assistant.assistant

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

    # TODO вынести количесвто попыток при старте в конфиги
    @staticmethod
    async def save_new_user(tg_username,
                            name,
                            tg_id,
                            tg_link,
                            attempts=3,
                            money=0,
                            seconds=6000):
        new_user: User = User(
            tg_username=tg_username,
            tg_link=tg_link,
            name=name,
            tg_id=tg_id,
            attempts=attempts,
            money_balance=money,
            time_balance=seconds,
            documents={},
            registration_date=datetime.datetime.now(),
            payment_history={f'{datetime.datetime.now()}': 0},
        )

        try:
            new_user.save()
            insighter_logger.info(f'Новый пользователь сохранен в базе {tg_username}, {name}, {tg_id}')
        except Exception as e:
            insighter_logger.exception(f"Ошибка в сохранение нового пользователя {tg_username}, {name}, {tg_id}: {e}")


    @staticmethod
    def add_attempts(tg_id,
                     new_value):
        user: User = User.objects(tg_id=tg_id).get()
        user.attempts = new_value
        try:
            user.save()
            insighter_logger.info(f'Попытки добавлены для {user.tg_username}, {user.name}, {user.tg_id}')

        except Exception as e:
            insighter_logger.exception(f"Ошибка в обновлении попыток {user.tg_username}, {user.name}, {user.tg_id}: {e}")


    @staticmethod
    async def delete_one_attempt(tg_id):
        user: User = User.objects(tg_id=tg_id).get()
        if user.attempts != 0:
            user.attempts -= 1
            try:
                user.save()
                insighter_logger.info(f'Попытка вычтена {user.tg_username}, {user.name}, {user.tg_id}')

            except Exception as e:
                insighter_logger.exception(f"Ошибка в вычитаниее попыток {user.tg_username}, {user.name}, {user.tg_id}: {e}")

        else:
            insighter_logger.info(f'0 попыток нужно дбавить  {user.tg_username}, {user.name}, {user.tg_id}')

            return None

    @staticmethod
    async def add_assistant_call_to_user(user_tg_id,
                                         assistant_name):
        user: User = User.objects(tg_id=user_tg_id).get()
        data = {'assistant': assistant_name,
                'date': datetime.datetime.now().strftime("%Y-%m-%d, %H:%M")}
        try:
            user.assistant_call.append(data)
            user.save()
        except Exception as e:
            insighter_logger.exception(e, "cant save assistant name")


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

    async def create_new_doc(self,
                             tg_id) -> str:
        document = {
            "date": datetime.datetime.now().strftime("%d_%B_%Y_%H_%M_%S"),
        }
        doc_id = await self.generate_new_doc_id()
        user: User = User.objects(tg_id=tg_id).get()
        user.documents.setdefault(doc_id, document)
        try:
            user.save()
            insighter_logger.info(f"Новый документ {doc_id} создан")
            return doc_id
        except Exception as e:
            insighter_logger.exception(e)
            raise  # Пробрасываем исключение

    @staticmethod
    async def save_new_transcribed_text(tg_id,
                                        doc_id,
                                        transcribed_text):
        user: User = User.objects(tg_id=tg_id).get()
        doc = user.documents.get(doc_id)
        if doc is None:
            raise ValueError(f"Документ с ID {doc_id} не найден")
        doc['transcription'] = transcribed_text
        try:
            user.save()
            insighter_logger.info("Транскрибированный текст сохранен")
        except Exception as e:
            insighter_logger.exception(e)
            raise

    @staticmethod
    async def add_meta_information(tg_id,
                                   doc_id,
                                   info: dict):
        user: User = User.objects(tg_id=tg_id).get()
        doc = user.documents.get(doc_id)
        if doc is None:
            raise ValueError(f"Документ с ID {doc_id} не найден")
        doc['meta_data'] = info
        try:
            user.save()
            insighter_logger.info("Транскрибированный текст сохранен")
        except Exception as e:
            insighter_logger.exception(e)
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
            insighter_logger.info("Саммари текст сохранен")
        except Exception as e:
            insighter_logger.exception(e)
            raise

    @staticmethod
    async def generate_new_doc_id(length=20):
        if length > 20 or length < 1:
            raise ValueError("Length must be between 1 and 20")
        random_bytes = os.urandom(16)
        hash_object = hashlib.sha256(random_bytes)
        return hash_object.hexdigest()[:length]

    @staticmethod
    async def update_user_page(tg_id: int,
                               current_page: int):
        user: User = User.objects(tg_id=tg_id).get()
        user.document_current_page = current_page
        try:
            user.save()
        except Exception as e:
            insighter_logger.exception(f"failed to update current doc page {e}")


class UserBalanceRepoORM:
    @staticmethod
    async def get_user_money_balance(tg_id):
        user: User = User.objects(tg_id=tg_id).get()
        balance = user.money_balance
        return balance

    @staticmethod
    async def get_user_time_balance(tg_id):
        user: User = User.objects(tg_id=tg_id).get()
        balance = user.time_balance
        return balance

    @staticmethod
    async def add_user_time_balance(tg_id,
                                    time):
        user: User = User.objects(tg_id=tg_id).get()
        user.time_balance += time
        user.time_balance = round(user.time_balance)
        user.save()

    @staticmethod
    async def update_time_balance(tg_id,
                                  time_to_subtract):
        user: User = User.objects(tg_id=tg_id).get()
        user.time_balance -= time_to_subtract
        user.time_balance = round(user.time_balance)
        user.save()

    @staticmethod
    async def add_user_money_balance(tg_id,
                                     money):
        user: User = User.objects(tg_id=tg_id).get()
        user.money_balance += money
        user.save()

    @staticmethod
    async def money_to_minutes(amount, exchange_rate=1):
        """
        Конвертирует деньги в минуты по заданному курсу обмена.

        Args:
            amount (float): Количество денег для конвертации.
            exchange_rate (float): Курс обмена денег на минуты. По умолчанию равен 1.

        Returns:
            int: Количество минут, полученное в результате конвертации.
        """

        return int(amount * exchange_rate)


class TariffRepoORM:
    @staticmethod
    async def get_tariff_price_by_name(tariff_name: str):
        tariff: Tariff = Tariff.objects(tariff_name=tariff_name).get()
        return tariff.price

    @staticmethod
    async def get_tariff_info_by_name(tariff_name: str) -> Tariff:
        tariff: Tariff = Tariff.objects(tariff_name=tariff_name).get()
        return tariff

    # TODO: поиск по тарифам не очивилдный оптимизхировать. По какомуц параметру определяются тарифы?
    @staticmethod
    async def get_base_tariff() -> Tariff:
        tariff: Tariff = Tariff.objects(tariff_name=TARIFFS['base']).get()
        return tariff

    @staticmethod
    async def get_standard_tariff() -> Tariff:
        tariff: Tariff = Tariff.objects(tariff_name=TARIFFS['standard']).get()
        return tariff

    @staticmethod
    async def get_premium_tariff() -> Tariff:
        tariff: Tariff = Tariff.objects(tariff_name=TARIFFS['premium']).get()
        return tariff

    @staticmethod
    async def add_new_tariff(tariff_name,
                             label,
                             price,
                             minutes,
                             currency):
        tariff = Tariff(
            tariff_name=tariff_name,
            currency=currency,
            label=label,
            price=price,
            minutes=minutes,
        )
        tariff.save()


class TransactionRepoORM:
    @staticmethod
    async def create_transaction_from_successful_payment(
            tg_user_id,
            name,
            amount,
            tariff,

            status,
            currency,
            invoice_payload,
            provider_payment_charge_id,
            telegram_payment_charge_id) -> Transactions:
        """
        Функция создаёт объект транзакции из данных успешного платежа.

        Args:
            telegram_payment_charge_id:
            provider_payment_charge_id:
            invoice_payload:
            currency:
            status:
            tariff:
            amount:
            name:
            tg_user_id:
            payment_id:
            date:

        Returns:
            Объект `Transactions` для записи в базу данных.
        """

        return Transactions(
            tg_user_id=tg_user_id,
            name=name,
            amount=amount,
            tariff=tariff,
            date=datetime.datetime.now(),
            status=status,
            currency=currency,
            invoice_payload=invoice_payload,
            provider_payment_charge_id=provider_payment_charge_id,
            telegram_payment_charge_id=telegram_payment_charge_id,
        )

    async def save_transaction(self,
                               tg_user_id,
                               name,
                               amount,
                               tariff,
                               status,
                               currency,
                               invoice_payload,
                               provider_payment_charge_id,
                               telegram_payment_charge_id, ):
        try:
            transaction = await self.create_transaction_from_successful_payment(tg_user_id=tg_user_id,
                                                                                name=name,
                                                                                amount=amount,
                                                                                tariff=tariff,
                                                                                status=status,
                                                                                currency=currency,
                                                                                invoice_payload=invoice_payload,
                                                                                provider_payment_charge_id=provider_payment_charge_id,
                                                                                telegram_payment_charge_id=telegram_payment_charge_id
                                                                                )
        except Exception as e:
            insighter_logger.exception(f'Failed to form transaction object {e}')
            raise e
        try:
            transaction.save()
        except Exception as e:
            insighter_logger.exception(f"failed to save transaction {e}")
            raise e


if __name__ == '__main__':
    async def main():
        env: Env = Env()
        env.read_env('.env')

        bd = MongoDB(bd_name=env('DATABASE'),
                     local_port=env('MONGO_DB_LOCAL_PORT'),
                     local_host=env('MONGO_DB_LOCAL_HOST'),
                     docker_port=(env('MONGO_DB_DOCKER_PORT')),
                     docker_host=(env('MONGO_DB_DOCKER_HOST')),
                     )
        MongoORMConnection(bd, system_type='local')
        # a = TariffRepoORM()
        # await a.add_new_tariff(
        #     tariff_name='base',
        #     label='Базовый тариф',
        #     price=990,
        #     minutes=200,
        #     currency='RUB',
        # )



    asyncio.run(main())

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
