import logging
from rich.logging import RichHandler
import click

import mc.include # do not remove
from mc.cli.apps import apps

logging.basicConfig(
    level="INFO",
    format="%(message)s",
    handlers=[
        RichHandler(
            show_time=True,  # show timestamps
            omit_repeated_times=False,  # show timestamp every line
            show_level=True,
            show_path=True,  # hide file path
            rich_tracebacks=False,  # beautiful exception tracebacks
        )
    ]
)
logger = logging.getLogger(__name__)


@click.group()
@click.pass_context
def cli(ctx):
    """Main CLI."""
    ctx.ensure_object(dict)

@cli.command()
def version():
    """Show version."""
    click.echo("Version 2.0.0")

#cli.add_command(credentials)
cli.add_command(apps)

if __name__ == "__main__":
    cli()