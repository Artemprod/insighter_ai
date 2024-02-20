from DB.Mongo.mongo_db import MongoORMConnection, MongoAssistantRepositoryORM
from config.bot_configs import load_bot_config, Config

config_data: Config = load_bot_config('.env')
MongoORMConnection(config_data.data_base, system_type=config_data.system.system_type)
assistant_repository = MongoAssistantRepositoryORM()
