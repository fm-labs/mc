import time

from orchestra.ansible.runner import KoAnsibleRunModel
from orchestra.storage.mongodb import get_ansible_runs_collection


def insert_ansible_run_record(run_id: str, project: str, playbook: str) -> KoAnsibleRunModel:
    """
    Initialize an Ansible run record in MongoDB.
    """

    collection = get_ansible_runs_collection()
    new_run = KoAnsibleRunModel(
        run_id=run_id,
        project_id=project,
        playbook=playbook,
        status="initialized",
        stdout=None,
        stderr=None,
        rc=None,
        events=[],
        stats={},
        created_at=time.time(),
        updated_at=time.time(),
        finished_at=None
    )

    print(f"[{run_id}] Created new run: {new_run}")
    collection.insert_one(new_run.model_dump())
    return new_run


def update_ansible_run_record(ansible_run: KoAnsibleRunModel):
    """
    Update an Ansible run record in MongoDB.
    """
    ansible_run.updated_at = time.time()

    get_ansible_runs_collection().update_one(
        {"run_id": ansible_run.run_id},
        {"$set": ansible_run.model_dump()},
        upsert=True)