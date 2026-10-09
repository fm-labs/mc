from typing import Any

import pytest

from inventorydb.items import MASK

BASE = "/api/inventory"


@pytest.fixture
def app_stack(storage) -> dict[str, Any]:
    item = {
        "id": "s1",
        "type": "compose",
        "label": "S1",
        "_internal": 1,
        "repository": {"url": "git://r", "auth": {"username": "u", "password": "repo-pw"}},
        "environment": {"DB_PASSWORD": "db-pw", "PORT": "80"},
    }
    storage.write("app_stack", item)
    return item


class TestTypes:
    def test_lists_item_types(self, client):
        r = client.get(f"{BASE}/")
        assert r.status_code == 200
        item_types = [t["item_type"] for t in r.json()]
        assert "app-stack" in item_types
        assert item_types == sorted(item_types)

    def test_schema(self, client):
        r = client.get(f"{BASE}/app-stack/_schema")
        assert r.status_code == 200
        assert "properties" in r.json()

    def test_meta(self, client):
        r = client.get(f"{BASE}/app-stack/_meta")
        assert r.status_code == 200
        assert "actions" in r.json()

    @pytest.mark.parametrize("path", ["nope/_schema", "nope/_meta"])
    def test_unknown_type_schema_and_meta(self, client, path):
        assert client.get(f"{BASE}/{path}").status_code == 404

    @pytest.mark.parametrize(
        "method, path",
        [
            ("get", "nope"),
            ("post", "nope"),
            ("get", "nope/a"),
            ("put", "nope/a"),
            ("delete", "nope/a"),
            ("post", "nope/a/action/x"),
            ("get", "nope/a/view/x"),
        ],
    )
    def test_unknown_type_is_rejected(self, client, method, path):
        kwargs = {"json": {"properties": {"id": "a"}}} if method in ("post", "put") else {}
        r = client.request(method, f"{BASE}/{path}", **kwargs)
        assert r.status_code == 404
        assert "Unknown item type" in r.json()["detail"]

    def test_underscore_type_name_is_accepted(self, client, app_stack):
        assert client.get(f"{BASE}/app_stack/s1").status_code == 200


class TestList:
    def test_empty(self, client):
        r = client.get(f"{BASE}/app-stack")
        assert r.status_code == 200
        assert r.json() == []

    def test_masks_items(self, client, app_stack):
        r = client.get(f"{BASE}/app-stack")
        assert r.status_code == 200
        [item] = r.json()
        assert item["id"] == "s1"
        assert item["properties"]["repository"]["auth"]["password"] == MASK
        assert item["properties"]["environment"] == {"DB_PASSWORD": MASK, "PORT": "80"}
        assert "_internal" not in item["properties"]


class TestCreate:
    def test_creates_item(self, client, storage):
        r = client.post(f"{BASE}/app-stack", json={"properties": {"id": "a", "type": "compose", "password": "pw"}})
        assert r.status_code == 201
        assert r.json() == {"id": "a", "properties": {"id": "a", "type": "compose", "password": MASK}}
        assert storage.read("app_stack", "a")["password"] == "pw"

    def test_id_from_payload(self, client, storage):
        r = client.post(f"{BASE}/app-stack", json={"id": "a", "properties": {"type": "compose"}})
        assert r.status_code == 201
        assert storage.read("app_stack", "a") == {"id": "a", "type": "compose"}

    @pytest.mark.parametrize("payload", [{}, {"properties": {}}, {"properties": {"type": "compose"}}])
    def test_requires_id(self, client, payload):
        r = client.post(f"{BASE}/app-stack", json=payload)
        assert r.status_code == 400
        assert "id is required" in r.json()["detail"]

    def test_rejects_unsafe_id(self, client):
        assert client.post(f"{BASE}/app-stack", json={"properties": {"id": ".."}}).status_code == 400

    def test_rejects_non_object_properties(self, client):
        assert client.post(f"{BASE}/app-stack", json={"properties": ["a"]}).status_code == 400

    def test_rejects_duplicate(self, client, app_stack, storage):
        r = client.post(f"{BASE}/app-stack", json={"properties": {"id": "s1", "label": "other"}})
        assert r.status_code == 409
        assert storage.read("app_stack", "s1")["label"] == "S1"


