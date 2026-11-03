# App stacks

An app stack is an inventory item (`app_stack`) that points to a compose project in a git repository.
mc copies the project into a working dir, adds its own overrides and runs `docker compose`.

Code: `../../../src/mc/plugin/apps/inventory/app_stack` · Compose runners: `src/mc/docker/compose_runner.py` ·
Deploy/destroy: `src/mc/tasks.py`

## Item

```json
{
  "id": "wordpress",
  "type": "compose",
  "label": "WordPress",
  "repository": { "url": "https://github.com/me/stacks.git", "path": "wordpress", "private": false },
  "stackfile": "compose.yaml",
  "environment": { "WP_ADMIN_USER": "admin" },
  "proxy_enabled": true,
  "proxy_https_enabled": true,
  "domain_name": "blog.example.com",
  "proxy_service_name": "wordpress",
  "proxy_container_port": 80
}
```

The `id` is the compose project name and the working dir name: `$MC_HOME/apps/<id>`.

## Actions

The actions are registered in `__init__.py` (`actions` dict) and offered in the UI through `meta.json`.

| Action | Handler | What it does |
|---|---|---|
| `sync` | `handle_app_stack_action_sync` | Clones or pulls the repo into `$MC_HOME/cache/repos/...`, then copies `repository.path` into the working dir (skips `.git`, `.github`, ...). `wipe_working_dir` deletes the working dir first |
| `configure` | `handle_app_stack_action_configure` | Saves `environment` on the item (drops empty values), then runs `prepare` |
| `deploy` | `handle_app_stack_action_deploy` | Needs `confirm: true`. Runs `prepare`, then `compose stop`, `up -d` |
| `redeploy` | `handle_app_stack_redeploy` | Needs `confirm: true`. Optional `sync`, then `configure` and `deploy` |
| `destroy` | `handle_app_stack_action_destroy` | Needs `confirm: true`. `compose down` |

Views: `template` (the stack's `template.json`) and `stackfile` (the compose file content).

`prepare` (internal) writes two files into the working dir:

- `.env` from `environment`, rewritten every time,
- `compose.override.yaml` with labels `mc.app.managed=true`, `mc.app.name=<id>`, and Traefik labels
  if `proxy_enabled` (see below).

## Compose files

`deploy` passes these files to compose, in this order, when they exist:

1. `stackfile` (e.g. `compose.yaml`)
2. `compose.override.yaml` (written by `prepare`)
3. `mc.override.yaml` (hand-written by the user, for local changes that survive a sync)

If `stackfile` is empty, no `-f` is passed and compose uses its own defaults.

## Private repositories

- **HTTPS:** set `repository.private` and `repository.auth.username` / `.password`. They are put into the URL.
- **SSH:** set `repository.private` and `repository.ssh_key_id`. The key must be at
  `$MC_HOME/etc/ssh_keys/<ssh_key_id>.pem`.

## Proxy (Traefik)

With `proxy_enabled`, mc assumes a Traefik instance on an external docker network and adds to
`proxy_service_name`: the network (`proxy_network_name`, default `traefik-ssl` in code, though the schema text
says `traefik`), `traefik.enable`, the service port, and routers for `domain_name` on the `web` entrypoint
(`proxy_http_enabled`) and/or `websecure` with cert resolver `le` (`proxy_https_enabled`).
`domain_name`, `proxy_service_name` and `proxy_container_port` are required then.

## Where it runs

`deploy` and `destroy` target `DOCKER_HOST` (default `unix:///var/run/docker.sock`). `target_node` is not used yet.
`get_compose_runner()` picks `LocalDockerComposeStackRunner` for `unix://` and `RemoteDockerComposeStackRunner`
(rsync + compose over SSH, with optional pre/post hook scripts) for `ssh://`.

Deploys run synchronously inside the HTTP request. The `background` flag is accepted but ignored, since the
celery worker is disabled.

## CLI

```bash
uv run python src/cli.py apps inspect <id>
uv run python src/cli.py apps update <id> [--check]
uv run python src/cli.py apps deploy <id> [--dry-run]
```
