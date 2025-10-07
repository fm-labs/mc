import yaml
import json
import os

class LiteralDumper(yaml.SafeDumper):
    pass

def str_representer(dumper, value: str):
    # Use literal block for multiline, plain for single-line
    if "\n" in value:
        # If you want to avoid a trailing newline, ensure it isn't there:
        value = value.rstrip("\n")
        return dumper.represent_scalar("tag:yaml.org,2002:str", value, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", value)

LiteralDumper.add_representer(str, str_representer)


def yaml_dump(data: dict, stream, **kwargs) -> None:
    kwargs["default_flow_style"] = kwargs.get("default_flow_style", False)
    yaml.dump(data, stream, Dumper=LiteralDumper, **kwargs)


def yaml_to_json(yaml_path: str, json_path: str) -> None:
    if not os.path.exists(yaml_path):
        print(f"YAML file does not exist: {yaml_path}")
        return

    with open(yaml_path, "r", encoding="utf-8") as yf:
        try:
            data = yaml.safe_load(yf) or {}
        except Exception as e:
            print(f"Error reading YAML file: {str(e)}")
            return

    with open(json_path, "w", encoding="utf-8") as jf:
        json.dump(data, jf, indent=2)
        print(f"Wrote JSON file: {json_path}")