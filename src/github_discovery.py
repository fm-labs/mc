import json
import os
import uuid

from kloudia.inventory.helper import gen_inventory_key
from kloudia.inventory.storage import get_inventory_storage_instance
from kloudia.plugin.github.github_api import github_get_repos

if __name__ == "__main__":

    # get github credentials from integration properties
    github_token = os.environ.get("GITHUB_TOKEN")
    if not github_token:
        raise ValueError("GITHUB_TOKEN environment variable is not set")

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
            "item_key": gen_inventory_key("repository", repo["full_name"]),
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