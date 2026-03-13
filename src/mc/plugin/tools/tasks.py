import os

from mc.util.subprocess_helper2 import subprocess_run, subprocess_stream
from orchestra.celery import celery
from mc.plugin.tools.toolindex import get_tool_def

SUBPROCESS_TIMEOUT = 300  # seconds, hard timeout for subprocesses

@celery.task(bind=True)
def task_subprocess_run(self, cmd: list, env: dict = None):
    """
    Synchronous version of subprocess_run, to be used in non-async contexts.
    Runs the command and waits for it to complete before returning the result.
    """

    result = subprocess_run(cmd, env)
    #if "error" in result:
    #    self.update_state(state='FAILURE', meta=result)
    return result


@celery.task(bind=True)
def task_subprocess_stream(self, cmd: list, env: dict = None):

    output = []
    bytes_received = 0
    bytes_received_total = 0

    def callback(line: str):
        print(line)
        output.append(line)

        # todo stream log output to pubsub or websocket for real-time updates
        # e.g. self.update_state(state='PROGRESS', meta={"log": line})

        nonlocal bytes_received
        nonlocal bytes_received_total

        bytes_received += len(line)
        if bytes_received > 10 * 1024 * 1024:  # every 10 MB
            self.update_state(state='PROGRESS', meta={"status": f"Received {bytes_received} bytes so far..."})
            bytes_received_total += bytes_received
            bytes_received = 0

    rc = subprocess_stream(cmd, env, callback=callback)

    return {"stdout": "".join(output), "returncode": rc}


@celery.task(bind=True)
def task_tool_exec(self, tool_name: str, command_name: str, **kwargs):
    tool = get_tool_def(tool_name)
    if not tool:
        return {"error": f"Tool '{tool_name}' not found."}

    commands = tool.get("commands", {})
    command = commands.get(command_name)
    if not command:
        return {"error": f"Command '{command_name}' not found in tool '{tool_name}'."}
    if not "cmd" in command:
        return {"error": f"Command '{command_name}' in tool '{tool_name}' has no 'cmd' defined."}

    try:
        # run the command with docker if specified
        if "_docker" in commands and "cmd" in commands["_docker"]:
            docker_cmd = commands["_docker"]["cmd"]
            cmd = docker_cmd + command["cmd"][1:]  # Skip the first element as it's the command itself
        else:
            cmd = command["cmd"]

        # substitute arguments in the command (derived from input schema)
        input_schema = command.get("input_schema", {})
        input_schema_props = input_schema.get("properties", {}) if input_schema else {}
        arguments = input_schema_props.keys() if input_schema_props else []
        for arg in arguments:
            if arg not in kwargs:
                return {"error": f"Missing argument '{arg}' for command '{command_name}'."}
            cmd = [part.replace(f"{{{{{arg}}}}}", str(kwargs[arg])) for part in cmd]

        print(f"Running command: {' '.join(cmd)}")

        # todo evaluate and set environment variables from command definition
        env = os.environ.copy()
        result = subprocess_run(cmd, env)
        if "error" in result:
            self.update_state(state='FAILURE', meta=result)

        return result
    except Exception as e:
        return {"error": "Unknown exception occurred: " +  str(e)}