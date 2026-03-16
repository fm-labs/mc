import os

from mc.config import get_env_var
from mc.util.awscli_helper import awscli_ecr_login
from mc.util.dockercli_helper import dockercli_login


def get_container_registry_credentials(registry_host: str, username: str = None, password: str = None) -> tuple[
    str, str]:
    """
    Lookup container registry credentials based on the registry URL.
    Supports Docker Hub, GitHub Container Registry, Azure Container Registry, and AWS ECR.

    :param registry_host: The URL of the container registry.
    :param username: Optional specified username to use for lookup.
    :return: A tuple of (username, password)
    """
    # if the registry_host is a full URL, extract the host part
    if "://" in registry_host:
        registry_host = registry_host.split("://", 1)[1].split("/", 1)[0]

    if registry_host in ["docker.io", "index.docker.io", ""]:
        username = username or get_env_var("DOCKERHUB_USERNAME", "")
        password = password or get_env_var("DOCKERHUB_TOKEN", "")
        return username, password
    elif registry_host in ["ghcr.io"]:
        username = username or get_env_var("GHCR_USERNAME")
        password = password or get_env_var("GHCR_TOKEN", "")
        return username, password
    elif registry_host.endswith("azurecr.io"):
        username = username or get_env_var("ACR_USERNAME", "")
        password = password or get_env_var("ACR_PASSWORD", "")
        return username, password
    elif registry_host.endswith("amazonaws.com"):
        print("Warning: AWS ECR registry detected. Attempting AWS ECR login ...")
        # access_key = get_env_var("AWS_ACCESS_KEY_ID", None)
        # secret_key = get_env_var("AWS_SECRET_ACCESS_KEY", None)
        # profile = get_env_var("AWS_PROFILE", None)
        # region = get_env_var("AWS_REGION", "us-east-1")

        # The username field is used to specify the AWS CLI profile name
        # profile = username

        access_key = username or get_env_var("AWS_ACCESS_KEY_ID", None)
        secret_key = password or get_env_var("AWS_SECRET_ACCESS_KEY", None)
        try:
            ecr_url, ecr_username, ecr_password = awscli_ecr_login(ecr_url=registry_host,
                                                                   # profile=profile,
                                                                   access_key=access_key,
                                                                   secret_key=secret_key
                                                                   )
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

def container_registry_login(registry_url: str, username: str = None, password: str = None):
    try:
        if not registry_url:
            raise ValueError("Missing registry url")

        username, password = get_container_registry_credentials(registry_url, username, password)
        if not username and not password:
            raise ValueError(f"Warning: No credentials found for registry: {registry_url}")

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
