# Apps

The apps plugin manages compose apps from app specs. It replaces [app stacks](app-stacks.md), which are
obsolete. The user-facing format is in the [App specification](../apps.md).

| Code | Contents |
|---|---|
| `src/mc/plugin/apps/apps_helper.py` | `AppSpec` and its parts, validation, load/save/list, `compile()`, compose commands |
| `src/mc/plugin/apps/compose_override.py` | `build_override` (volumes, networks) and `build_traefik_override` (routing) |
| `src/mc/plugin/apps/routes.py` | `/api/apps` routes |
| `src/mc/cli/apps.py` | `apps` CLI group |
| `src/mc/docker/compose_runner.py` | `LocalDockerComposeStackRunner`: builds and runs `docker compose` commands |
| `ui/src/app/apps/` | List page, editor page, section editors, run panel, compiled-files dialog |
| `ui/src/features/apps/` | Types and client-side validation (mirrors the pydantic validators) |

## Storage

- Spec: `$MC_CONFIG_DIR/apps/<id>.yaml`, written by `save_app_spec()` with `exclude_none`. `load_app_spec()`
  takes the id from the file name. `list_app_specs()` skips files that don't validate.
- Project folder: `$MC_HOME/apps/<id>/` with the stackfile and the generated files.
- All writes go through `write_file_atomic()` (temp file in the same folder, then `os.replace`).

## Compile

`AppSpec.compile()` reads the stackfile and writes two files; it returns warnings for parts it couldn't apply.
The API and the CLI compile on every save, and `apps up` in the CLI compiles before starting.

- `compose.override.yaml` from `build_override()`: volumes and networks.
- `compose.traefik.yaml` from `build_traefik_override()`: routing.

Compose merges override files in ways that don't fit, so the generated files use the `!override` tag
(compose 2.24.4 or later) to replace a list or mapping instead:

- Service `volumes` merge by mount target, so a plain override would keep the original mount next to the new
  one. Changed services get their full `volumes` list rewritten.
- Setting service `networks` drops the implicit `default` network. The full mapping is written, including
  `default` for services that had no `networks`.

`compose.traefik.yaml` is applied last, so its service `networks` include the service's own networks, the spec
networks and `traefik-ssl` (`_spec_service_networks()`). Labels merge normally, so the compose file's labels
are kept.

Traefik names are `<app>-<service>-<port>` with anything but letters, digits, `-` and `_` replaced by `-`.
Every router sets `.service`, so a container can have routes on several ports. The network, entrypoints and
cert resolver are constants in `compose_override.py` (`TRAEFIK_*`).

## Running compose

`AppSpec.compose_runner()` returns a `LocalDockerComposeStackRunner` with:

- `--project-directory` set to the **host** path of the project folder (`get_mc_real_path()`), so relative bind
  mounts resolve on the host when mc runs in a container. In development, set `MC_HOST_HOME` to `MC_HOME`.
- `--file` for the stackfile plus each generated file that exists (`stackfile_paths()`).
- `env`: the spec's `environment` on top of `os.environ`, then `DOCKER_HOST` (always the local socket),
  `COMPOSE_PROJECT_DIRECTORY` and `COMPOSE_PROJECT_NAME`, which win over the spec.

`compose_cmd()` builds `(cmd, env)` without running it. `AppSpec.action_cmd(action, global_args)` builds the
command for `up` (always `--detach`, so it exits), `down`, `stop` and `restart`. The API runs it as a streamed
subprocess; the CLI runs it attached to the terminal.

## API

All routes need auth, like the other routers.

| Route | Does |
|---|---|
| `GET /api/apps` | List specs |
| `POST /api/apps/new/scratch` | Create from a compose file: `id`, `title`, `description`, `stackfile_content`, `volumes`, `networks`, `environment`, `routing`. Compiles. `409` if the id exists |
| `POST /api/apps/new/bundle` | Not implemented (`501`) |
| `GET /api/apps/{id}` | Spec, compose file, generated files and editor hints (below) |
| `PUT /api/apps/{id}` | Update. Omitted fields keep their value; `stackfile_content` rewrites the compose file. Compiles |
| `GET /api/apps/{id}/compiled` | The compose files in order, and the `docker compose config` output (or `merged_error`) |
| `POST /api/apps/{id}/action/{action}` | Run `up`, `down`, `stop` or `restart`, streamed |

Create and update return `compile_warnings`. Invalid specs return `422` with pydantic's error list (without
input values); a bad compose file or id returns `400`.

Editor hints in the details: `compose_volumes` and `compose_networks` (top-level names in the compose file) and
`compose_services` (service name to the container ports in `ports` and `expose`).

The action route streams like the tool stream: newline-delimited JSON (`?format=sse` for server-sent events)
with `STDOUT` lines, then `RC` with the exit code, or `ERROR`. compose runs with `--progress plain --ansi never`
so the output is line-based. If the client disconnects, the subprocess is terminated.

## UI

`/admin/apps` lists the specs, `/admin/apps/new` and `/admin/apps/:appId` open the editor
(`app-spec-edit-page.tsx`). Each spec section has its own component in `components/`; they get rows and per-row
errors from `apps-validation.ts`. The editor keeps form state as rows (env and routes as strings while typing)
and converts them on save.

The service and port hints come from the last saved compose file; the UI doesn't parse unsaved YAML.

## Not done yet

- Deleting an app (API, UI, CLI).
- `container` apps (`type: container`, `image`).
- Creating from a bundle or template.
- Remote Docker hosts: apps always use the local socket.
