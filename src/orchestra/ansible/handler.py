
def ko_ansible_artifacts_handler(artifacts_dir):
    # Do something here
    print(artifacts_dir)



def ko_ansible_status_handler(data, runner_config):
    """
    A function passed to __init__ of Runner and to the ansible_runner.interface.run() interface functions.
    This function will be called any time the status changes, expected values are:

    - starting: Preparing to start but hasn’t started running yet
    - running: The Ansible task is running
    - canceled: The task was manually canceled either via callback or the cli
    - timeout: The timeout configured in Runner Settings was reached (see env/settings - Settings for Runner itself)
    - failed: The Ansible process failed
    - successful: The Ansible process succeeded

    @see https://ansible.readthedocs.io/projects/runner/en/stable/python_interface/#runner-status-handler

    :param data:
    :param runner_config:
    :return:
    """
    print("STATUSHANDLER", data)

    # todo Update the status of the task in the database
    # todo Publish the status to redis pub/sub


def ko_ansible_event_handler(data):
    """
    A function passed to __init__ of :class:Runner <ansible_runner.runner.Runner>,
    this is invoked every time an Ansible event is received.
    You can use this to inspect/process/handle events as they come out of Ansible.
    This function should return True to keep the event, otherwise it will be discarded.

    @see https://ansible.readthedocs.io/projects/runner/en/stable/python_interface/#runner-event-handler

    :param data:
    :return:
    """
    print("EVENTHANDLER", data)

    # todo Store the event of the task in the database
    # todo Publish the event to redis pub/sub
    return True
