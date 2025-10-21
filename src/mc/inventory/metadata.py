# Manage inventory metadata such as JSON schemas for different item types in databases.
import os
import json
from dataclasses import dataclass
from typing import Optional

from mc import config

from mc.inventory.storage import get_inventory_storage_instance

@dataclass
class InventoryMetadata:
    item_type: str
    title: str
    description: Optional[str] = None
    version: Optional[str] = None
    icon: Optional[str] = None


def enumerate_inventory_item_types_from_schema_dir() -> list[str]:
    """
    Enumerate all inventory item types by scanning the schema directory.

    Returns:
        list[str]: A list of inventory item types.
    """
    schema_dir = os.path.join(config.RESOURCES_DIR, "schemas", "inventory")
    if not os.path.exists(schema_dir):
        return []

    item_types = []
    for filename in os.listdir(schema_dir):
        if not filename.startswith("_") and filename.endswith(".schema.json"):
            item_type = filename[:-len(".schema.json")]
            item_types.append(item_type)
    return item_types


def enumerate_inventories_metadata_from_schema_dir() -> list[InventoryMetadata]:
    """
    Enumerate all inventory item metadata by scanning the schema directory.

    Returns:
        list[InventoryMetadata]: A list of inventory item metadata.
    """
    schema_dir = os.path.join(config.RESOURCES_DIR, "schemas", "inventory")
    if not os.path.exists(schema_dir):
        return []

    metadata_list = []
    for filename in os.listdir(schema_dir):
        if not filename.startswith("_") and filename.endswith(".schema.json"):
            item_type = filename[:-len(".schema.json")]
            schema_path = os.path.join(schema_dir, filename)
            try:
                with open(schema_path, "r", encoding="utf-8") as f:

                    schema = json.load(f)
                    title = schema.get("title", item_type)
                    description = schema.get("description")
                    version = schema.get("version")
                    icon = schema.get("$icon")
                    metadata = InventoryMetadata(
                        item_type=item_type,
                        title=title,
                        description=description,
                        version=version,
                        icon=icon
                    )
                    metadata_list.append(metadata)
            except (IOError, json.JSONDecodeError):
                continue
    return metadata_list


def list_inventory_item_types() -> list[str]:
    """
    List all inventory item types that have associated JSON schemas stored in the database.
    And also include item types from the schema directory.

    Returns:
        list[str]: A list of inventory item types.
    """
    # schema resources in the database
    storage = get_inventory_storage_instance()
    items = storage.list_items("_schemas")
    db_items_types = [item["item_key"] for item in items if "item_key" in item]

    # schema resources in the folder
    folder_items_types = enumerate_inventory_item_types_from_schema_dir()
    all_item_types = set(db_items_types) | set(folder_items_types)
    return list(all_item_types)


def store_inventory_json_schema(item_type: str, schema: dict):
    """
    Store a JSON schema for a specific inventory item type in the database.

    Args:
        item_type (str): The type of inventory item (e.g., "server", "network", "application").
        schema (dict): The JSON schema that defines the structure of the inventory item.
    """
    schema_dir = os.path.join(config.RESOURCES_DIR, "schemas", "inventory")
    if not os.path.exists(schema_dir):
        os.makedirs(schema_dir, exist_ok=True)
    schema_path = os.path.join(schema_dir, f"{item_type}.schema.json")
    with open(schema_path, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2)


    storage = get_inventory_storage_instance()
    item = {
        "item_key": item_type,
        "schema": schema
    }
    storage.save_item("_schemas", item)


def retrieve_inventory_json_schema(item_type: str) -> dict | None:
    """
    Retrieve a JSON schema for a specific inventory item type from the database.

    Args:
        item_type (str): The type of inventory item (e.g., "server", "network", "application").

    Returns:
        dict | None: The JSON schema if found, otherwise None.
    """
    schema_dir = os.path.join(config.RESOURCES_DIR, "schemas", "inventory")
    schema_path = os.path.join(schema_dir, f"{item_type}.schema.json")
    if os.path.exists(schema_path):
        try:
            with open(schema_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (IOError, json.JSONDecodeError):
            pass

    storage = get_inventory_storage_instance()
    item = storage.get_item("_schemas", item_type)
    if item:
        return item.get("schema")
    return None


def store_inventory_metadata(item_type: str, metadata: dict):
    """
    Store metadata for a specific inventory item type in the database.

    Args:
        item_type (str): The type of inventory item (e.g., "server", "network", "application").
        metadata (dict): The metadata associated with the inventory item type.
    """
    storage = get_inventory_storage_instance()
    item = {
        "item_key": item_type,
        "metadata": metadata
    }
    storage.save_item("_metadata", item)


def retrieve_inventory_metadata(item_type: str) -> dict | None:
    """
    Retrieve metadata for a specific inventory item type from the database.

    Args:
        item_type (str): The type of inventory item (e.g., "server", "network", "application").

    Returns:
        dict | None: The metadata if found, otherwise None.
    """
    storage = get_inventory_storage_instance()
    item = storage.get_item("_metadata", item_type)
    if item:
        return item.get("metadata")
    return None