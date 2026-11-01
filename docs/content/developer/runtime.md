# Runtime and configuration

## Container image

`Dockerfile` builds in two stages:

1. **ui-builder** (node alpine): `pnpm install` and `pnpm run build` in `ui/`.
2. **runtime** (python alpine): installs docker-cli, compose, buildx, git, openssh, nginx, supervisor, aws-cli;
   installs Python deps with `uv sync --no-dev --locked`; copies `src/`, `resources/` and the built UI to `/app/ui`.

The container runs as user `app` (uid/gid 33333). `install.sh` adds the docker socket's group with `--group-add`
so `app` can use the mounted socket.

| Port | Served by |
|---|---|
| 3080 | nginx, HTTP |
| 3443 | nginx, HTTPS (self-signed cert unless you mount one) |
| 5000 | uvicorn, internal only |

## Processes

`entrypoint supervisor` starts supervisord. Each program calls `entrypoint <name>`:

| Program | Autostart | What it runs |
|---|---|---|
| `api` | yes | `uvicorn server:app` on `0.0.0.0:5000` |
| `nginx` | yes | Creates a self-signed cert and dhparam in `$CONFIG_DIR/ssl` on first start, then nginx |
| `ssh-agent` | yes | ssh-agent at `/ssh-agent/agent.sock`, loads keys with `ssh-add-all`, then keeps it alive |
| `redis`, `celery-worker`, `celery-flower`, `scan` | no | Not used by default |

The healthcheck calls `GET /api/health` on port 3080.

`entrypoint` also exports `SSH_AUTH_SOCK`, and sets `GIT_SSH_COMMAND` and `DOCKER_SSH_COMMAND` to
`ssh -F $SSH_CONFIG` (default `/home/app/.ssh/config`), so git and docker over SSH use the same keys and config.

## Directories

| Path | Env var | Default (image) | Contents |
|---|---|---|---|
| Data | `DATA_DIR` | `/opt/mc` | Everything persistent (mounted as the `mc-data` volume) |
| Config | `CONFIG_DIR` | `/opt/mc/etc` | `mc.conf.json`, `users.json`, `ssh_config`, `ssl/`, `ssh_keys/`, `inventory/` (user types), `inventory.toml` |
| Inventory | | `$DATA_DIR/inventory` | Stored items |
| Apps | | `$DATA_DIR/apps/<stack id>` | Working dir of each app stack |
| Repo cache | | `$DATA_DIR/cache/repos` | Git checkouts of stack repositories |
| UI | `STATIC_UI_DIR` | `/app/ui` | Built UI |
| Resources | `RESOURCES_DIR` | `/app/resources` | Bundled resources |

Running locally without the env vars, `DATA_DIR` defaults to `/opt/mc` too, so set `DATA_DIR` in `.env.local`
for development.

## Config file

`mc.config.load_config()` reads `mc.conf.json` from `/etc/mc` and then `$DATA_DIR/etc`, and deep-merges them
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
| `DEV_MODE` | `false` | Enables `/docs`, `/redoc` and `/api/openapi.json` |
| `MC_API_KEY` | none | Enables `x-api-key` auth (must be more than 8 chars). Used by nodes |
| `JWT_SECRET_KEY` | random per start | Signs login tokens. Unset means a restart logs everyone out |
| `INVENTORY_STORAGE` | `directory` | `directory`, `file` or `sqlite` |
| `INVENTORY_USER_CODE` | `false` | Load Python modules of user item types |
| `MC_API_CONF_MC_WRITABLE` | unset | `1` allows editing `mc.conf.json` from the Settings page |
| `MC_API_CONF_SSH_WRITABLE` | unset | `1` allows editing `ssh_config` from the Settings page |
| `MCP_ENABLED` / `MCP_TRANSPORT` | `false` / `streamable-http` | MCP server (not mounted, see [Architecture](architecture.md#not-wired-up-yet)) |
| `DOCKER_HOST` | `unix:///var/run/docker.sock` | Target of app stack deploys |

The `*_WRITABLE` flags are read from the real process env only, so `mc.conf.json` can't grant itself write access.

## Users

Users live in `$CONFIG_DIR/users.json`, one `username:bcrypt-hash` per line (`mc/users.py`). On first start the
`operator` user is created and its password is printed to the log once.
