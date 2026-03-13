#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from typing import Any, Dict, Optional

import click

from mc.credentials_manager import update_credentials, remove_credentials, get_credentials, add_credentials
from mc.vault import open_vaultfile

# ----------------------------- Helpers ---------------------------------- #

def _stdin_has_data() -> bool:
    # True if data is being piped into stdin (not a TTY)
    return not sys.stdin.isatty()


def _read_json_from_stdin() -> Dict[str, Any]:
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            raise click.BadParameter("No JSON received on stdin.")
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise click.BadParameter("Expected a JSON object at top level.")
        return data
    except json.JSONDecodeError as e:
        raise click.BadParameter(f"Invalid JSON on stdin: {e}") from e


def _interactive_collect_credentials() -> Dict[str, Any]:
    """
    Prompt user for key/value pairs without echoing *values* if desired.
    Finish by entering an empty key.
    """
    creds: Dict[str, Any] = {}
    click.echo("Entering interactive mode. Leave key empty to finish.")
    while True:
        key = click.prompt("Key name", default="", show_default=False)
        if not key:
            break

        hide = click.confirm(f"Hide value input for '{key}'? (recommended for secrets)", default=True)
        value = click.prompt(f"Value for '{key}'", hide_input=hide)

        # Basic type coercion:
        # Try bool/null/int/float; otherwise keep string
        v_lower = str(value).lower()
        if v_lower in ("true", "false"):
            parsed: Any = (v_lower == "true")
        elif v_lower in ("null", "none"):
            parsed = None
        else:
            try:
                parsed = int(value) if value.isdigit() else float(value)
            except ValueError:
                parsed = value

        creds[key] = parsed

    if not creds:
        raise click.BadParameter("No credentials provided.")
    return creds


def _gather_credentials(interactive: bool) -> Dict[str, Any]:
    """
    Input policy:
      - If stdin has data: read JSON from stdin.
      - Else if interactive: prompt for keys/values.
      - Else: error out (to avoid exposing secrets on CLI).
    """
    if _stdin_has_data():
        return _read_json_from_stdin()
    if interactive:
        return _interactive_collect_credentials()
    raise click.BadParameter(
        "No credentials provided. Either pipe JSON on stdin or enable --interactive."
    )


# ----------------------------- Helpers ---------------------------------- #

def ask_password(prompt: str = "Enter password") -> str:
    return click.prompt(prompt, hide_input=True)


# ----------------------------- CLI Group -------------------------------- #

@click.group()
def credentials():
    pass


# ----------------------------- Commands --------------------------------- #

@credentials.command("add")
@click.argument("vaultfile")
@click.argument("name")
@click.pass_context
def cmd_add(ctx: click.Context, vaultfile: str, name: str):
    """
    Add a credential set.

    VAULTFILE is the path to a vault .yaml/.yml/.toml file.
    NAME is the unique credential name.

    Credentials are read from JSON on stdin or entered interactively.
    """
    with open_vaultfile(vaultfile, mode="w") as decrypted_file:
        creds = _gather_credentials(ctx.obj["interactive"])
        add_credentials(decrypted_file.name, name, creds)
        click.echo(f"Added credential '{name}' to {vaultfile}.")


@credentials.command("update")
@click.argument("vaultfile")
@click.argument("name")
@click.pass_context
def cmd_update(ctx: click.Context, vaultfile: str, name: str):
    """
    Update (change) keys for an existing credential set.

    VAULTFILE is the path to a vault .yaml/.yml/.toml file.
    NAME is the credential name to modify.

    Reads JSON from stdin or prompts interactively.
    """
    with open_vaultfile(vaultfile, mode="w") as decrypted_file:
        creds = _gather_credentials(ctx.obj["interactive"])
        update_credentials(decrypted_file.name, name, creds)
        click.echo(f"Updated credential '{name}' in {vaultfile}.")


@credentials.command("remove")
@click.argument("vaultfile")
@click.argument("name")
@click.option("--yes", "-y", is_flag=True, default=False, help="Do not prompt for confirmation.")
def cmd_remove(vaultfile: str, name: str, yes: bool):
    """
    Remove a credential set.

    VAULTFILE is the path to a vault .yaml/.yml/.toml file.
    NAME is the credential name to remove.
    """
    if not yes:
        click.confirm(f"Remove credential '{name}' from {vaultfile}?", abort=True)

    with open_vaultfile(vaultfile, mode="w") as decrypted_file:
        remove_credentials(decrypted_file.name, name)
        click.echo(f"Removed credential '{name}' from {vaultfile}.")


@credentials.command("show")
@click.argument("vaultfile")
@click.argument("name", required=False, default=None)
def cmd_show(vaultfile: str, name: Optional[str]):
    """
    Show credentials (all or one).

    VAULTFILE is the path to a vault .yaml/.yml/.toml file.
    NAME is the optional credential name to show (omit to show all).
    """
    with open_vaultfile(vaultfile, mode="r") as f:
        creds = get_credentials(f.name, name)
        click.echo(json.dumps(creds, indent=2, sort_keys=True))


# ----------------------------- Entrypoint -------------------------------- #

if __name__ == "__main__":
    cli()