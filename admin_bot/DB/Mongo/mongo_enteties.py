from mongoengine import Document, StringField, DateTimeField, IntField, DictField, ListField, DecimalField, FloatField


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
    name = StringField()
    tg_id = IntField()
    money_balance = DecimalField()
    time_balance = FloatField()
    attempts = IntField()
    documents = DictField()
    registration_date = DateTimeField()
    payment_history = DictField()
    assistant_call = ListField()
    meta = {
        'collection': 'Users'  # Здесь указывается имя коллекции
    }

