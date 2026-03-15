import os

import click

from mc.client.apiclient import McApiClient


@click.group()
@click.option("--host", "-h", help="API host URL", default=None, envvar="MC_API_HOST")
@click.pass_context
def remote(ctx, host):
    """Main CLI."""
    ctx.ensure_object(dict)
    ctx.obj["host"] = host or "http://localhost:3080"

    api_key = os.getenv("MC_API_KEY", "")
    api_client = McApiClient(api_url=host, api_key=api_key)
    ctx.obj["api_client"] = api_client

@remote.command()
@click.pass_context
def info(ctx):
    """Show API info."""
    click.echo("API info: ...")
    print(ctx.obj["api_client"].get_info())

@remote.command()
@click.pass_context
def health(ctx):
    """Show API info."""
    click.echo("API health: ...")
    print(ctx.obj["api_client"].get('/health'))


if __name__ == "__main__":
    remote()