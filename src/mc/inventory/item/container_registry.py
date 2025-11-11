import os

from rx.helper.awscli_helper import awscli_ecr_login
from rx.helper.dockercli_helper import dockercli_login


def lookup_container_registry_credentials(registry_host: str, specified_username: str = None) -> tuple[str, str]:
    """
    Lookup container registry credentials based on the registry URL.
    Supports Docker Hub, GitHub Container Registry, Azure Container Registry, and AWS ECR.

    :param registry_host: The URL of the container registry.
    :param specified_username: Optional specified username to use for lookup.
    :return: A tuple of (username, password)
    """
    # if the registry_host is a full URL, extract the host part
    if "://" in registry_host:
        registry_host = registry_host.split("://", 1)[1].split("/", 1)[0]

    if registry_host in ["docker.io", "index.docker.io", ""]:
        username = os.environ.get("DOCKERHUB_USERNAME", specified_username)
        password = os.environ.get("DOCKERHUB_TOKEN", "")
        return username, password
    elif registry_host in ["ghcr.io"]:
        username = os.environ.get("GHCR_USERNAME", specified_username)
        password = os.environ.get("GHCR_TOKEN", "")
        return username, password
    elif registry_host.endswith("azurecr.io"):
        username = os.environ.get("ACR_USERNAME", specified_username)
        password = os.environ.get("ACR_PASSWORD", "")
        return username, password
    elif registry_host.endswith("amazonaws.com"):
        print("Warning: AWS ECR registry detected. Attempting AWS ECR login ...")
        # access_key = os.environ.get("AWS_ACCESS_KEY_ID", None)
        # secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY", None)
        # profile = os.environ.get("AWS_PROFILE", None)
        # region = os.environ.get("AWS_REGION", "us-east-1")

        # The username field is used to specify the AWS CLI profile name
        profile = specified_username
        try:
            ecr_url, ecr_username, ecr_password = awscli_ecr_login(ecr_url=registry_host,
                                                                   profile=profile)
            username = ecr_username
            password = ecr_password
        except Exception as e:
            print(f"Error: Failed to get AWS ECR credentials for {registry_host}: {str(e)}")
            username = ""
            password = ""
        return username, password
    else:
        print(f"Warning: No credentials found for registry: {registry_host}")
        return "", ""

# def handle_container_registry_configure(item: dict, action_params: dict) -> dict:
#     return {
#         "status": "error",
#         "message": "Container registry configure action not implemented yet."
#     }


def handle_container_registry_login(item: dict, action_params: dict) -> dict:
    item_props = item.get("properties", {})
    registry_url= item_props.get("registry_url")
    username = item_props.get("username")
    #password = item_props.get("password")
    #is_private = item_props.get("is_private", True)

    try:
        if not registry_url:
            raise ValueError("Missing registry url")

        username, password = lookup_container_registry_credentials(registry_url, username)
        if not username and not password:
            raise ValueError(f"Warning: No credentials found for registry: {registry_url}")

        #remote_login_host = action_params.get("remote_login_host")
        #if remote_login_host:
        #    print("Info: Using remote docker daemon for container registry login.")
        #    raise NotImplementedError("Remote docker daemon login not implemented yet.")

        env = os.environ.copy()
        dockercli_login(username, password, registry_url, env=env)

        return {
            "status": "success",
            "message": f"Logged in to container registry {registry_url} successfully."
        }
    except Exception as e:
        # return {
        #     "status": "error",
        #     "message": f"Failed to login to container registry {registry_url}: {str(e)}"
        # }
        raise


actions = {
    "login": handle_container_registry_login,
}