class TestRead:
    def test_reads_item(self, client, app_stack):
        r = client.get(f"{BASE}/app-stack/s1")
        assert r.status_code == 200
        body = r.json()
        assert body["id"] == "s1"
        assert body["properties"]["label"] == "S1"
        assert body["properties"]["repository"]["auth"]["password"] == MASK

    def test_missing(self, client):
        assert client.get(f"{BASE}/app-stack/missing").status_code == 404


class TestUpdate:
    def test_updates_item(self, client, app_stack, storage):
        r = client.put(f"{BASE}/app-stack/s1", json={"properties": {"label": "S2"}})
        assert r.status_code == 200
        assert r.json()["properties"]["label"] == "S2"
        assert storage.read("app_stack", "s1")["label"] == "S2"

    def test_round_trip_keeps_secrets(self, client, app_stack, storage):
        # what the UI does: read the item, edit a field, send back all properties
        received = client.get(f"{BASE}/app-stack/s1").json()
        received["properties"]["label"] = "S2"
        r = client.put(f"{BASE}/app-stack/s1", json=received)
        assert r.status_code == 200
        assert storage.read("app_stack", "s1") == {**app_stack, "label": "S2"}

    def test_response_masks_secrets(self, client, app_stack):
        r = client.put(f"{BASE}/app-stack/s1", json={"properties": {"password": "new"}})
        assert r.json()["properties"]["password"] == MASK

    def test_missing(self, client):
        assert client.put(f"{BASE}/app-stack/missing", json={"properties": {}}).status_code == 404

    def test_rejects_non_object_properties(self, client, app_stack):
        assert client.put(f"{BASE}/app-stack/s1", json={"properties": "x"}).status_code == 400


class TestDelete:
    def test_deletes_item(self, client, app_stack, storage):
        r = client.delete(f"{BASE}/app-stack/s1")
        assert r.status_code == 200
        assert r.json() is True
        assert storage.read("app_stack", "s1") is None

    def test_missing(self, client):
        assert client.delete(f"{BASE}/app-stack/missing").status_code == 404


class TestActionsAndViews:
    @pytest.fixture
    def variable(self, storage) -> dict[str, Any]:
        item = {"id": "v1", "label": "V1", "value": "x"}
        storage.write("variable", item)
        return item

    def test_runs_action_with_stored_item(self, client, variable, item_module):
        item_module.actions["echo"] = lambda item, params: {"item": item, "params": params}
        r = client.post(f"{BASE}/variable/v1/action/echo", json={"a": 1})
        assert r.status_code == 200
        assert r.json() == {"item": variable, "params": {"a": 1}}

    def test_action_body_is_optional(self, client, variable, item_module):
        item_module.actions["echo"] = lambda item, params: {"params": params}
        r = client.post(f"{BASE}/variable/v1/action/echo")
        assert r.status_code == 200
        assert r.json() == {"params": {}}

    def test_runs_view(self, client, variable, item_module):
        async def view(item, params):
            return {"label": item["label"]}

        item_module.views["show"] = view
        r = client.get(f"{BASE}/variable/v1/view/show")
        assert r.status_code == 200
        assert r.json() == {"label": "V1"}

    @pytest.mark.parametrize("path", ["action/nope", "view/nope"])
    def test_unknown_handler(self, client, variable, item_module, path):
        method = "post" if path.startswith("action") else "get"
        assert client.request(method, f"{BASE}/variable/v1/{path}").status_code == 404

    def test_missing_item(self, client, item_module):
        item_module.actions["echo"] = lambda item, params: {}
        r = client.post(f"{BASE}/variable/missing/action/echo", json={})
        assert r.status_code == 404

    def test_handler_value_error_is_400(self, client, variable, item_module):
        def fail(item, params):
            raise ValueError("bad input")

        item_module.actions["fail"] = fail
        r = client.post(f"{BASE}/variable/v1/action/fail", json={})
        assert r.status_code == 400
        assert r.json()["detail"] == "bad input"

    def test_handler_error_is_500(self, client, variable, item_module):
        def fail(item, params):
            raise RuntimeError("boom")

        item_module.actions["fail"] = fail
        r = client.post(f"{BASE}/variable/v1/action/fail", json={})
        assert r.status_code == 500
        assert "boom" in r.json()["detail"]


def test_inventory_requires_auth():
    """The inventory router is mounted behind JWT auth in the main app."""
    from fastapi.testclient import TestClient

    import server

    # no `with` block: the lifespan (docker connections etc.) is not started
    r = TestClient(server.app).get(f"{BASE}/app-stack")
    assert r.status_code == 401
