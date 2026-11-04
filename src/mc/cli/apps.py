"""
`mc apps`: manage app specs ($MC_CONFIG_DIR/apps/<id>.yaml) and run their compose stacks.
"""
import json
import os
import subprocess
import sys
from contextlib import contextmanager
from typing import Iterator

import click
import pydantic
import yaml

from mc.plugin.apps.apps_helper import (
    AppSpec,
    app_spec_exists,
    get_appspec_path,
    list_app_specs,
    load_app_spec,
    save_app_spec,
    validate_app_id,
    validate_compose_stackfile,
)


@contextmanager
def _errors() -> Iterator[None]:
    """Turn spec errors into clean CLI errors instead of tracebacks."""
    try:
        yield
    except pydantic.ValidationError as e:
        lines = [f"  {'.'.join(str(p) for p in err['loc']) or 'spec'}: {err['msg']}" for err in e.errors()]
        raise click.ClickException("Invalid app spec:\n" + "\n".join(lines)) from e
    except (ValueError, FileNotFoundError, RuntimeError) as e:
        raise click.ClickException(str(e)) from e


def _load(app_id: str) -> AppSpec:
    with _errors():
        return load_app_spec(app_id)


def _compile(spec: AppSpec) -> None:
    """Regenerate the override files and print any warnings."""
    if spec.type != "compose":
        return
    with _errors():
        warnings = spec.compile()
    for w in warnings:
        click.secho(f"Warning: {w}", fg="yellow", err=True)


def _save(spec: AppSpec) -> None:
    with _errors():
        save_app_spec(spec)
    _compile(spec)
    click.echo(f"Saved {get_appspec_path(spec.id)}")


def _run(spec: AppSpec, cmd: list[str], env: dict[str, str]) -> None:
    """Run a compose command attached to the terminal and exit with its return code."""
    if spec.stackfile and not os.path.isfile(spec.stackfile_path):
        raise click.ClickException(f"Compose file not found: {spec.stackfile_path}")
    try:
        rc = subprocess.run(cmd, env=env).returncode
    except FileNotFoundError as e:
        raise click.ClickException("docker CLI not found") from e
    if rc != 0:
        sys.exit(rc)


@click.group()
def apps():
    """Manage apps and run their compose stacks."""


@apps.command("list")
@click.option("--json", "as_json", is_flag=True, help="Print JSON")
def list_apps(as_json: bool):
    """List app specs."""
    specs = list_app_specs()
    if as_json:
        click.echo(json.dumps([s.model_dump(mode="json") for s in specs], indent=2))
        return
    if not specs:
        click.echo("No apps. Create one with: mc apps create <id> -f compose.yaml")
        return
    width = max(len(s.id) for s in specs)
    for s in specs:
        routes = ", ".join(d for r in s.routing for d in r.domain_names)
        click.echo(f"{s.id:<{width}}  {s.type:<9}  {s.title or ''}" + (f"  [{routes}]" if routes else ""))


@apps.command("show")
@click.argument("app_id")
@click.option("--json", "as_json", is_flag=True, help="Print JSON")
def show_app(app_id: str, as_json: bool):
    """Show an app spec and its file paths. Environment values are hidden."""
    spec = _load(app_id)
    data = spec.model_dump(mode="json", exclude_none=True)
    data["environment"] = {k: "****" for k in spec.environment}
    if as_json:
        click.echo(json.dumps(data, indent=2))
        return
    click.echo(f"# {get_appspec_path(spec.id)}")
    if spec.stackfile:
        click.echo(f"# compose files: {', '.join(spec.stackfile_paths())}")
    click.echo(yaml.safe_dump(data, sort_keys=False).rstrip())


@apps.command("create")
@click.argument("app_id")
@click.option("-f", "--file", "compose_file", type=click.File("r"), required=True,
              help="compose.yaml to start from ('-' for stdin)")
@click.option("--title", help="Display title")
@click.option("--description", help="Description")
def create_app(app_id: str, compose_file, title: str | None, description: str | None):
    """Create a compose app from a compose.yaml."""
    with _errors():
        validate_app_id(app_id)
        if app_spec_exists(app_id):
            raise click.ClickException(f"App '{app_id}' already exists")
        spec = AppSpec.create_from_string(app_id, compose_file.read(), title=title, description=description)
    _compile(spec)
    click.echo(f"Created {get_appspec_path(spec.id)}")


