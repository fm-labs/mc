import json
import os

CONFIG_DIR = os.getenv("CONFIG_DIR", "config")

def load_config_json(file_name: str) -> dict|list:
    file_path = f"config/{file_name}.json"
    with open(file_path, 'r') as f:
        return json.load(f)