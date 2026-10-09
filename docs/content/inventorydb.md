# Inventory (inventorydb)

The inventory stores the items Mission Control manages (app stacks, container nodes, registries,
SSH keys, secrets, variables, ...). It is schema-driven: every item type is defined by a JSON schema,
and the API and UI forms are generated from it.

Code: `src/inventorydb/` · Item types: `src/mc/inventory/item/`


## Item types

Each item type is a Python package named after the type with underscores. Core types live in
`src/mc/inventory/item/`, and plugin types in their plugin's `inventory/` package (see [Registry](#registry)):

```
src/mc/plugin/apps/inventory/app_stack/
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
All lookups are then served from memory, so **changes to item types or `inventory.toml` need a server
restart**.

The registry loads types from three sources, in order of precedence:

| # | Source | Location |
|---|---|---|
| 1 | Built-in types | packages in `mc.inventory.item` (see above) |
| 2 | Plugin types | `mc.plugin.<plugin>.inventory` packages, and installed packages registered under the `mc.inventory_types` entry point group |
| 3 | User types | folders in `$CONFIG_DIR/inventory/` |

All sources use the same layout: one folder per type with `schema.json`, an optional `meta.json` and an
optional `__init__.py` with the handlers. If several sources define the same type, the first one wins and the
others are skipped with a warning. A skipped or disabled type's code never runs.

#### Plugin types

A plugin adds item types with an `inventory` subpackage that contains one package per type. For example, the
apps plugin provides `app-stack` and `app-template` in `mc/plugin/apps/inventory/`, and the containers plugin
provides `container-node` and `container-registry` in `mc/plugin/containers/inventory/`. For the
PyInstaller binary, add the plugin's item package to the `--collect-submodules` / `--collect-data` flags in
`build_bin.sh`. An installed Python package does the same through an
entry point whose value is its item package:

```toml
# pyproject.toml of the plugin
[project.entry-points."mc.inventory_types"]
my_plugin = "my_plugin.inventory"
```

#### User types

User types live outside the code in `$CONFIG_DIR/inventory/<type>/`. Folder names must be lowercase letters,
digits and `-`. Folders starting with `.` or `_` are ignored.

```
$CONFIG_DIR/inventory/backup-target/
    schema.json
    meta.json       # optional
    __init__.py     # optional, only loaded with INVENTORY_USER_CODE=true
    checks.py       # optional, imported with "from .checks import ..."
```

Schema-only user types always work. Python code is loaded only if `INVENTORY_USER_CODE=true` is set (default
`false`), because it runs inside the API process with its full permissions. Even then, code is skipped if the
folder, the type folder or any `.py` file in it is writable by other users. User modules are loaded as
`mc_user_inventory.<type>` without changing `sys.path`. They can import `mc.*` and any package installed in the
environment. In the PyInstaller binary, that means only the bundled packages.

User types can't replace built-in or plugin types. To customise those, use `inventory.toml`.

#### Overrides: `inventory.toml`

`$CONFIG_DIR/inventory.toml` is optional and can disable or adjust any item type:

```toml
[types.app-template]
enabled = false         # don't load this type (from any source)

[types.app-stack]
title = "Stacks"        # replaces the schema title
icon = "layers"         # replaces the schema $icon
order = 1               # position in the type list (and the sidebar)
```

Types with an `order` come first. The others follow, sorted by name.

#### Warnings

When the registry loads, it logs a warning (`Inventory: ...`) for each of these:

- schema or meta files that can't be read (an invalid schema skips the type)
- an item module that fails to import. The type stays available, and its actions return `500` with the
  import error.
- a `form`/`view` action in `meta.json` with no handler in the module's `actions`/`views`, and the reverse
- an unsupported action `type`, an action without `id`, or a `link` action without `href`
- modules or folders in a source without a `schema.json`, which means they aren't item types
- a type defined by several sources, or user code that was skipped (disabled, or writable by others)
- invalid entries in `inventory.toml`, or sections that match no item type


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
# src/mc/plugin/containers/inventory/container_node/__init__.py
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