@apps.command("edit")
@click.argument("app_id")
@click.option("--compose", "edit_compose", is_flag=True, help="Edit compose.yaml instead of the spec")
def edit_app(app_id: str, edit_compose: bool):
    """
    Edit an app spec (volumes, networks, routing, environment, ...) or its compose.yaml in $EDITOR.

    The result is validated before it's saved. Saving regenerates the override files.
    """
    spec = _load(app_id)
    if edit_compose:
        with _errors():
            text = spec.read_stackfile()
    else:
        with open(get_appspec_path(app_id)) as f:
            text = f.read()

    while True:
        edited = click.edit(text, extension=".yaml")
        if edited is None or edited == text:
            click.echo("No changes.")
            return
        try:
            with _errors():
                if edit_compose:
                    validate_compose_stackfile(edited)
                    spec.write_stackfile(edited)
                    new_spec = spec
                else:
                    data = yaml.safe_load(edited) or {}
                    if not isinstance(data, dict):
                        raise ValueError("App spec must be a YAML mapping")
                    if data.get("id", app_id) != app_id:
                        raise ValueError("The app id can't be changed")
                    new_spec = AppSpec.model_validate({**data, "id": app_id})
        except (click.ClickException, yaml.YAMLError) as e:
            click.secho(e.format_message() if isinstance(e, click.ClickException) else f"Invalid YAML: {e}",
                        fg="red", err=True)
            if not click.confirm("Edit again?", default=True):
                raise click.Abort()
            text = edited
            continue
        break

    if edit_compose:
        _compile(new_spec)
        click.echo(f"Saved {new_spec.stackfile_path}")
    else:
        _save(new_spec)


@apps.command("compile")
@click.argument("app_id")
def compile_app(app_id: str):
    """Regenerate compose.override.yaml and compose.traefik.yaml from the spec."""
    spec = _load(app_id)
    if spec.type != "compose":
        raise click.ClickException("Only compose apps can be compiled")
    _compile(spec)
    for path in spec.stackfile_paths()[1:]:
        click.echo(f"Wrote {path}")


@apps.command("config")
@click.argument("app_id")
def config_app(app_id: str):
    """Print the merged compose config (`docker compose config`)."""
    spec = _load(app_id)
    with _errors():
        cmd, env = spec.compose_runner().compose_cmd("config")
    _run(spec, cmd, env)


def _run_action(app_id: str, action: str, compile_first: bool = False) -> None:
    spec = _load(app_id)
    if compile_first:
        _compile(spec)
    with _errors():
        cmd, env = spec.action_cmd(action)  # type: ignore[arg-type]
    _run(spec, cmd, env)


@apps.command("up")
@click.argument("app_id")
@click.option("--no-compile", is_flag=True, help="Don't regenerate the override files first")
def up_app(app_id: str, no_compile: bool):
    """Start the app (docker compose up --detach). Compiles the spec first."""
    _run_action(app_id, "up", compile_first=not no_compile)


def _add_action_command(action: str, help_text: str) -> None:
    @apps.command(action, help=help_text)
    @click.argument("app_id")
    def command(app_id: str):
        _run_action(app_id, action)


for _action, _help in (
        ("down", "Stop and remove the app's containers (docker compose down)."),
        ("stop", "Stop the app's containers (docker compose stop)."),
        ("restart", "Restart the app's containers (docker compose restart)."),
):
    _add_action_command(_action, _help)


# ----------------------------- env ---------------------------------- #

@apps.group("env")
def env():
    """Environment variables passed to docker compose (never written to compose files)."""


@env.command("list")
@click.argument("app_id")
@click.option("--show-values", is_flag=True, help="Print values instead of ****")
def env_list(app_id: str, show_values: bool):
    """List an app's environment variables."""
    spec = _load(app_id)
    for name, value in spec.environment.items():
        click.echo(f"{name}={value if show_values else '****'}")


def _parse_assignment(arg: str) -> tuple[str, str | None]:
    """NAME=VALUE, or NAME alone to be prompted for the value."""
    name, sep, value = arg.partition("=")
    return name.strip(), (value if sep else None)


@env.command("set")
@click.argument("app_id")
@click.argument("assignments", nargs=-1, required=True)
def env_set(app_id: str, assignments: tuple[str, ...]):
    """
    Set variables: NAME=VALUE ... Pass NAME alone to type the value hidden (for secrets).
    """
    spec = _load(app_id)
    environment = dict(spec.environment)
    for arg in assignments:
        name, value = _parse_assignment(arg)
        if value is None:
            value = click.prompt(f"Value for {name}", hide_input=True, default="", show_default=False)
        environment[name] = value
    with _errors():
        spec = AppSpec.model_validate({**spec.model_dump(), "environment": environment})
    _save(spec)


@env.command("unset")
@click.argument("app_id")
@click.argument("names", nargs=-1, required=True)
def env_unset(app_id: str, names: tuple[str, ...]):
    """Remove variables."""
    spec = _load(app_id)
    missing = [n for n in names if n not in spec.environment]
    if missing:
        click.secho(f"Not set: {', '.join(missing)}", fg="yellow", err=True)
    environment = {k: v for k, v in spec.environment.items() if k not in names}
    if environment == spec.environment:
        return
    with _errors():
        spec = AppSpec.model_validate({**spec.model_dump(), "environment": environment})
    _save(spec)
