from pymongo import MongoClient

from orchestra import settings

mongo: MongoClient | None = None

def init_mongo():
    global mongo
    if mongo is None:
        print("Initializing MongoDB", settings.MONGODB_URL)
        mongo = MongoClient(settings.MONGODB_URL)
    return mongo


def get_collection(collection_name: str):
    global mongo
    if mongo is None:
        init_mongo()
    return mongo['orchestra'][collection_name]


def get_ansible_runs_collection():
    return get_collection("ansible_runs")