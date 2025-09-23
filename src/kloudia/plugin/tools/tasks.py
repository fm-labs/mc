import os
import subprocess

from orchestra.celery import celery
from kloudia.plugin.tools.toolindex import get_tool_def

SUBPROCESS_TIMEOUT = 300  # seconds, hard timeout for subprocesses

@celery.task(bind=True)
def task_subprocess_run(self, cmd: list, env: dict = None):
    try:
        print(f"Running command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, env=env)
        print(f"Command finished with return code {result.returncode}")
        print(f"STDOUT:\n{result.stdout}")
        print(f"STDERR:\n{result.stderr}")

        # if result.returncode != 0:
        #     return {"error": f"Command failed with return code {result.returncode}",
        #             "output": result.stdout,
        #             "stderr": result.stderr,
        #             "returncode": result.returncode}

        return {"output": result.stdout, "stderr": result.stderr, "returncode": result.returncode}
    except subprocess.CalledProcessError as e:
        return {"error": str(e), "output": e.output, "stderr": e.stderr, "returncode": e.returncode}
    except Exception as e:
        return {"error": str(e)}


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
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, env=env, timeout=SUBPROCESS_TIMEOUT)
        print(f"Command finished with return code {result.returncode}")
        print(f"STDOUT:\n{result.stdout}")
        print(f"STDERR:\n{result.stderr}")

        #if result.returncode != 0:
        #    raise Exception(f"Tool command failed with return code {result.returncode}")

        return {"stdout": result.stdout, "stderr": result.stderr, "returncode": result.returncode}
    except subprocess.CalledProcessError as e:
        return {"error": str(e), "stdout": e.stdout, "stderr": e.stderr, "returncode": e.returncode}
    except Exception as e:
        return {"error": "Unknown exception occured: " +  str(e)}