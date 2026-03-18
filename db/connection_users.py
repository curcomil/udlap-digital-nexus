from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
import os

load_dotenv()
uri = os.getenv("MONGODB_URI")


class MongoDBConnection_Users:
    def __init__(self, db_name: str, collection_name: str):
        # Comentar server_api si se usa MongoLocal
        self.client = MongoClient(uri, server_api=ServerApi("1"))
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]

    def get__users(self):
        result = list(self.collection.find({}))
        return result
