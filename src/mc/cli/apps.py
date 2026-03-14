import logging
import click

from mc.inventory.item.app_stack import AppStackItem, handle_app_stack_action_deploy, handle_app_stack_action_sync
from mc.inventory.storage import get_inventory_storage_instance

logger = logging.getLogger(__name__)

@click.group()
def apps():
    """Deploy applications and stacks."""
    pass


@apps.command("inspect")
@click.argument("name")
def inspect_app(name: str):
    """Deploy an application stack."""
    storage = get_inventory_storage_instance()
    stack = storage.get_item("app_stack", name)
    if not stack:
        click.echo(f"Stack '{name}' not found.")
        return
    #for key, value in stack.items():
    #    click.echo(f"- {key}: {value}")
    item = AppStackItem.from_item_dict(stack)
    logger.info(item)


@apps.command("update")
@click.argument("name")
@click.option("--check", is_flag=True, help="Check for changes without applying them")
def update_app(name: str, dry_run: bool):
    """Deploy an application stack."""
    storage = get_inventory_storage_instance()
    stack = storage.get_item("app_stack", name)
    if not stack:
        click.echo(f"Stack '{name}' not found.")
        return

    print(stack)
    click.echo(f"Updating stack '{name}' ...")
    handle_app_stack_action_sync(stack, action_params={})


@apps.command("deploy")
@click.argument("name")
@click.option("--dry-run", is_flag=True, help="Show the stack configuration without deploying")
def deploy_app(name: str, dry_run: bool):
    """Deploy an application stack."""
    storage = get_inventory_storage_instance()
    stack = storage.get_item("app_stack", name)
    if not stack:
        click.echo(f"Stack '{name}' not found.")
        return

    print(stack)
    click.echo(f"Deploying stack '{name}' ...")
    handle_app_stack_action_deploy(stack, action_params={})
