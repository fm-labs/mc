from pymongo import MongoClient
from kloudia import config

mongo: MongoClient | None = None

def get_mongo_client():
    global mongo
    if mongo is not None:
        return mongo

    mongodb_uri = config.MONGODB_URL
    if not mongodb_uri:
        raise ValueError("MONGODB_URL is not set in environment variables.")

    mongo = MongoClient(mongodb_uri)
    return mongo


def get_mongo_collection(db_name: str, collection_name: str):
    _mongo = get_mongo_client()
    return _mongo[db_name][collection_name]
