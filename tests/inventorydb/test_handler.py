import importlib

import pytest

from inventorydb.handler import (
    get_inventory_item_action_handler,
    get_inventory_item_view_handler,
    handle_inventory_item_action,
    handle_inventory_item_view,
)


def test_loads_action_handler(item_module):
    def handler(item, params):
        return {}

    item_module.actions["ping"] = handler
    assert get_inventory_item_action_handler("variable", "ping") is handler


def test_loads_view_handler(item_module):
    def handler(item, params):
        return {}

    item_module.views["details"] = handler
    assert get_inventory_item_view_handler("variable", "details") is handler


def test_normalizes_item_type(item_module):
    def handler(item, params):
        return {}

    item_module.actions["ping"] = handler
    assert get_inventory_item_action_handler("Variable", "ping") is handler


def test_loads_real_item_module():
    from mc.inventory.item import ssh_key

    assert get_inventory_item_action_handler("ssh-key", "set_content") is ssh_key.actions["set_content"]


def test_unknown_action(item_module):
    with pytest.raises(NotImplementedError, match="Action 'nope'"):
        get_inventory_item_action_handler("variable", "nope")


def test_unknown_view(item_module):
    with pytest.raises(NotImplementedError, match="View 'nope'"):
        get_inventory_item_view_handler("variable", "nope")


def test_module_without_registry(item_module):
    del item_module.views
    with pytest.raises(NotImplementedError):
        get_inventory_item_view_handler("variable", "details")


def test_item_type_without_module():
    with pytest.raises(NotImplementedError, match="has no actions"):
        get_inventory_item_action_handler("no_such_type", "ping")


@pytest.mark.parametrize("item_type", ["../x", "a.b", "a b", ""])
def test_rejects_invalid_item_type(item_type):
    with pytest.raises(NotImplementedError, match="Invalid item type"):
        get_inventory_item_action_handler(item_type, "ping")


def test_missing_dependency_in_item_module_is_not_hidden(monkeypatch):
    # an item module that exists but fails on a missing dependency must surface the real error
    def broken_import(name, *args, **kwargs):
        if name == "mc.inventory.item.broken":
            raise ModuleNotFoundError("No module named 'somedep'", name="somedep")
        return original_import(name, *args, **kwargs)

    original_import = importlib.import_module
    monkeypatch.setattr(importlib, "import_module", broken_import)
    with pytest.raises(ModuleNotFoundError, match="somedep"):
        get_inventory_item_action_handler("broken", "ping")


async def _async_handler(item, params):
    return {"async": True, "id": item["id"], "params": params}


def _sync_handler(item, params):
    return {"async": False, "id": item["id"], "params": params}


@pytest.mark.parametrize("handler, is_async", [(_async_handler, True), (_sync_handler, False)])
async def test_handle_action_runs_sync_and_async_handlers(item_module, handler, is_async):
    item_module.actions["run"] = handler
    result = await handle_inventory_item_action("variable", {"id": "a"}, "run", {"x": 1})
    assert result == {"async": is_async, "id": "a", "params": {"x": 1}}


async def test_handle_view_defaults_params(item_module):
    item_module.views["show"] = _sync_handler
    result = await handle_inventory_item_view("variable", {"id": "a"}, "show", None)
    assert result["params"] == {}
