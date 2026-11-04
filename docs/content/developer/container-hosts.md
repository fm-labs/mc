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


### Node proxy (experimental)

The node proxy forwards any HTTP request to a node, not only the `/api/containers` routes. A request with an
`x-mc-node: <alias>` header is sent to that node's URL with the same method, path, query string and body.
The UI's RPC page uses it to run RPC methods on a node.

Code: `src/mc/server/middleware/node_proxy_middleware.py`. Tests: `tests/mc/test_node_proxy_middleware.py`.

It's off by default. Set `MC_NODE_PROXY_ENABLED=true` on the primary mc to turn it on. The node doesn't need it.
The middleware is always loaded. While it's off, requests for a node return `404` and are never handled locally,
so a command meant for a node can't run on the primary mc by mistake.

```bash
curl -X POST https://mc:3443/api/rpc \
  -H "Authorization: Bearer <login token>" \
  -H "x-mc-node: node1" \
  -d '{"jsonrpc": "2.0", "method": "test.ping", "id": 1}'
```

How a request is handled:

1. No `x-mc-node` header, an empty one, `localhost` or `default`: the local mc handles the request as usual.
2. The proxy must be on (`MC_NODE_PROXY_ENABLED`), else `404`.
3. The request must have a valid login token (`Authorization: Bearer <JWT>`), else `401`. `x-api-key` is not
   accepted for proxied requests.
4. The alias must be a `docker_hosts` entry with a `node+http://` or `node+https://` URL, else `404`.
   Without an `api_key` the request is sent with no key; if the node needs one, its `401` becomes a `502`.
5. The request is sent to the node. The path and query string are kept as sent (encoding, repeated keys, empty values),
   and the body is streamed.
6. The node's response is streamed back with its status code and headers. The body isn't decoded, so compressed
   responses stay valid.

Headers sent to the node:

- `x-api-key` is set to the entry's `api_key` (if set), so the node authenticates the primary mc, not the user.
- Removed: `authorization`, `cookie`, the client's `x-api-key`, `x-mc-node` (so the node doesn't proxy the request
  again), `host`, `content-length` and hop-by-hop headers (`connection`, `keep-alive`, `te`, `trailer`,
  `transfer-encoding`, `upgrade`, `proxy-authorization`).
- All other headers are sent, including repeated ones.

Headers returned from the node drop `set-cookie`, `content-length`, `proxy-authenticate` and hop-by-hop headers.
Node cookies are never stored, because one HTTP client is shared by all users.

Errors:

| Status | Cause |
|---|---|
| `401` `Unauthorized` | No valid login token |
| `404` `Node not found` | Proxy off, unknown alias, or not a `node+http(s)://` host |
| `502` `Proxy authentication error` | The node returned `401`, e.g. a wrong `api_key`. Not passed on as `401`, which would log you out of the local UI |
| `502` `Upstream node unreachable` | Connection error |
| `504` `Upstream node timed out` | No response within the timeout (30 s) |

Other node errors keep their status code and body.

Limits:

- HTTP only. WebSocket requests are always handled locally.
- The timeout is 30 s for every node. The entry's `timeout` field isn't used.
- Redirects from the node are returned to the client, not followed.
- The HTTP client is created on the first proxied request and closed when the server shuts down.


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
