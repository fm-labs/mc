import shutil
import time
import uuid

from orchestra.ansible.record import insert_ansible_run_record, update_ansible_run_record
from orchestra.ansible.runner import run_ansible_playbook, KoAnsibleRunModel
from orchestra.project import build_ansible_runner_structure


def ko_playbook_run(project: str, playbook: str, **kwargs):
    run_id = str(uuid.uuid4())
    cleanup = kwargs.pop("cleanup", False)
    if not playbook.endswith(".yml"):
        playbook = playbook + ".yml"

    # create a temporary directory for ansible runner
    private_data_dir = build_ansible_runner_structure(project)
    print(f"[{run_id}] Private data dir: {private_data_dir}")

    # create ansible job in MongoDB
    ansible_run = insert_ansible_run_record(run_id, project=project, playbook=playbook)

    # execute playbook
    # during playbook execution, the ansible job status is updated in MongoDB (multiple times)
    print(
        f"[{run_id}] Running playbook {playbook} in context {project} with run ID {run_id} and private data dir {private_data_dir}")
    runner = run_ansible_playbook(run_id=run_id,
                                  private_data_dir=private_data_dir,
                                  playbook=playbook,
                                  **kwargs)

    # parse the ansible-runner result
    events = []
    for event in runner.events:
        print("Event: ", event)
        events.append(event)
        # if event.get('event') == 'runner_on_ok':
        #     task_result = {
        #         'job_id': job_id,
        #         'task_name': event['event_data'].get('task'),
        #         'host': event['event_data'].get('host'),
        #         'status': event['event'],
        #         'stdout': event['stdout'],
        #         'event_data': event['event_data'],
        #     }
        #     results.append(task_result)

    ansible_run.status = runner.status
    ansible_run.rc = runner.rc
    ansible_run.stdout = runner.stdout.read()
    ansible_run.stderr = runner.stderr.read()
    ansible_run.events = events
    ansible_run.stats = runner.stats
    ansible_run.finished_at = time.time()

    # update the run record and store the result in MongoDB
    update_ansible_run_record(ansible_run)

    # Remove the temporary ansible runner structure
    if cleanup:
        try:
            shutil.rmtree(private_data_dir, ignore_errors=False)
        except OSError as e:
            print(f"[{run_id}] Error while cleanup: {private_data_dir} : {e.strerror}")
            # shutil.rmtree(private_data_dir, ignore_errors=True)

    return ansible_run
