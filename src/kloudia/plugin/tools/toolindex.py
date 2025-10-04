import os
import json
from pathlib import Path

from kloudia.config import RESOURCES_DIR

TOOL_INDEX = []
TOOL_DIR = Path(RESOURCES_DIR) / "toolbox"

def load_tool_index():
    global TOOL_INDEX

    print("Loading tool index...")
    TOOL_INDEX.clear()
    # enumerate all json files in the tools directory
    tool_names = [f[:-5] for f in os.listdir(TOOL_DIR) if f.endswith('.json')]
    for tool_name in tool_names:
        tool_file = os.path.join(TOOL_DIR, f"{tool_name}.json")
        with open(tool_file, 'r') as f:
            tool_data = json.load(f)
            TOOL_INDEX.append(tool_data)


def get_tool_index():
    global TOOL_INDEX
    if not TOOL_INDEX:
        load_tool_index()

    return TOOL_INDEX


def get_tool_def(tool_name) -> dict | None:
    tool_file = os.path.join(TOOL_DIR, f"{tool_name}.json")
    if os.path.exists(tool_file):
        with open(tool_file, 'r') as f:
            tool_data = json.load(f)
            return tool_data
    return None
