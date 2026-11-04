# API

All routes are under `/api`. With `MC_DEV_MODE=true`, the OpenAPI docs are at `/docs` and `/redoc`.

## Auth

The routers depend on `mc.server.deps.dep_auth_user`, which accepts either:

- **Bearer JWT** from `POST /api/auth/login` (OAuth2 password form: `username`, `password`). The UI stores it
  in `localStorage`.
- **`x-api-key` header** matching `MC_API_KEY` (more than 8 chars). Used by a primary mc to talk to its nodes.

Missing or invalid credentials return `401`.

| Module | Role |
|---|---|
| `mc/server/deps.py` | `dep_auth_user`: reads the bearer token or API key, returns the user dict |
| `mc/server/auth_helper.py` | `create_jwt_access_token` / `verify_jwt_access_token` (PyJWT) |
| `mc/server/auth.py` | Maps verified JWT claims or an API key to a user (`{"username": ...}`) |
| `mc/config.py` | `JWT_*` settings |

Tokens are HS256, signed with `JWT_SECRET_KEY`, and expire after 60 minutes. Claims: `sub` (username),
`iss` (`mc`), `iat`, `nbf`, `exp`, `jti`. The header has a `kid` (first 16 hex chars of the key's MD5), so tokens
signed with an older key can be told apart. Verification pins the algorithm and checks the issuer and audience (`mc`).

```bash
TOKEN=$(curl -s -X POST localhost:3080/api/auth/login -d 'username=operator&password=...' | jq -r .access_token)
curl -H "Authorization: Bearer $TOKEN" localhost:3080/api/containers/hosts
```

## Routes

| Prefix | Module | Purpose |
|---|---|---|
| `/api/info`, `/api/health` | `server/router.py` | Version, health (no auth) |
| `/api/auth/login`, `/logout`, `/user` | `server/router.py` | Login and current user |
| `/api/containers/hosts` | `plugin/containers/routes.py` | Configured hosts and connection state |
| `/api/containers/{alias}/...` | `plugin/containers/routes.py` | `version`, `info`, `df`, `containers`, `images`, `volumes`, `networks`, `prune/{scope}`, `events/stream` |
| `/api/containers/{alias}/containers/{id}/...` | same | `actions/{action}`, `exec`, `top` (`?ps_args=aux`), `logs`, `logs/stream` |
| `/api/inventory/...` | `inventorydb/routes.py` | Item types, schema/meta, CRUD, actions, views (see [inventorydb](inventorydb.md#api)) |
| `/api/rpc` | `server/routes_rpc.py` | JSON-RPC (below) |
| `/api/tools`, `/api/tools/{name}` | `plugin/tools/routes.py` | List, describe, run (`POST`) and stream (`POST .../stream`) tools (below) |
| `/api/apps/...` | `plugin/apps/routes.py` | App specs: CRUD, bundle upload, compiled files, streamed compose actions (see [Apps](apps.md#api)) |
| `/api/config?conf=mc\|ssh` | `server/routes_config.py` | Read and (if enabled) write config files |

## Errors

`HTTPException`s are returned as a `Problem` JSON body (`server/models.py`):

```json
{ "error": "No such container", "status": 404, "detail": "No such container" }
```

For node hosts, the node's status code is kept, except `401` from the node, which becomes `400` so the local
UI doesn't log out.

## Streams

Long-running reads stream newline-delimited JSON (`application/x-ndjson`, one object per line):

- `GET /api/containers/{alias}/containers/{id}/logs/stream`: container logs (`?format=sse` for server-sent events)
- `GET /api/containers/{alias}/events/stream`: docker events
- `POST /api/tools/{name}/stream` and `POST /api/apps/{id}/action/{action}`: subprocess output as `STDOUT`
  events, then `RC` (exit code) or `ERROR`

Blocking SDK calls run in a thread pool (`run_in_threadpool`, `anyio.to_thread`), so a slow host doesn't block
the event loop. The generator stops when the client disconnects.

## RPC

`/api/rpc` is a small JSON-RPC 2.0 endpoint for operations that don't fit REST.

- `GET /api/rpc` lists methods with a JSON schema of their params, generated from the function signature
  (`Literal` becomes `enum`, names ending in `password`/`secret`/`token` get `format: password`).
- `POST /api/rpc` with `{"jsonrpc": "2.0", "method": "...", "params": {...}, "id": 1}`. Without `id` it's a
  notification and returns `{}`.

| Method | Does |
|---|---|
| `test.ping`, `test.echo` | Connectivity test |
| `system.update` | Pulls `fmlabs/mc:latest` (restart needed) |
| `docker.info`, `docker.prune` | Local docker info, prune by scope |
| `docker.volume.backup`, `.restore`, `.clone` | Back up a volume to a tar file, restore it, or copy it to a new volume |
| `docker.container.action` | Start/stop/restart/pause/unpause a local container |
| `docker.swarm.info`, `.init`, `.join_token`, `.leave` | Swarm management |
| `user.change_password`, `user.reset_password` | Users (reset prints the new password to the log) |
| `ssh.add_key`, `ssh.list_keys` | Keys in the container's ssh-agent |

RPC handlers use `docker.from_env()`, so they act on the local docker engine, not on a container host alias.

To add a method, write `rpc_<name>(..., **kwargs) -> dict` in `src/mc/rpc.py` and register it in `RPC_HANDLERS`.
The UI's RPC page builds its form from the generated schema.

## Tools

Tools are commands mc can run for you, defined by a `cmd` (or `url`, not implemented yet), `args`, `env` and an
optional `input_schema` (`plugin/tools/toolindex.py`). They come from:

- built-ins: volume backup/restore, Traefik start/stop/destroy, image update, build cache prune, `gen-secret`,
- the `tools` and `commands` blocks in `mc.conf.json`,
- `*.json` files in `/etc/mc/tools` and `$MC_HOME/tools`.

`{{name}}` placeholders in `args` and `env` are filled from the request params; a missing one is an error.

- `POST /api/tools/{name}` with params as JSON body returns `[returncode, stdout, stderr]`.
- `POST /api/tools/{name}/stream?format=json|sse` streams the output line by line.

The UI's Tools page (`/admin/tools`) lists them and builds a form from `input_schema`.

## MCP

The MCP server (`src/mcp_server.py`, port 5001, `/mcp` via nginx) is a separate process and doesn't use the API's
auth. Clients send `Authorization: Bearer $MC_MCP_TOKEN`. Tools: `list_docker_hosts`, `list_tools`, `exec_tool`.
