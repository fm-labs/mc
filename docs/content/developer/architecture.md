# Architecture

mc is a single container: a FastAPI backend and a React UI, behind nginx. It manages containers on one or more
container hosts (docker, podman or other mc instances) and deploys app stacks with docker compose.

```
browser ──► nginx :3080 / :3443 (TLS)
              └─► uvicorn :5000  (FastAPI, src/server.py)
                    ├─ /api/...           REST API (JWT or API key)
                    │    ├─ containers  ──► docker / podman SDK ──► local socket, tcp://, ssh://
                    │    │              └─► NodeContainerClient ──► other mc instance (/api/containers)
                    │    ├─ inventory   ──► inventorydb ──► $MC_HOME/inventory (JSON files)
                    │    ├─ rpc         ──► mc.rpc handlers (docker, swarm, users, ssh)
                    │    ├─ tools       ──► tool index ──► subprocess (scripts in $MC_BIN_DIR)
                    │    └─ config      ──► $MC_CONFIG_DIR/mc.conf.json, ssh_config
                    └─ /              static UI (ui/dist, hash router)
            └─► /mcp ──► MCP server :5001 (FastMCP, src/mcp_server.py)
```

## Repo layout

| Path | Contents |
|---|---|
| `src/server.py` | FastAPI app: lifespan, exception handler, router, static UI mount |
| `src/mcp_server.py` | Standalone MCP server (separate process) |
| `src/cli.py` | Click CLI (`version`, `apps inspect/update/deploy`) |
| `src/mc/config.py` | Config file loading and env settings |
| `src/mc/server/` | Routers (`router.py` wires them), auth (`deps.py`, `auth_helper.py`), config and RPC routes |
| `src/mc/db.py` | Redis client (unused by default) |
| `src/mc/plugin/containers/` | Container host clients, manager and `/api/containers` routes |
| `src/mc/plugin/tools/` | Tool index (built-in and JSON-defined commands) and `/api/tools` routes |
| `src/mc/inventory/` | mc's inventory setup and core item types (`app_stack`, `secret`, `ssh_key`, ...) |
| `src/inventorydb/` | Standalone schema-driven item store (no mc imports) |
| `src/mc/docker/` | Compose runners (local and over SSH), metrics, helpers |
| `src/mc/tasks.py` | Git clone/update and compose deploy/destroy functions |
| `src/mc/rpc.py` | JSON-RPC handlers and schema generation |
| `src/mc/mcp/` | MCP app: token auth and providers from the containers and tools plugins |
| `src/mc/util/` | Subprocess, SSH, git, YAML, MongoDB helpers |
| `ui/` | React 19 + Vite + Tailwind + shadcn/ui |
| `scripts/` | Helper scripts copied to `$MC_BIN_DIR` (volume backup/restore, Traefik) |
| `container/` | Entrypoint, supervisor, nginx, redis configs for the image |
| `tests/` | pytest (`inventorydb`, `mc`) |

## Request flow

1. nginx serves the request. Anything not found as a static file goes to uvicorn on `127.0.0.1:5000`.
2. FastAPI routes `/api/...` through `app_router` (`src/mc/server/router.py`). Every router except
   `/api/info`, `/api/health` and `/api/auth/login` requires `dep_auth_user` (JWT bearer or `x-api-key`).
3. Container routes resolve the `{alias}` to a client through the `ContainerClientsManager` in `app.state.ccm`.
   Clients are created lazily on first use (see [Container hosts](container-hosts.md)).
4. Inventory routes load the item type from the registry and read/write storage. Actions (e.g. `deploy`) call
   the Python handlers registered by the item type.
5. Everything else falls through to the static UI mount at `/` (`MC_UI_HTML_DIR`, default `ui/dist`).

## Startup

On import, `server.py` calls `setup_inventory()`. The lifespan then:

- creates the `operator` admin user with a random password if `users.json` has none (`mc.setup`),
- creates the container clients manager (`app.state.ccm`),
- creates the inventory storage (`app.state.storage`) and loads all item types, so schema errors show at startup.

On shutdown, all container clients are closed.

## Not wired up (yet)

Some code exists but is not mounted or not enabled by default:

- Routers in `routes_infra.py` and `routes_stream.py` are not included in `app_router`.
- The MCP server runs as its own supervisor program, not mounted in the API app. It only offers
  `list_docker_hosts`, `list_tools` and `exec_tool` so far.
- Celery worker, Flower and redis have supervisor programs with `autostart=false`. Deploys run synchronously
  in the request.
- App stack `target_node` is ignored; deploys use `DOCKER_HOST` (see [App stacks](app-stacks.md)).
