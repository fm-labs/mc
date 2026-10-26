import logging

import click
from rich.logging import RichHandler

from mc.cli.apps import apps
from mc.config import API_VERSION, API_NAME
from mc.inventory import setup_inventory

# configure inventorydb for mc, before the inventory is used
setup_inventory()

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
    ],
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
    click.echo(f"{API_NAME} v{API_VERSION}")


# cli.add_command(credentials)
cli.add_command(apps)

if __name__ == "__main__":
    cli()
