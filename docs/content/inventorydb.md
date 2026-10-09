# Inventory (inventorydb)

The inventory stores the items Mission Control manages (app stacks, container nodes, registries,
SSH keys, secrets, variables, ...). It is schema-driven: every item type is defined by a JSON schema,
and the API and UI forms are generated from it.

Code: `src/inventorydb/` · Item types: `src/mc/inventory/item/`


## Item types

Each item type is a Python package in `src/mc/inventory/item/`, named after the type with underscores:

```
src/mc/inventory/item/app_stack/
    __init__.py     # required; may define the action and view handlers
    schema.json     # required
    meta.json       # optional
    helper.py       # optional, any other modules the type needs
```

| File | Purpose |
|---|---|
| `schema.json` | JSON schema of the item properties (`title`, `description`, `version`, `$icon` are shown in the UI) |
| `meta.json` | UI metadata: table columns (`index.columns`) and the `actions` offered for the type, see [Inventory UI](inventory-ui.md) |
| `__init__.py` | `actions` / `views` dicts with the type's handlers (can be empty) |

Type names are hyphenated in URLs (`app-stack`) and underscored in packages and storage (`app_stack`). The API
accepts both forms. Packages starting with `_` are ignored. The JSON files are package data, so they ship
with the code in the wheel, the Docker image and the PyInstaller binary.

### Registry

Item types are loaded once by the registry (`inventorydb/registry.py`), at server startup or on first use.
All lookups are then served from memory, so **changes to schema, meta or module files need a server
restart**.

The registry is built from sources. Currently there is one, `PackageSource("mc.inventory.item")`, which
loads the packages described above. If several sources define the same type, the first one wins.

When the registry loads, it logs a warning (`Inventory: ...`) for each of these:

- schema or meta files that can't be read (an invalid schema skips the type)
- an item module that fails to import. The type stays available, and its actions return `500` with the
  import error.
- a `form`/`view` action in `meta.json` with no handler in the module's `actions`/`views`, and the reverse
- an unsupported action `type`, an action without `id`, or a `link` action without `href`
- modules or packages in `mc.inventory.item` without a `schema.json`, which means they aren't item types


## Storage

Items are plain JSON objects with a required string `id`, stored via [objbase](https://pypi.org/project/objbase/)
under `$DATA_DIR/inventory`. The backend is selected with `INVENTORY_STORAGE`:

| Value | Layout |
|---|---|
| `directory` (default) | one JSON file per item: `<type>/<id>.json` |
| `file` | one JSON file per type |
| `sqlite` | `inventory.db` |

Ids must be usable as a file name (no `/`, not `.` or `..`).


## API

All routes are under `/api/inventory` and require a bearer token.

| Method | Path | Result |
|---|---|---|
| `GET` | `/` | List of item types |
| `GET` | `/{type}/_schema`, `/{type}/_meta` | Schema / metadata of a type |
| `GET` | `/{type}` | All items, sorted by `name`, `label` or `id` |
| `POST` | `/{type}` | Create an item (`201`) |
| `GET` | `/{type}/{id}` | Read an item |
| `PUT` | `/{type}/{id}` | Update an item (merged into the stored item) |
| `DELETE` | `/{type}/{id}` | Delete an item |
| `POST` | `/{type}/{id}/action/{name}` | Run an action; the JSON body (optional) is passed as params |
| `GET` | `/{type}/{id}/view/{name}` | Render a view |

Request and response bodies wrap the item: `{"id": "my-app", "properties": {...}}`.
On create, the id is taken from `properties.id` (or the top-level `id`).

Errors: `400` invalid input or id · `404` unknown type, item, action or view · `409` item already exists ·
`500` handler failure.


## Secrets and protected keys

- **Masking:** values of keys containing `password`, `secret`, `token`, `passphrase`, `private_key` or
  `api_key` (case-insensitive, at any nesting depth) are returned as `*****`.
- **Round trips are safe:** on update, a `*****` value keeps the stored value, so a client can send back
  what it received. Send a new value to replace a secret.
- **Private keys:** keys starting with `_` are never returned and can't be set by clients; they are kept on update.
- **Reserved keys:** `item_type` is removed from client input.

Prefer the `secret` item type (stored in the vault, not in the inventory) for sensitive values.


## Actions and views

A type's module exposes two registries that map names to handlers:

```python
# src/mc/inventory/item/container_node/__init__.py
def handle_node_ping(item: dict, params: dict) -> dict:
    ...
    return {"status": "success"}


actions = {"ping": handle_node_ping}
views = {}  # optional, same shape
```

Handlers receive the stored (unmasked) item and the params, and return a JSON-serializable dict.
They can be sync (run in a thread pool) or `async`. Raise `ValueError` for invalid input (→ `400`);
any other exception becomes a `500`.

To offer an action in the UI, list it in `meta.json`:

```json
{
  "actions": [
    {"id": "ping", "name": "Ping", "type": "form", "inputSchema": {"type": "object", "properties": {}}}
  ]
}
```


## Adding an item type

1. Create the package `src/mc/inventory/item/<type_with_underscores>/` with an `__init__.py`.
2. Add `schema.json`.
3. Optionally add `meta.json` for columns and actions, and the handlers to `__init__.py`.

No code changes to `inventorydb` are needed. Restart the server, then check the log for `Inventory:` warnings.


## Limitations

- Items are not validated against their schema on create/update.
- Updates merge: removing a field in a form does not delete it from the stored item.
- Deleting an item does not run cleanup (e.g. an `ssh-key` item's key file under `etc/ssh_keys/` is kept).
