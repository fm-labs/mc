import subprocess

from orchestra.celery import celery
from kloudia.integrations.tools.toolindex import TOOL_INDEX


@celery.task
def tool_exec_task(tool_name: str, command: str, **kwargs):
    if tool_name not in TOOL_INDEX:
        return {"error": f"Tool '{tool_name}' not found."}

    if command not in TOOL_INDEX[tool_name]:
        return {"error": f"Command '{command}' not found in tool '{tool_name}'."}

    try:
        tool = TOOL_INDEX[tool_name]
        command_info = tool[command]

        if "_docker" in tool:
            docker_cmd = tool["_docker"]["cmd"]
            cmd = docker_cmd + command_info["cmd"][1:]  # Skip the first element as it's the command itself
        else:
            cmd = command_info["cmd"]

        for arg in command_info.get("arguments", []):
            if arg not in kwargs:
                return {"error": f"Missing argument '{arg}' for command '{command}'."}
            cmd = [part.replace(f"{{{{{arg}}}}}", str(kwargs[arg])) for part in cmd]

        print(f"Running command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        print(f"Command finished with return code {result.returncode}")
        print(f"STDOUT:\n{result.stdout}")
        print(f"STDERR:\n{result.stderr}")

        if result.returncode != 0:
            raise Exception(f"Tool command failed with return code {result.returncode}")

        return {"output": result.stdout}

    except Exception as e:
        return {"error": str(e)}