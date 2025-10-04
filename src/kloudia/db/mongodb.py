from pymongo import MongoClient
from kloudia import config

mongo: MongoClient | None = None

def get_global_mongo_client() -> MongoClient:
    global mongo
    if mongo is None:
        mongo = get_mongo_client()
    return mongo


def get_mongo_client(ping: bool = False) -> MongoClient:
    mongodb_uri = config.MONGODB_URL
    if not mongodb_uri:
        raise ValueError("MONGODB_URL is not set in environment variables.")

    client = MongoClient(mongodb_uri)
    if ping:
        try:
            # The ismaster command is cheap and does not require auth.
            client.admin.command('ismaster')
        except Exception as e:
            raise ConnectionError(f"Could not connect to MongoDB: {e}")
    return client


def get_mongo_collection(db_name: str, collection_name: str):
    _mongo = get_mongo_client()
    return _mongo[db_name][collection_name]
