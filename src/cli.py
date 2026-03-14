import click

from mc.cli.credentials import credentials

@click.group()
@click.option("--interactive/--no-interactive", default=True)
@click.pass_context
def cli(ctx, interactive):
    """Main CLI."""
    ctx.ensure_object(dict)
    ctx.obj["interactive"] = interactive

@cli.command()
def version():
    """Show version."""
    click.echo("Version 2.0.0")

#cli.add_command(credentials)

if __name__ == "__main__":
    cli()