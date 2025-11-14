from typing import List

from pymongo import MongoClient
from mc import config

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


def mongodb_results_to_json(results: List[dict], strip_id=True) -> List[dict]:
    json_results = []
    for doc in results:
        if strip_id and "_id" in doc:
            doc.pop("_id")
        elif "_id" in doc:
            doc["_id"] = str(doc["_id"])  # Convert ObjectId to string
        json_results.append(doc)
    return json_results


def mongodb_result_to_json(result: dict, strip_id=True) -> dict:
    if result and "_id" in result:
        if strip_id and "_id" in result:
            result.pop("_id")
        elif "_id" in result:
            result["_id"] = str(result["_id"])  # Convert ObjectId to string
    return result