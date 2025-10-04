#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from contextlib import contextmanager
from tempfile import NamedTemporaryFile
from typing import Any, Dict, Optional

import typer

from xvault.backend.ansible_vault import run_ansible_vault
from xvault.credentials import add_credentials, update_credentials, remove_credentials, get_credentials

app = typer.Typer(no_args_is_help=True, add_completion=False)


# ----------------------------- Helpers ---------------------------------- #

def _stdin_has_data() -> bool:
    # True if data is being piped into stdin (not a TTY)
    return not sys.stdin.isatty()


def _read_json_from_stdin() -> Dict[str, Any]:
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            raise typer.BadParameter("No JSON received on stdin.")
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise typer.BadParameter("Expected a JSON object at top level.")
        return data
    except json.JSONDecodeError as e:
        raise typer.BadParameter(f"Invalid JSON on stdin: {e}") from e


def _interactive_collect_credentials() -> Dict[str, Any]:
    """
    Prompt user for key/value pairs without echoing *values* if desired.
    Finish by entering an empty key.
    """
    creds: Dict[str, Any] = {}
    typer.echo("Entering interactive mode. Leave key empty to finish.")
    while True:
        key = typer.prompt("Key name", default="", show_default=False)
        if not key:
            break

        hide = typer.confirm(f"Hide value input for '{key}'? (recommended for secrets)", default=True)
        value = typer.prompt(f"Value for '{key}'", hide_input=hide)

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
        raise typer.BadParameter("No credentials provided.")
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
    raise typer.BadParameter(
        "No credentials provided. Either pipe JSON on stdin or enable --interactive."
    )


# ---------------------------- Global flags ------------------------------- #

@app.callback()
def _main(
    ctx: typer.Context,
    interactive: bool = typer.Option(
        True,
        "--interactive/--no-interactive",
        help="Interactively prompt for credentials when not reading JSON from stdin.",
        show_default=True,
    ),
):
    """
    Manage raw unencrypted vault credentials (YAML or TOML), without exposing secrets
    on the command line. For 'add' and 'update', supply credentials via JSON on stdin
    or via interactive prompts.
    """
    ctx.obj = {"interactive": interactive}


# ----------------------------- Helpers ---------------------------------- #
def ask_password(prompt: str = "Enter password") -> str:
    return typer.prompt(prompt, hide_input=True)

# ----------------------------- Commands --------------------------------- #

@app.command("add")
def cmd_add(
    ctx: typer.Context,
    vaultfile: str = typer.Argument(..., help="Path to vault .yaml/.yml/.toml"),
    name: str = typer.Argument(..., help="Credential name (unique)"),
):
    """
    Add a credential set. Credentials are read from JSON on stdin or entered interactively.
    """
    with open_vaultfile(vaultfile, mode="w") as decrypted_file:
        creds = _gather_credentials(ctx.obj["interactive"])
        add_credentials(decrypted_file.name, name, creds)
        typer.echo(f"Added credential '{name}' to {vaultfile}.")



@app.command("update")
def cmd_update(
    ctx: typer.Context,
    vaultfile: str = typer.Argument(..., help="Path to vault .yaml/.yml/.toml"),
    name: str = typer.Argument(..., help="Credential name to modify"),
):
    """
    Update (change) keys for an existing credential set. Reads JSON from stdin or prompts.
    """
    with open_vaultfile(vaultfile, mode="w") as decrypted_file:
        creds = _gather_credentials(ctx.obj["interactive"])
        update_credentials(decrypted_file.name, name, creds)
        typer.echo(f"Updated credential '{name}' in {vaultfile}.")


@app.command("remove")
def cmd_remove(
    vaultfile: str = typer.Argument(..., help="Path to vault .yaml/.yml/.toml"),
    name: str = typer.Argument(..., help="Credential name to remove"),
    yes: bool = typer.Option(
        False, "--yes", "-y", help="Do not prompt for confirmation."
    ),
):
    """Remove a credential set."""
    if not yes:
        typer.confirm(f"Remove credential '{name}' from {vaultfile}?", abort=True)

    with open_vaultfile(vaultfile, mode="w") as decrypted_file:
        remove_credentials(decrypted_file.name, name)
        typer.echo(f"Removed credential '{name}' from {vaultfile}.")


@app.command("show")
def cmd_show(
    vaultfile: str = typer.Argument(..., help="Path to vault .yaml/.yml/.toml"),
    name: Optional[str] = typer.Argument(
        None, help="Credential name to show (omit to show all)"
    ),
):
    """Show credentials (all or one)."""
    with open_vaultfile(vaultfile, mode="r") as f:
        creds = get_credentials(f.name, name)
        print(json.dumps(creds, indent=2, sort_keys=True))


# ----------------------------- Entrypoint -------------------------------- #

if __name__ == "__main__":
    app()
