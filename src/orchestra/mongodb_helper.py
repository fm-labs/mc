from mc.db.mongodb import get_mongo_collection


def get_ansible_runs_collection():
    return get_mongo_collection("orchestra", "ansible_runs")


def get_celery_task_log_collection():
    return get_mongo_collection("orchestra", "celery_task_logs")
