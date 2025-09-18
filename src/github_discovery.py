import json
import os
import uuid

from kloudia.integrations import load_integration_properties
from kloudia.inventory.storage import get_inventory_storage_instance
from kloudia.plugin.github.github_api import github_get_repos

if __name__ == "__main__":

    # get github credentials from integration properties
    github_integration = load_integration_properties("software_provider", "github")
    if github_integration is None:
        raise Exception("No github integration found in config")

    #github_token = os.environ.get("GITHUB_TOKEN", default="")
    github_token = github_integration["password"] if "password" in github_integration else None
    if not github_token:
        raise Exception("No github token found")

    # list all repos for a user
    repos = github_get_repos(github_token, visibility="all")

    print(repos)
    print(f"Found {len(repos)} repositories")

    # save repos to a file
    with open("data/github_repos.json", "w") as f:
        json.dump(repos, f, indent=4)


    # map each github repo to an inventory entry
    inventory = []
    inventory_storage = get_inventory_storage_instance()
    for repo in repos:
        is_enabled = repo["archived"] is False and repo["disabled"] is False
        entry = {
            "uuid": str(uuid.uuid4().hex),
            "item_type": "repository",
            "provider": "github",
            "name": repo["full_name"],
            "properties": {
                "url": repo["html_url"],
            },
            "github": repo,
        }
        inventory.append(entry)
        inventory_storage.save_item("repository", entry)

    # save inventory to a file
    with open("data/inventory_repository.json", "w") as f:
        json.dump(inventory, f, indent=4)