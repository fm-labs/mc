import requests

def github_get_repos(token: str, visibility=None) -> list[dict]:
    """
    List private GitHub repositories for the authenticated user.

    Args:
        token (str): GitHub personal access token with appropriate scopes.
        visibility (str, optional): Filter repositories by visibility.
                                    Can be 'all', 'public', or 'private'. Defaults to None.

    Returns:
        list: A list of github repositories.
    """

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    repos = []
    page = 1


    while True:
        url = f"https://api.github.com/user/repos?per_page=100&page={page}&affiliation=owner"
        if visibility:
            url += f"&visibility={visibility}"

        response = requests.get(
            url=url,
            headers=headers
        )
        if response.status_code != 200:
            raise Exception(f"GitHub API error: {response.status_code} - {response.text}")

        data = response.json()
        if not data:
            break

        repos.extend(data)
        page += 1

    return repos


def github_list_repos(token: str, visibility=None) -> list[str]:
    """
    List private GitHub repositories for the authenticated user.

    Args:
        token (str): GitHub personal access token with appropriate scopes.
        visibility (str, optional): Filter repositories by visibility.
                                    Can be 'all', 'public', or 'private'. Defaults to None.

    Returns:
        list: A list of github repository names.
    """
    repos = github_get_repos(token, visibility)
    return [repo['full_name'] for repo in repos]