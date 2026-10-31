# Container hosts

A container host is a docker engine, podman engine or another mc instance ("node") that mc manages containers on.
Each host has an alias (e.g. `localhost`), which is used in the API routes: `/api/containers/{alias}/...`.

Code: `src/mc/plugin/containers/` (`deps.py`, `manager.py`, `node_client.py`, `routes.py`)


## Configuration

Container hosts are configured in the `docker_hosts` section of the mc config file (`mc.conf.json`):

```json
{
  "docker_hosts": {
    "localhost": { "url": "unix:///var/run/docker.sock" },
    "remote":    { "url": "ssh://user@my-remote-host" },
    "podman":    { "url": "podman+unix:///run/podman/podman.sock" },
    "node1":     { "url": "node+https://other-mc-node:3443", "api_key": "...", "autoconnect": true }
  }
}
```

The URL prefix selects the engine:

| URL | Engine |
|---|---|
| `unix://...`, `tcp://...`, `ssh://...` (no prefix) | docker |
| `docker+<url>` | docker |
| `podman+<url>` | podman |
| `node+<url>` | another mc instance (see [Nodes](#nodes)) |

`ssh://` docker hosts use the local `ssh` client, so the SSH key and host key must be set up for the user mc runs as.

Every entry can set `"autoconnect": true` to be connected in the UI by default (see [Connecting in the UI](#connecting-in-the-ui)).
Entries without a `url` are skipped.


### `localhost` fallback

If `docker_hosts` has no `localhost` entry, mc still lists a `localhost` host that connects to
`unix:///var/run/docker.sock`. To use a different socket, add an explicit `localhost` entry.

The `DOCKER_HOST` environment variable is **not** used for container hosts anymore. App stack deploy and destroy
still use it (default `unix:///var/run/docker.sock`), not `docker_hosts`. The app stack's `target_node` is ignored.


## How clients are loaded

Clients are created lazily, on the first API request for a host alias, not at startup:

1. `GET /api/containers/hosts` lists the hosts from `docker_hosts` (plus the `localhost` fallback).
   It reads the config only and doesn't connect to any host. `connected` is `true` once a client for the host was created.
2. A request to `/api/containers/{alias}/...` looks up the alias in the `ContainerClientsManager`.
   If no client is registered yet, it's created from the `docker_hosts` entry and registered (`deps.py`).
   Parallel first requests for the same host share one client.
3. Unknown aliases return `404`. If the client can't be created (e.g. an `ssh://` host is down), the request returns `502`
   and the next request tries again.

Hosts are only reached when they are used, so an unreachable host doesn't slow down the startup.
Config changes need a restart, because the config file is loaded once at startup and created clients are kept.

The `version` endpoint (`/api/containers/{alias}/version`) is cached for one hour per alias.


## Connecting in the UI

Hosts start disconnected in the UI, unless they have `"autoconnect": true`. Click **Connect** on the host page to load
its data, and **Disconnect** to stop. The choice is saved per host in the browser
(`localStorage` key `container_host_<alias>_enabled`) and overrides `autoconnect`.
The status shows `Connected` (host responded), `Disconnected` (connect enabled, but no response) or `Disabled`.

The **Engine** view shows the raw `info` and `summary` data of the host.


## Nodes

A node is another mc instance. mc talks to the node's `/api/containers` routes, so the node's own container hosts
can be used from the primary host.

```json
{
  "docker_hosts": {
    "node1": {
      "url": "node+https://node1:3443",
      "api_key": "...",
      "remote_alias": "localhost",
      "timeout": 15
    }
  }
}
```

| Field | Default | Description |
|---|---|---|
| `url` | required | Node URL with the `node+` prefix |
| `api_key` | none | Must match `MC_API_KEY` on the node (more than 8 characters) |
| `remote_alias` | `localhost` | Container host alias on the node |
| `timeout` | `15` | Request timeout in seconds |
| `autoconnect` | `false` | Connect in the UI by default |

Errors from a node keep their status code, with the node's status and message in the detail,
e.g. `Node https://node1:3080: (404) No such container`. A `401` from the node (e.g. a wrong `api_key`) is returned
as `400`, because a `401` would log you out of the local UI.


## Migrating from the `nodes` section

The `nodes` section and the `localdocker` alias were replaced:

| Before | Now |
|---|---|
| `"nodes": { "node1": { "base_url": "http://node1:3080", ... } }` | `"docker_hosts": { "node1": { "url": "node+http://node1:3080", ... } }` |
| `remote_alias` default `localdocker` | `remote_alias` default `localhost` |
| local host alias `localdocker` (from `DOCKER_HOST`) | `localhost` (from `docker_hosts`, or the fallback) |
| `autoconnect` (node connected at startup) | `autoconnect` (host connected in the UI by default) |

Nodes that still run an older mc version only have a `localdocker` alias, so set `"remote_alias": "localdocker"`
for them until they're updated.
