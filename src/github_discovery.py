import json
import os

from kloudia.plugin.github.github_api import github_get_repos

if __name__ == "__main__":

    github_token = os.environ.get("GITHUB_TOKEN", default="")
    # list all repos for a user
    repos = github_get_repos(github_token, visibility="all")

    print(repos)
    print(f"Found {len(repos)} repositories")

    # save repos to a file
    with open("data/github_repos.json", "w") as f:
        json.dump(repos, f, indent=4)
