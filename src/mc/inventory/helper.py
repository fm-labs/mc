import hashlib
import json
import os

from mc.config import RESOURCES_DIR


# def gen_inventory_key(item_type: str, item_name: str) -> str:
#     """Generate a unique MD5 hash key for an inventory item based on its type and name."""
#     key_string = f"{item_type}:{item_name}"
#     return hashlib.md5(key_string.encode('utf-8')).hexdigest()


def default_inventory_item_schema_lookup(item_type: str) -> dict:
    schema_file = os.path.join(RESOURCES_DIR, "schemas", "inventory", f"{item_type.lower()}.schema.json")
    if not os.path.exists(schema_file):
        return {}

    try:
        with open(schema_file, "r") as f:
            schema = json.load(f)
            return schema
    except (json.JSONDecodeError, FileNotFoundError):
        return {}
    except Exception:
        return {}


def default_inventory_item_meta_lookup(item_type: str) -> dict:
    meta_file = os.path.join(RESOURCES_DIR, "schemas", "inventory", f"{item_type.lower()}.meta.json")
    if not os.path.exists(meta_file):
        return {}

    try:
        with open(meta_file, "r") as f:
            metadata = json.load(f)
            return metadata
    except (json.JSONDecodeError, FileNotFoundError):
        return {}
    except Exception:
        return {}


def lookup_inventory_schema(item_type: str):
    return default_inventory_item_schema_lookup(item_type)


def lookup_inventory_metadata(item_type: str):
    return default_inventory_item_meta_lookup(item_type)
