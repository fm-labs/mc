import json

import pytest

from inventorydb import metadata
from mc import config


@pytest.fixture
def resources_dir(tmp_path, monkeypatch):
    """Point schema lookups at an empty resources dir."""
    schema_dir = tmp_path / "schemas" / "inventory"
    schema_dir.mkdir(parents=True)
    monkeypatch.setattr(metadata, "RESOURCES_DIR", str(tmp_path))
    monkeypatch.setattr(config, "RESOURCES_DIR", str(tmp_path))
    return schema_dir


@pytest.mark.parametrize("item_type", ["app-stack", "app_stack", "App-Stack"])
def test_lookup_schema_accepts_name_variants(item_type):
    schema = metadata.lookup_inventory_schema(item_type)
    assert schema.get("properties")


@pytest.mark.parametrize("item_type", ["app-stack", "app_stack"])
def test_lookup_metadata_accepts_name_variants(item_type):
    assert metadata.lookup_inventory_metadata(item_type).get("actions")


def test_lookup_missing():
    assert metadata.lookup_inventory_schema("nope") == {}
    assert metadata.lookup_inventory_metadata("nope") == {}


def test_lookup_invalid_json(resources_dir):
    (resources_dir / "broken.schema.json").write_text("{not json")
    assert metadata.lookup_inventory_schema("broken") == {}


def test_enumerate(resources_dir):
    (resources_dir / "thing.schema.json").write_text(
        json.dumps({"title": "Thing", "description": "A thing", "version": "1", "$icon": "box"})
    )
    (resources_dir / "untitled.schema.json").write_text("{}")
    (resources_dir / "_hidden.schema.json").write_text("{}")
    (resources_dir / "broken.schema.json").write_text("{not json")
    (resources_dir / "thing.meta.json").write_text("{}")

    infos = {i.item_type: i for i in metadata.enumerate_inventories_from_schema_dir()}
    assert set(infos) == {"thing", "untitled"}
    assert infos["thing"] == metadata.InventoryShortInfo("thing", "Thing", "A thing", "1", "box")
    assert infos["untitled"].title == "untitled"


def test_enumerate_missing_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "RESOURCES_DIR", str(tmp_path / "missing"))
    assert metadata.enumerate_inventories_from_schema_dir() == []
