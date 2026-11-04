# Inventory UI

The UI builds the inventory pages from the backend's schemas and metadata, with no code per item type.
For the backend and API, see [Inventory (inventorydb)](inventorydb.md).

Code: `ui/src/app/inventory/` · Types: `ui/src/features/inventory/inventory.types.ts` ·
API client: `ui/src/lib/api-client.ts`


## Navigation

The sidebar (`components/layout/admin-sidebar.tsx`, `nav-inventory.tsx`) calls `GET /api/inventory` and
adds a link for each item type. The link label is the schema `title`, and the link goes to
`/admin/inventory/<item_type>`. New item types appear in the sidebar automatically.


## Pages

| Route | Page |
|---|---|
| `/admin/inventory/:itemType` | Item list (`page.tsx`) |
| `/admin/inventory/:itemType/:itemId` | Item detail view (`item-page.tsx`) |

The list page is structured like this:

```
InventoryPage
└─ InventoryProvider          state, data loading, action dispatch (useInventory())
   ├─ Header + InventoryPrimaryButtons   "Create" button
   ├─ InventoryDataTable                 item list
   ├─ InventoryDebug                     raw items/columns (dev builds only)
   └─ InventoryDialogs                   create/update drawer, action/view drawers
```

`InventoryProvider` fetches three things for the item type: the items, `_schema` and `_meta`.
Its components read them through the `useInventory()` hook. When the provider is given a single `item`
(as on the detail page), it doesn't fetch the item list.


## Item list

The table columns are set in the type's `meta.json` under `index.columns`:

```json
{
  "index": {
    "columns": [
      {"name": "id", "title": "ID"},
      {"name": "type", "title": "Type"},
      {"name": "label", "title": "Label"}
    ]
  }
}
```

- **`name`:** `id` for the item id. Any other value is a key in `item.properties`.
- **`title`:** the column header. Defaults to `name`.
- **Order:** columns are shown in the listed order.
- **Opening an item:** the `id` column links to the item's detail view, so include `id` in the columns.

If the type has no metadata file, or the file has no `index.columns`, the columns are inferred from the schema:
`id`, then one column per schema property. In this fallback, non-required properties after the 10th are hidden
by default and can be shown with the column toggle.

An `Actions` column is always added at the end. Its dropdown has `Edit`, then the actions from
the type's `meta.json`, then `Delete`. Delete asks for confirmation and reloads the list.


## Detail view

The detail view (`item-page.tsx`) loads the item with `GET /api/inventory/<type>/<id>`. An unknown id shows
a "not found" message.

- **Header:** a back link to the list, and the item's `label`, `name` or `title` (falling back to the id).
  Next to it are an `Edit` button, which opens the update drawer, one button per action from
  the type's `meta.json`, and a `Delete` button. Delete asks for confirmation, then deletes the item and
  returns to the list.
- **Properties:** shown by `InventoryItemProperties` as a list of labelled values. Labels come from the
  schema `title`. A schema `description` shows as an info icon next to the label, with the text on hover. Properties are listed in schema order, followed by any properties
  that aren't in the schema. Values are formatted by type:

  | Value | Shown as |
  |---|---|
  | empty, `null` | `–` |
  | `*****` (masked secret) | lock icon |
  | boolean | `Yes` / `No` badge |
  | multi-line string | code block |
  | `http(s)://` URL | link |
  | array of scalars | badges |
  | object, array of objects | nested list (uses the schema's `properties` / `items`) |

- **Show raw JSON:** expands the item as a JSON tree.

After an edit, the item is reloaded.


## Create and update

`InventoryMutateDrawer` renders an [rjsf](https://rjsf-team.github.io/react-jsonschema-form/) form from the
schema, with a required `id` field added at the top (read-only on update). When saved, the form data is
sent as `properties`:

- **Create:** `POST /api/inventory/<type>`. The backend takes the id from `properties.id`.
- **Update:** `PUT /api/inventory/<type>/<id>`. The form starts with the stored values, and secrets show
  as `*****`. A field left as `*****` keeps its stored value.

After saving, the list is reloaded. After an update, the current item is reloaded too.


## Actions and views

Actions are defined in the type's `meta.json` under `actions`, and their `type` sets what happens on click:

| `type` | Behaviour |
|---|---|
| `form` | Opens a drawer with a form built from `inputSchema` and `uiSchema` (without `inputSchema`, just a Submit button). Submitting it sends `POST .../action/<id>` with the form data. The request timeout is `timeout` ms (default 120000). |
| `view` | Opens a drawer that loads `GET .../view/<id>` and shows the JSON result, with a Refresh button. |
| `link` | Navigates to `href`. |
| `separator` | Adds a divider in the dropdown. |

Action responses are shown as JSON. If the response contains `error`, it is shown as a toast. If it
contains `task_id`, the drawer shows the task's progress and log (`TaskProvider`, `TaskProgress`, `TaskLog`).

Example:

```json
{
  "actions": [
    {
      "id": "generate",
      "name": "Generate Key",
      "type": "form",
      "timeout": 30000,
      "inputSchema": {"type": "object", "properties": {"bits": {"type": "integer", "default": 4096}}},
      "uiSchema": {"bits": {"ui:widget": "updown"}}
    },
    {"type": "separator"},
    {"id": "info", "name": "Info", "type": "view"}
  ]
}
```


## Known gaps

- **No `uiSchema` in the item form:** the create/update drawer doesn't apply a `uiSchema`, so secret
  fields show as plain text inputs.
- **Lists aren't refreshed after actions:** after an action runs, the list isn't reloaded.
- **Plain `link` targets:** a `link` action's `href` is used as is (item fields aren't filled in), and
  following it reloads the whole page.
