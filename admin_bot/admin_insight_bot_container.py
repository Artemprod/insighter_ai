from DB.Mongo.mongo_db import MongoORMConnection, MongoAssistantRepositoryORM
from config.bot_configs import load_bot_config, Config

config_data: Config = load_bot_config('.env')
MongoORMConnection(config_data.data_base)
assistant_repository = MongoAssistantRepositoryORM()