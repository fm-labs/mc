from __future__ import annotations

import typer


def cli_error(msg: str) -> None:
    typer.secho(msg, fg=typer.colors.RED, err=True)


def cli_info(msg: str) -> None:
    typer.secho(msg, fg=typer.colors.BLUE)


def cli_success(msg: str) -> None:
    typer.secho(msg, fg=typer.colors.GREEN)


def cli_warn(msg: str) -> None:
    typer.secho(msg, fg=typer.colors.YELLOW)


def cli_debug(msg: str) -> None:
    typer.secho(msg, fg=typer.colors.CYAN)
