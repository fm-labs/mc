# Runtime and configuration

## Container image

`Dockerfile` builds in three stages:

1. **ui-builder** (node alpine): `pnpm install` and `pnpm run build` in `ui/`.
2. **app-builder** (python alpine): installs Python deps with `uv sync --no-dev --locked` and copies `src/`.
3. **final** (python alpine): installs docker-cli, compose, buildx, git, openssh, nginx, supervisor, aws-cli;
   copies `/app` from app-builder, the built UI to `/app/ui`, and `container/bin/*` and `scripts/*` to
   `/app/bin` (on `PATH`). Scripts stay outside the data volume, so image updates replace them.

The container runs as user `app` (uid/gid 33333). `install.sh` adds the docker socket's group with `--group-add`
so `app` can use the mounted socket.

| Port | Served by |
|---|---|
| 3080 | nginx, HTTP |
| 3443 | nginx, HTTPS (self-signed cert unless you mount one) |
| 5000 | uvicorn, internal only |
| 5001 | MCP server, internal only (nginx proxies `/mcp` to it) |

## Processes

`entrypoint supervisor` starts supervisord. Each program calls `entrypoint <name>`:

| Program | Autostart | What it runs |
|---|---|---|
| `api` | yes | `uvicorn server:app` on `0.0.0.0:5000` |
| `nginx` | yes | Creates a self-signed cert and dhparam in `$MC_CONFIG_DIR/ssl` on first start, then nginx |
| `ssh-agent` | yes | ssh-agent at `/ssh-agent/agent.sock`, loads keys with `ssh-add-all`, then keeps it alive |
| `mcp-server` | yes | `src/mcp_server.py` with streamable HTTP on `0.0.0.0:5001`, path `/mcp` (experimental) |
| `redis`, `celery-worker`, `celery-flower`, `scan` | no | Not used by default |

The healthcheck calls `GET /api/health` on port 3080.

`entrypoint` also exports `SSH_AUTH_SOCK`, and sets `GIT_SSH_COMMAND` and `DOCKER_SSH_COMMAND` to
`ssh -F $SSH_CONFIG` (default `/home/app/.ssh/config`), so git and docker over SSH use the same keys and config.

## Directories

| Path | Env var | Default (image) | Contents |
|---|---|---|---|
| Data | `MC_HOME` | `/var/lib/mc` | Everything persistent (mounted as the `mc-data` volume) |
| Config | `MC_CONFIG_DIR` | `/var/lib/mc/etc` | `mc.conf.json`, `users.json`, `ssh_config`, `ssl/`, `ssh_keys/`, `inventory/` (user types), `inventory.toml` |
| Inventory | | `$MC_HOME/inventory` | Stored items |
| Apps | | `$MC_HOME/apps/<stack id>` | Working dir of each app stack |
| Repo cache | | `$MC_HOME/cache/repos` | Git checkouts of stack repositories |
| Bin | `MC_BIN_DIR` | `/app/bin` (local: `./scripts`) | Helper scripts used by tools (`mc-docker-volume-*.sh`, `mc-traefik-*.sh`) |
| Tools | | `/etc/mc/tools`, `$MC_HOME/tools` | Tool definitions (`*.json`), see [API](api.md#tools) |
| Backups | `MC_BACKUP_DIR` | `/tmp/backup` | Volume backup target. It's passed to docker, so it's a path **on the host** |
| UI | `MC_UI_HTML_DIR` | `/app/ui` | Built UI |

Running locally without the env vars, `MC_HOME` defaults to `/var/lib/mc` too, so set `MC_HOME` in `.env.local`
for development.

## Config file

`mc.config.load_config()` reads `mc.conf.json` from `/etc/mc` and then `$MC_HOME/etc`, and deep-merges them
(later wins). It's read once at import; changes need a restart.

```json
{
  "environment": { "MC_API_KEY": "a-long-random-key" },
  "docker_hosts": { "localhost": { "url": "unix:///var/run/docker.sock" } }
}
```

- `environment`: values here take precedence over real env vars for settings read with `get_env_var()`.
- `docker_hosts`: see [Container hosts](container-hosts.md).

`.env` and `.env.local` in the working dir are loaded with `python-dotenv` before anything else.

## Settings

| Variable | Default | Purpose |
|---|---|---|
| `MC_DEV_MODE` | `false` | Enables `/docs`, `/redoc` and `/api/openapi.json` |
| `MC_API_KEY` | none | Enables `x-api-key` auth (must be more than 8 chars). Used by nodes |
| `JWT_SECRET_KEY` | random per start | Signs login tokens. Unset means a restart logs everyone out |
| `INVENTORY_STORAGE` | `directory` | `directory`, `file` or `sqlite` |
| `INVENTORY_USER_CODE` | `false` | Load Python modules of user item types |
| `MC_API_CONF_MC_WRITABLE` | unset | `1` allows editing `mc.conf.json` from the Settings page |
| `MC_API_CONF_SSH_WRITABLE` | unset | `1` allows editing `ssh_config` from the Settings page |
| `MC_CORS_ENABLED` / `MC_CORS_ALLOWED_ORIGINS` | `true` / `*` | CORS middleware on the API |
| `MC_MCP_ENABLED` | `true` | MCP server accepts tokens. `false` denies every request |
| `MC_MCP_TOKEN` | random per start | Bearer token for the MCP server. With `MC_DEV_MODE`, any token starting with `dev-` works |
| `MCP_TRANSPORT`, `MCP_HOST`, `MCP_PORT`, `MCP_PATH` | `stdio`, `127.0.0.1`, `5001`, `/mcp` | MCP server; the entrypoint's `mcp-server-http` sets `streamable-http` on `0.0.0.0` |
| `DOCKER_HOST` | `unix:///var/run/docker.sock` | Target of app stack deploys |

The `*_WRITABLE` flags are read from the real process env only, so `mc.conf.json` can't grant itself write access.

## Users

Users live in `$MC_CONFIG_DIR/users.json`, one `username:bcrypt-hash` per line (`mc/users.py`). On first start the
`operator` user is created and its password is printed to the log once.
