# App specification

An app is a docker compose project that mc manages. You write the `compose.yaml`; the app spec adds what
changes per install: volumes, networks, routing and environment variables. mc turns the spec into compose
override files every time you save.

Create and edit apps under **Admin → Apps**, or with the CLI (see [CLI](#cli)).
For a walkthrough, see [Deploy an app](guides/deploy-app.md).

## Files

| File | Written by | Contents |
|---|---|---|
| `$MC_CONFIG_DIR/apps/<id>.yaml` | you (editor, CLI, API) | The app spec |
| `$MC_HOME/apps/<id>/compose.yaml` | you | The compose file |
| `$MC_HOME/apps/<id>/compose.override.yaml` | mc, on save | Volumes and networks from the spec |
| `$MC_HOME/apps/<id>/compose.traefik.yaml` | mc, on save | Routing from the spec |

Don't edit the two generated files; they're overwritten on every save. `docker compose` gets all three
compose files, in the order above.

## Spec

```yaml
# $MC_CONFIG_DIR/apps/wordpress.yaml
id: wordpress
type: compose
title: WordPress
description: Blog with a MySQL database
stackfile: compose.yaml
volumes:
  - volume_name: wp-data
    container_path: /var/www/html
    bind: true
    host_path: ./data/wp
  - volume_name: db-data
    container_path: /var/lib/mysql
networks:
  - network_name: backend
    external: true
routing:
  - service_name: wordpress
    service_port: 80
    mode: https
    domain_names: [blog.example.com, www.blog.example.com]
environment:
  WORDPRESS_DB_PASSWORD: supersecret
```

| Field | Notes |
|---|---|
| `id` | Lowercase letters, digits, `-` and `_`, up to 63 chars. Also the compose project name and the folder name. `new` is reserved. Taken from the file name; it can't be changed |
| `type` | `compose`. (`container` is reserved for single-container apps, not supported yet) |
| `title`, `description` | Shown in the UI |
| `stackfile` | Compose file name in the app folder, `compose.yaml` |
| `volumes` | See [Volumes](#volumes) |
| `networks` | See [Networks](#networks) |
| `routing` | See [Routing](#routing) |
| `environment` | See [Environment](#environment) |

## Volumes

Each entry replaces a volume of the compose file with a named volume or a host folder.

| Field | Notes |
|---|---|
| `volume_name` | Name of the volume as used in `compose.yaml` (`wp-data` in `wp-data:/var/www/html`) |
| `container_path` | Absolute path in the container |
| `bind` | `true` mounts a host folder instead of a named volume |
| `host_path` | Host folder, required with `bind`. A relative path is relative to the app folder. Missing folders are created |

- Every service that mounts `volume_name` gets the spec's mount instead. A read-only (`:ro`) mount stays
  read-only.
- If no service mounts it and the compose file has only one service, the volume is added to that service.
  Otherwise it's skipped with a warning.
- Named volumes are declared at the top level for you.

## Networks

| Field | Notes |
|---|---|
| `network_name` | Network name |
| `external` | `true` for a network that already exists on the Docker host. Compose won't create or remove it |

Every service joins every spec network and keeps its own networks (including `default`). Services with
`network_mode` are skipped with a warning.

## Routing

Routes serve a service port on one or more domains through [Traefik](https://traefik.io).

| Field | Notes |
|---|---|
| `service_name` | Service in `compose.yaml` |
| `service_port` | Port the service listens on inside the container (1-65535) |
| `mode` | `http`, `https` or `http+https` |
| `domain_names` | One or more host names. Lowercased; wildcards aren't supported |

mc assumes Traefik is already running with:

- the external Docker network `traefik-ssl`,
- entrypoints `web` (HTTP) and `websecure` (HTTPS),
- a certificate resolver named `le` (used for HTTPS).

The routed service gets the Traefik labels and joins `traefik-ssl`. Each service and port can have one route;
put all its domains in that route. A route to a service that doesn't exist, or that uses `network_mode`, is
skipped with a warning.

## Environment

Name-value pairs passed to `docker compose` when it runs, so `${NAME}` in `compose.yaml` is filled in.
They are not written to the compose files.

- Names: letters, digits and `_`, not starting with a digit.
- `DOCKER_HOST`, `COMPOSE_PROJECT_DIRECTORY` and `COMPOSE_PROJECT_NAME` are set by mc and can't be used.
- Values are stored as plain text in the spec file.

Variables only reach a container if `compose.yaml` passes them on, for example:

```yaml
services:
  wordpress:
    image: wordpress:${WP_VERSION:-latest}
    environment:
      WORDPRESS_DB_PASSWORD: ${WORDPRESS_DB_PASSWORD}
```

## Running an app

| Action | Runs |
|---|---|
| Up | `docker compose up --detach --remove-orphans` |
| Restart | `docker compose restart` |
| Stop | `docker compose stop` |
| Down | `docker compose down`. Removes containers and the app's networks; volumes are kept |

Apps run on the local Docker host (`unix:///var/run/docker.sock`).

## CLI

The CLI is `src/cli.py` (`mc-cli` when built with `build_bin.sh`). The examples use an alias:

```bash
alias mc-cli="uv run python src/cli.py"   # from the repo root

mc-cli apps list
mc-cli apps show <id>                       # env values are hidden
mc-cli apps create <id> -f compose.yaml     # -f - reads stdin; --title, --description
mc-cli apps edit <id>                       # edit the spec in $EDITOR, validated before saving
mc-cli apps edit <id> --compose             # edit compose.yaml
mc-cli apps compile <id>                    # regenerate the override files
mc-cli apps config <id>                     # print the merged compose config

mc-cli apps up <id>                         # compiles first, unless --no-compile
mc-cli apps restart|stop|down <id>

mc-cli apps env list <id> [--show-values]
mc-cli apps env set <id> NAME=VALUE ...     # NAME alone prompts for a hidden value
mc-cli apps env unset <id> NAME ...
```

`list` and `show` also take `--json`. The CLI reads `MC_HOME` and `MC_CONFIG_DIR` like the server, so
run it with the same env (inside the mc container, or with `.env.local` in development).
