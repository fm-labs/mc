import typer

from xvault.cli import app as xvault_app

app = typer.Typer()
app.add_typer(xvault_app, name="vault", help="Manage vault credentials")

if __name__ == "__main__":
    app()
