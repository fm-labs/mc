import typer
from typing_extensions import Annotated

app = typer.Typer()

def load_deploy_config():
    # Placeholder for loading deployment configuration
    return {"name": "testing", "url": "file:///opt/deployments/testing"}


@app.command()
def deploy(
    target: str,
    confirm: Annotated[
        bool, typer.Option(prompt="Are you sure you want to deploy the target?")
    ],
):
    if confirm:
        print(f"Confirmed deployment to: {target}")
    else:
        print("Operation cancelled")
        raise typer.Exit()


@app.callback()
def main(ctx: typer.Context):
    config = load_deploy_config()
    print(f"Deployment Config: {config}")
    ctx.obj = config
    print("Welcome to the Deployment CLI")