import uuid

import ansible_runner
from ansible_runner import Runner

from orchestra.ansible.handler import ko_ansible_status_handler, ko_ansible_event_handler
from orchestra.pubsub.publisher import start_publisher


def run_ansible_playbook(private_data_dir, playbook, run_id=None, **kwargs) -> Runner:
    """
    Run an Ansible playbook and return the results.

    See: https://ansible.readthedocs.io/projects/runner/en/stable/intro/#runner-input-directory-hierarchy

    The ansible runner expects the following directory structure:
    .
    ├── env
    │   ├── envvars
    │   ├── extravars
    │   ├── passwords
    │   ├── cmdline
    │   ├── settings
    │   └── ssh_key
    ├── inventory
    │   └── hosts
    └── project
        ├── test.yml
        └── roles
            └── testrole
                ├── defaults
                ├── handlers
                ├── meta
                ├── README.md
                ├── tasks
                ├── tests
                └── vars


    Tge ansible runner will create a directory structure like this:

    .
    ├── artifacts
    │   └── [identifier]

    .
    ├── artifacts
    │   └── 37f639a3-1f4f-4acb-abee-ea1898013a25
    │       ├── fact_cache
    │       │   └── localhost
    │       ├── job_events
    │       │   ├── 1-34437b34-addd-45ae-819a-4d8c9711e191.json
    │       │   ├── 2-8c164553-8573-b1e0-76e1-000000000006.json
    │       │   ├── 3-8c164553-8573-b1e0-76e1-00000000000d.json
    │       │   ├── 4-f16be0cd-99e1-4568-a599-546ab80b2799.json
    │       │   ├── 5-8c164553-8573-b1e0-76e1-000000000008.json
    │       │   ├── 6-981fd563-ec25-45cb-84f6-e9dc4e6449cb.json
    │       │   └── 7-01c7090a-e202-4fb4-9ac7-079965729c86.json
    │       ├── rc
    │       ├── status
    │       └── stdout


    Runner configuration

    :param str private_data_dir: The directory containing all runner metadata needed to invoke the runner module.
        Output artifacts will also be stored here for later consumption.
    :param str ident: The run identifier for this invocation of Runner. Will be used to create and name the artifact directory holding the results of the invocation.
    :param bool json_mode: Store event data in place of stdout on the console and in the stdout file
    :param str or list playbook: The playbook (either a list or dictionary of plays, or as a path relative to
                     ``private_data_dir/project``) that will be invoked by runner when executing Ansible.
    :param str module: The module that will be invoked in ad-hoc mode by runner when executing Ansible.
    :param str module_args: The module arguments that will be supplied to ad-hoc mode.
    :param str host_pattern: The host pattern to match when running in ad-hoc mode.
    :param str or dict or list inventory: Overrides the inventory directory/file (supplied at ``private_data_dir/inventory``) with
        a specific host or list of hosts. This can take the form of:

            - Path to the inventory file in the ``private_data_dir/inventory`` directory or
              an absolute path to the inventory file
            - Native python dict supporting the YAML/json inventory structure
            - A text INI formatted string
            - A list of inventory sources, or an empty list to disable passing inventory

    :param str role: Name of the role to execute.
    :param str or list roles_path: Directory or list of directories to assign to ANSIBLE_ROLES_PATH
    :param dict envvars: Environment variables to be used when running Ansible. Environment variables will also be
                    read from ``env/envvars`` in ``private_data_dir``
    :param dict extravars: Extra variables to be passed to Ansible at runtime using ``-e``. Extra vars will also be
                      read from ``env/extravars`` in ``private_data_dir``.
    :param dict passwords: A dictionary containing password prompt patterns and response values used when processing output from
                      Ansible. Passwords will also be read from ``env/passwords`` in ``private_data_dir``.
    :param dict settings: A dictionary containing settings values for the ``ansible-runner`` runtime environment. These will also
                     be read from ``env/settings`` in ``private_data_dir``.
    :param str ssh_key: The ssh private key passed to ``ssh-agent`` as part of the ansible-playbook run.
    :param str cmdline: Command line options passed to Ansible read from ``env/cmdline`` in ``private_data_dir``
    :param bool suppress_env_files: Disable the writing of files into the ``env`` which may store sensitive information
    :param str limit: Matches ansible's ``--limit`` parameter to further constrain the inventory to be used
    :param int forks: Control Ansible parallel concurrency
    :param int verbosity: Control how verbose the output of ansible-playbook is
    :param bool quiet: Disable all output
    :param str artifact_dir: The path to the directory where artifacts should live, this defaults to 'artifacts' under the private data dir
    :param str project_dir: The path to the playbook content, this defaults to 'project' within the private data dir
    :param int rotate_artifacts: Keep at most n artifact directories, disable with a value of 0 which is the default
    :param int timeout: The timeout value in seconds that will be passed to either ``pexpect`` of ``subprocess`` invocation
                    (based on ``runner_mode`` selected) while executing command. It the timeout is triggered it will force cancel the
                    execution.
    :param str streamer: Optionally invoke ansible-runner as one of the steps in the streaming pipeline
    :param io.FileIO _input: An optional file or file-like object for use as input in a streaming pipeline
    :param io.FileIO _output: An optional file or file-like object for use as output in a streaming pipeline
    :param Callable event_handler: An optional callback that will be invoked any time an event is received by Runner itself, return True to keep the event
    :param Callable cancel_callback: An optional callback that can inform runner to cancel (returning True) or not (returning False)
    :param Callable finished_callback: An optional callback that will be invoked at shutdown after process cleanup.
    :param Callable status_handler: An optional callback that will be invoked any time the status changes (e.g...started, running, failed, successful, timeout)
    :param Callable artifacts_handler: An optional callback that will be invoked at the end of the run to deal with the artifacts from the run.
    :param bool process_isolation: Enable process isolation, using either a container engine (e.g. podman) or a sandbox (e.g. bwrap).
    :param str process_isolation_executable: Process isolation executable or container engine used to isolate execution. (default: podman)
    :param str process_isolation_path: Path that an isolated playbook run will use for staging. (default: /tmp)
    :param str or list process_isolation_hide_paths: A path or list of paths on the system that should be hidden from the playbook run.
    :param str or list process_isolation_show_paths: A path or list of paths on the system that should be exposed to the playbook run.
    :param str or list process_isolation_ro_paths: A path or list of paths on the system that should be exposed to the playbook run as read-only.
    :param str container_image: Container image to use when running an ansible task
    :param list container_volume_mounts: List of bind mounts in the form 'host_dir:/container_dir. (default: None)
    :param list container_options: List of container options to pass to execution engine.
    :param str directory_isolation_base_path: An optional path will be used as the base path to create a temp directory, the project contents will be
                                          copied to this location which will then be used as the working directory during playbook execution.
    :param str fact_cache: A string that will be used as the name for the subdirectory of the fact cache in artifacts directory.
                       This is only used for 'jsonfile' type fact caches.
    :param str fact_cache_type: A string of the type of fact cache to use.  Defaults to 'jsonfile'.
    :param bool omit_event_data: Omits extra ansible event data from event payload (stdout and event still included)
    :param bool only_failed_event_data: Omits extra ansible event data unless it's a failed event (stdout and event still included)
    :param bool check_job_event_data: Check if job events data is completely generated. If event data is not completely generated and if
                                 value is set to 'True' it will raise 'AnsibleRunnerException' exception,
                                 if set to 'False' it log a debug message and continue execution. Default value is 'False'

    :return:
    """

    if run_id is None:
        run_id = kwargs.get('ident', str(uuid.uuid4()))

    # Setup RunnerConfig and Runner
    # rc = RunnerConfig(
    #     private_data_dir=private_data_dir,
    #     playbook=playbook_path,
    #     json_mode=True,
    #     ident=job_id,
    #     **kwargs
    # )
    # rc.prepare()
    #
    # r = Runner(config=rc,
    #            cancel_callback=None, finished_callback=None,
    #            event_handler=None, status_handler=None, artifacts_handler=None)
    # r.run()

    start_publisher()

    status_handler = kwargs.get('status_handler')
    if status_handler is None:
        status_handler = ko_ansible_status_handler

    event_handler = kwargs.get('event_handler')
    if event_handler is None:
        event_handler = ko_ansible_event_handler

    r = ansible_runner.run(
        ident=run_id,
        json_mode=True,
        private_data_dir=private_data_dir,
        playbook=playbook,
        event_handler=event_handler,
        status_handler=status_handler,
        **kwargs
    )
    return r
