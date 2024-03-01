from mongoengine import Document, StringField, DateTimeField, IntField, DictField, ListField, DecimalField, FloatField, \
    BooleanField


class Assistant(Document):
    assistant_id = StringField()
    assistant = StringField()
    name = StringField()
    button_name = StringField()
    assistant_prompt = StringField()
    user_prompt = StringField()
    user_prompt_for_chunks = StringField()
    created_at = DateTimeField()

    meta = {
        'collection': 'assistants'  # Здесь указывается имя коллекции
    }


class User(Document):
    tg_username = StringField()
    tg_link = StringField()
    name = StringField()
    tg_id = IntField()
    money_balance = DecimalField()
    time_balance = FloatField()
    attempts = IntField()
    documents = DictField()
    registration_date = DateTimeField()
    payment_history = DictField()
    assistant_call = ListField()
    document_current_page = IntField()

    meta = {
        'collection': 'Users'  # Здесь указывается имя коллекции
    }


class Transactions(Document):
    tg_user_id = IntField(required=True)  # ID пользователя в Telegram
    name = StringField(max_length=255, required=True)  # Имя пользователя
    amount = DecimalField(required=True)  # Сумма пополнения
    tariff = StringField(max_length=255, required=True)  # Тариф
    date = DateTimeField(required=True)  # Дата пополнения
    status = BooleanField(required=True)  # Статус (True - успешно, False - ошибка)
    currency = StringField(max_length=3, required=True)  # Валюта
    invoice_payload = StringField()  # Данные, отправленные в поле `payload` при инициализации платежа
    provider_payment_charge_id = StringField()  # ID платежа в системе платежного провайдера
    telegram_payment_charge_id = StringField()  # ID платежа в Telegram
    meta = {
        'collection': 'Transactions',  # Здесь указывается имя коллекции
    }


class Tariff(Document):
    tariff_name = StringField()
    label = StringField()
    currency = StringField()
    price = DecimalField()
    minutes = IntField()

    meta = {
        'collection': 'Tariffs'  # Здесь указывается имя коллекции
    }


