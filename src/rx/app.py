from __future__ import annotations

from pathlib import Path
from typing import Optional
import subprocess

import typer

from rx.helper.typer_helper import cli_error, cli_info, cli_success, cli_warn, cli_debug
from rx.config import load_config, GlobalContext

app = typer.Typer(add_completion=False, help="RX - Build and Runment Tool")


# def get_run_handler(run_cfg: RunConfig, ctx: GlobalContext):
#     if not run_cfg.action:
#         return None
#     module_name = "rx.handler." + run_cfg.action.replace("-", "_")
#     handler_name = "handler"
#     try:
#         module = __import__(module_name, fromlist=[handler_name])
#         handler = getattr(module, handler_name)
#     except (ImportError, AttributeError) as e:
#         print(f"Error importing handler for {run_cfg.action}: {e}")
#         handler = None
#     return handler
#
#
#
# def rx_run(run_cfg: RunConfig, ctx: GlobalContext) -> int:
#     handler = get_run_handler(run_cfg, ctx)
#     if not handler:
#         raise ValueError(f"No handler found for run type: {run_cfg.action}")
#
#     print(f"Using run handler: {handler.__module__}.{handler.__name__}")
#     return handler(run_cfg, ctx)


def run_step(label: str, command: str | None, cwd: Optional[Path] = None, dry_run: bool = False) -> None:
    if command is None or not command.strip():
        cli_warn(f"Skipping {label} (empty)")
        return

    cli_debug(f"→ {label}: {command}")
    if dry_run:
        cli_info("   (dry-run; not executing)")
        return

    # check for command macros
    # a macro is defined as a command that starts with a ':' sign
    # the first word is the macro name, the rest are arguments
    if command.startswith(":"):
        macro = command.split(" ", 1)[0][1:]
        macro_args = command.split(" ", 1)[1] if " " in command else ""
        cli_debug(f"  (macro detected): {macro} {macro_args}")
        cli_warn("  (macros are not yet implemented)")
        return


    # Use shell=True to allow chained commands/flags exactly as written in TOML.
    result = subprocess.run(command, shell=True, cwd=cwd)

    if result.returncode != 0:
        cli_error(f"{label} failed with exit code {result.returncode}")
        raise typer.Exit(code=result.returncode)


@app.callback()
def main(
    ctx: typer.Context,
    config_path: Path = typer.Option(None, "--config", "-c", help="Path to TOML config."),
    working_dir: Optional[Path] = typer.Option(None, "--working-dir", "-w", help="Working directory for commands."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Print steps without executing."),
):
    """
    Define global options and store them in ctx.obj so all subcommands can access them.
    """
    if working_dir is None:
        working_dir = Path.cwd()

    if working_dir is not None and not working_dir.exists():
        cli_error(f"Working directory does not exist: {working_dir}")
        raise typer.Exit(code=2)

    if config_path is None:
        default_paths = [
            Path.cwd() / "rx.toml",
            Path.cwd() / "app.toml",
            #Path.cwd() / "rx.json",
            #Path.cwd() / "app.json",
        ]

        for p in default_paths:
            if p.exists():
                config_path = p
                break
        if config_path is None:
            cli_error("No config file specified and no default config file found (rx.toml or app.toml in current directory).")
            raise typer.Exit(code=2)

    elif not config_path.exists():
        cli_error(f"Config file does not exist: {config_path}")
        raise typer.Exit(code=2)

    configdata = load_config(config_path)
    ctx.obj = GlobalContext(config_path=config_path, cwd=working_dir, dry_run=dry_run, config=configdata)
    cli_success("--- RX CLI ---")
    cli_info(f"Config: {config_path}")
    cli_info(f"Working dir: {working_dir}")
    if dry_run:
        cli_info("Dry run mode: ON (no commands will be executed)")



@app.command(help="List configured run and run targets.")
def targets(ctx: typer.Context) -> None:
    g: GlobalContext = ctx.obj
    cfg = g.config

    def filter_by_action(action: str):
        return {k: v for k, v in cfg.run.items() if v.action == action}

    cli_info(f"Variables: {cfg}")

    cli_info("Available build targets:")
    for target in cfg.build.keys():
        cli_info(f" - {target}")
        #cli_debug(f"   [{cfg.build[target].action}] {cfg.build[target].src} -> {cfg.build[target].dest}")

    cli_info("Available publish targets:")
    for target in filter_by_action("publish").keys():
        cli_info(f" - [{cfg.run[target].action}] {target}")
        cli_debug(f"   {cfg.run[target].src} -> {cfg.run[target].dest}")

    cli_info("Available run targets:")
    for target in filter_by_action("run").keys():
        cli_info(f" - [{cfg.run[target].action}] {target}")
        cli_debug(f"   {cfg.run[target].command}")



@app.command(help="Run the build.")
def build(
    ctx: typer.Context,
    target: str = typer.Argument(None, help="Run target name (e.g. production)."),
):
    g: GlobalContext = ctx.obj
    cfg = g.config
    cwd = g.cwd
    dry_run = g.dry_run

    if target is None:
        # cli_error("No build target specified.")
        # raise typer.Exit(code=2)
        cli_warn("No build target specified. Using 'default'.")
        target = "default"

    build_cfg = cfg.build.get(target)
    if build_cfg is None:
        cli_error(f"Build target '{target}' is not defined in {g.config_path}")

        cli_debug("Available build targets:")
        for t in cfg.build.keys():
            cli_debug(f" - {t}")
        raise typer.Exit(code=2)

    cli_info(
        f"Building target={target} - {cfg.metadata.name} v{cfg.metadata.version}")

    run_step("command_before", build_cfg.command_before, cwd=cwd, dry_run=dry_run)
    run_step("build", build_cfg.command, cwd=cwd, dry_run=dry_run)
    run_step("command_after", build_cfg.command_after, cwd=cwd, dry_run=dry_run)
    cli_success("✅ Build finished")


@app.command(help="Run to target.")
def run(
    ctx: typer.Context,
    target: str = typer.Argument(None, help="Run target name (e.g. production)."),
):
    g: GlobalContext = ctx.obj
    run_cfg = g.config.run.get(target)
    if run_cfg is None:
        cli_error(f"{target} is not defined in {g.config_path}")
        raise typer.Exit(code=2)

    cli_info(f"Running '{target}' (type: {run_cfg.action}) from {run_cfg.src}")

    # Hooks and main command
    run_step("command_before", run_cfg.command_before, cwd=g.cwd, dry_run=g.dry_run)
    try:
        if (run_cfg.command is not None) and (run_cfg.command != ""):
            run_step("run", run_cfg.command, cwd=g.cwd, dry_run=g.dry_run)
        else:
            raise ValueError(f"No command defined for run target '{target}'")
    except Exception as e:
        cli_error(str(e))
        raise e
        raise typer.Exit(code=3)

    run_step("command_after", run_cfg.command_after, cwd=g.cwd, dry_run=g.dry_run)
    cli_success("✅ Run finished")


