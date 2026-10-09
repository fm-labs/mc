import pytest
from objbase.errors import ItemNotFoundError

from inventorydb import items
from inventorydb.items import MASK


@pytest.mark.parametrize(
    "item_type, expected",
    [
        ("app-stack", "app_stack"),
        ("App-Stack", "app_stack"),
        ("app_stack", "app_stack"),
        ("secret", "secret"),
    ],
)
def test_storage_key(item_type, expected):
    assert items.storage_key(item_type) == expected


class TestToResponse:
    def test_wraps_item(self):
        assert items.to_response({"id": "a", "label": "A"}) == {"id": "a", "properties": {"id": "a", "label": "A"}}

    @pytest.mark.parametrize(
        "key",
        [
            "password",
            "secret",
            "token",
            "passphrase",
            "private_key",
            "api_key",
            "DB_PASSWORD",
            "client_secret",
            "GITHUB_TOKEN",
            "Password",
        ],
    )
    def test_masks_sensitive_keys(self, key):
        assert items.to_response({"id": "a", key: "value"})["properties"][key] == MASK

    def test_masks_nested_values(self):
        item = {
            "id": "a",
            "repository": {"url": "git://r", "auth": {"username": "u", "password": "pw"}},
            "environment": {"DB_PASSWORD": "pw", "PORT": "80"},
            "list": [{"token": "t", "name": "n"}],
        }
        props = items.to_response(item)["properties"]
        assert props["repository"] == {"url": "git://r", "auth": {"username": "u", "password": MASK}}
        assert props["environment"] == {"DB_PASSWORD": MASK, "PORT": "80"}
        assert props["list"] == [{"token": MASK, "name": "n"}]

    @pytest.mark.parametrize("value", [None, ""])
    def test_empty_sensitive_values_are_not_masked(self, value):
        assert items.to_response({"id": "a", "password": value})["properties"]["password"] == value

    def test_drops_private_keys(self):
        props = items.to_response({"id": "a", "_internal": 1, "nested": {"_x": 1, "y": 2}})["properties"]
        assert props == {"id": "a", "nested": {"y": 2}}

    def test_does_not_modify_stored_item(self):
        item = {"id": "a", "password": "pw", "_internal": 1}
        items.to_response(item)
        assert item == {"id": "a", "password": "pw", "_internal": 1}


class TestListItems:
    def test_empty(self, storage):
        assert items.list_inventory_items(storage, "app-stack") == []

    def test_sorted_by_name_label_or_id(self, storage):
        storage.write("app_stack", {"id": "c"})
        storage.write("app_stack", {"id": "x", "label": "b"})
        storage.write("app_stack", {"id": "y", "name": "a"})
        assert [i["id"] for i in items.list_inventory_items(storage, "app-stack")] == ["y", "x", "c"]


class TestCreateItem:
    def test_creates_item(self, storage):
        created = items.create_inventory_item(storage, "app-stack", {"id": "a", "label": "A"})
        assert created == {"id": "a", "label": "A"}
        assert storage.read("app_stack", "a") == {"id": "a", "label": "A"}

    @pytest.mark.parametrize("data", [{}, {"id": ""}, {"id": None}, {"id": 123}])
    def test_requires_id(self, storage, data):
        with pytest.raises(ValueError, match="id is required"):
            items.create_inventory_item(storage, "app-stack", data)

    @pytest.mark.parametrize("bad_id", ["..", "a/b", "../etc"])
    def test_rejects_unsafe_id(self, storage, bad_id):
        with pytest.raises(ValueError):
            items.create_inventory_item(storage, "app-stack", {"id": bad_id})

    def test_rejects_duplicate(self, storage):
        items.create_inventory_item(storage, "app-stack", {"id": "a", "label": "first"})
        with pytest.raises(items.ItemExistsError):
            items.create_inventory_item(storage, "app-stack", {"id": "a", "label": "second"})
        assert storage.read("app_stack", "a")["label"] == "first"

    def test_strips_private_and_reserved_keys(self, storage):
        items.create_inventory_item(storage, "app-stack", {"id": "a", "_internal": 1, "item_type": "x"})
        assert storage.read("app_stack", "a") == {"id": "a"}


class TestReadItem:
    def test_reads_item(self, storage):
        storage.write("app_stack", {"id": "a", "label": "A"})
        assert items.read_inventory_item(storage, "app-stack", "a") == {"id": "a", "label": "A"}

    def test_missing(self, storage):
        with pytest.raises(ItemNotFoundError):
            items.read_inventory_item(storage, "app-stack", "missing")


class TestUpdateItem:
    def test_merges_data(self, storage):
        storage.write("app_stack", {"id": "a", "label": "A", "type": "compose"})
        updated = items.update_inventory_item(storage, "app-stack", "a", {"label": "B"})
        assert updated == {"id": "a", "label": "B", "type": "compose"}
        assert storage.read("app_stack", "a") == updated

    def test_missing(self, storage):
        with pytest.raises(ItemNotFoundError):
            items.update_inventory_item(storage, "app-stack", "missing", {"label": "B"})

    def test_cannot_change_id(self, storage):
        storage.write("app_stack", {"id": "a"})
        items.update_inventory_item(storage, "app-stack", "a", {"id": "b"})
        assert storage.read("app_stack", "a") == {"id": "a"}
        assert storage.read("app_stack", "b") is None

    def test_keeps_private_keys_and_drops_reserved_keys(self, storage):
        storage.write("app_stack", {"id": "a", "_internal": 1, "item_type": "app_stack"})
        items.update_inventory_item(storage, "app-stack", "a", {"_internal": 2, "item_type": "x"})
        assert storage.read("app_stack", "a") == {"id": "a", "_internal": 1}

    def test_masked_values_keep_stored_secrets(self, storage):
        stored = {
            "id": "a",
            "label": "A",
            "password": "pw",
            "repository": {"auth": {"username": "u", "password": "repo-pw"}},
            "environment": {"DB_PASSWORD": "db-pw"},
        }
        storage.write("app_stack", stored)
        # simulate a client sending back what it received, with one field changed
        data = items.to_response(stored)["properties"]
        data["label"] = "B"
        items.update_inventory_item(storage, "app-stack", "a", data)
        assert storage.read("app_stack", "a") == {**stored, "label": "B"}

    def test_new_secret_values_replace_stored_ones(self, storage):
        storage.write("app_stack", {"id": "a", "repository": {"auth": {"password": "old"}}})
        items.update_inventory_item(storage, "app-stack", "a", {"repository": {"auth": {"password": "new"}}})
        assert storage.read("app_stack", "a")["repository"]["auth"]["password"] == "new"

    def test_mask_without_stored_value_is_kept_as_is(self, storage):
        storage.write("app_stack", {"id": "a"})
        items.update_inventory_item(storage, "app-stack", "a", {"password": MASK})
        assert storage.read("app_stack", "a")["password"] == MASK


class TestDeleteItem:
    def test_deletes_item(self, storage):
        storage.write("app_stack", {"id": "a"})
        assert items.delete_inventory_item(storage, "app-stack", "a") is True
        assert storage.read("app_stack", "a") is None

    def test_missing(self, storage):
        with pytest.raises(ItemNotFoundError):
            items.delete_inventory_item(storage, "app-stack", "missing")
