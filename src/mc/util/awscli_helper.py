import os
import subprocess


def awscli_ecr_login(ecr_url, region=None, profile=None, access_key=None, secret_key=None) -> tuple[str, str, str]:
    """Login to AWS ECR using AWS CLI."""

    # extract region from ecr_url if possible, otherwise default to us-east-1
    # ecr_url format: <aws_account_id>.dkr.ecr.<region>.amazonaws.com
    # example: http://123456789012.dkr.ecr.us-west-2.amazonaws.com
    if region is None:
        region = "us-east-1"
        try:
            parts = ecr_url.split(".")
            if len(parts) >= 4 and parts[2] == "ecr":
                region = parts[3]
        except Exception:
            pass

    try:
        p_aws_env = os.environ.copy()
        if profile:
            p_aws_env["AWS_PROFILE"] = profile

        if not profile and access_key and secret_key:
            p_aws_env["AWS_ACCESS_KEY_ID"] = access_key
            p_aws_env["AWS_SECRET_ACCESS_KEY"] = secret_key

        cmd = ["aws", "ecr", "get-login-password", "--region", region]
        print(cmd)
        print("Running AWS CLI command:", " ".join(cmd), flush=True)

        p_aws = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            text=True,
            env=p_aws_env,
        )
        print("AWS ECR login successful!", p_aws.stdout, flush=True)
        ecr_password = p_aws.stdout.strip()
        ecr_username = "AWS"

        return ecr_url, ecr_username, ecr_password

    except subprocess.CalledProcessError as e:
        print("Docker login failed:", e.stderr, flush=True)
        raise e
