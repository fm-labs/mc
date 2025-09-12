import requests

def github_list_private_repos(token: str) -> list:
    """
    List private GitHub repositories for the authenticated user.

    Args:
        token (str): GitHub personal access token with appropriate scopes.

    Returns:
        list: A list of private repository names.
    """

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    repos = []
    page = 1

    while True:
        response = requests.get(
            f"https://api.github.com/user/repos?per_page=100&page={page}&visibility=private",
            headers=headers
        )
        if response.status_code != 200:
            raise Exception(f"GitHub API error: {response.status_code} - {response.text}")

        data = response.json()
        if not data:
            break

        repos.extend([repo['full_name'] for repo in data])
        page += 1

    return repos