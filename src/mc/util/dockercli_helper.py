import os
import subprocess
import time
from tempfile import TemporaryFile

from mc.util.rx_util import toolcmd


def dockercli(cmd: list[str], env=None) -> dict:
    """
    Execute a Docker CLI command.

    :param cmd: List of command arguments (e.g., ['docker', 'ps'])
    :param env: Optional environment variables to pass to the subprocess
    """

    _env = os.environ.copy()
    if env:
        _env.update(env)

    dockerhost = _env.get("DOCKER_HOST",  "")
    print(f"Executing Docker command with DOCKER_HOST={dockerhost}: {' '.join(cmd)}")

    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        text=True,
        env=_env,
    )

    if result.returncode != 0:
       print("Docker command failed:", " ".join(cmd), result.stderr)
       raise RuntimeError(result.stderr)

    print("Docker command executed successfully:", " ".join(cmd), result.stdout)

    # write the command output to a tmp file for debugging
    with open(f"/tmp/dockercli_output_{str(int(time.time()))}.txt", "w") as f:
        f.write(result.stdout)

    return {
        "out": result.stdout,
        "err": result.stderr,
        "rc": result.returncode,
    }


def dockercli_login(username: str, password: str, registry="https://docker.io", env=None) -> dict:
    """
    Login to Docker and ensure credentials persist.

    :param username: Docker registry username
    :param password: Docker registry password
    :param registry: Docker registry URL (default: Docker Hub)
    :param env: Optional environment variables to pass to the subprocess
    """
    if not registry.startswith("http"):
        registry = "https://" + registry

    # write password to a temporary file to avoid exposing it in process list
    with TemporaryFile() as tmp_file:
        tmp_file.write(bytes(password, "utf-8"))
        tmp_file.flush()
        tmp_file.seek(0)

        _env = os.environ.copy()
        if env:
            _env.update(env)

        cmd = toolcmd("docker", ["login", "--username", username, "--password-stdin", registry])
        print(cmd)
        print(_env)
        result = subprocess.run(
            cmd,
            input=tmp_file.read(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            text=False,
            env=_env,
        )

        if result.returncode != 0:
            print("Docker login failed:", result.stderr.decode())
            raise RuntimeError(result.stderr.decode())

        return {
            "out": result.stdout.decode(),
            "err": result.stderr.decode(),
            "rc": result.returncode,
        }


def dockercli_image_pull(image: str, env=None) -> dict:
    """
    Pull a Docker image from a registry.

    :param image: Docker image name (e.g., 'nginx:latest')
    :param env: Optional environment variables to pass to the subprocess
    """
    cmd = toolcmd("docker", ["image", "pull", image])
    return dockercli(cmd, env=env)


def dockercli_image_push(image: str, env=None) -> dict:
    """
    Push a Docker image to a registry.

    :param image: Docker image name (e.g., 'nginx:latest')
    :param env: Optional environment variables to pass to the subprocess
    """
    cmd = toolcmd("docker", ["image", "push", image])
    return dockercli(cmd, env=env)



# def dockercli_login_ecr_with_awscli(ecr_url, region="us-east-1", profile=None, access_key=None, secret_key=None):
#     """Login to AWS ECR using AWS CLI."""
#     try:
#         p_aws_env = dict({
#             #"DOCKER_CONFIG": settings.DOCKER_CONFIG,
#         })
#         if profile:
#             p_aws_env["AWS_PROFILE"] = profile
#         else:
#             p_aws_env["AWS_ACCESS_KEY_ID"] = access_key
#             p_aws_env["AWS_SECRET_ACCESS_KEY"] = secret_key
#
#         p_aws = subprocess.run(
#             ["aws", "ecr", "get-login-password", "--region", region],
#             stdout=subprocess.PIPE,
#             stderr=subprocess.PIPE,
#             check=True,
#             text=True,
#             env=p_aws_env,
#         )
#
#         print("AWS ECR login successful!", p_aws.stdout, flush=True)
#         ecr_password = p_aws.stdout # bytes
#         ecr_username = "AWS"
#
#         # Use the obtained password to log in to Docker
#         #ecr_url = f"{region}.dkr.ecr.amazonaws.com"
#         p_docker = subprocess.run(
#             ["docker", "login", "--username", ecr_username, "--password-stdin", ecr_url],
#             input=ecr_password,
#             stdout=subprocess.PIPE,
#             stderr=subprocess.PIPE,
#             check=True,
#             text=True,
#             env=dict({
#                 #"DOCKER_CONFIG": settings.DOCKER_CONFIG
#             }),
#         )
#
#         print("Docker login to ECR successful!", p_docker.stdout, flush=True)
#         return ecr_url, ecr_username, ecr_password
#
#     except subprocess.CalledProcessError as e:
#         print("Docker login failed:", e.stderr, flush=True)
#         return False
