from pathlib import Path

from rx import config
from rx.config import RunConfig, GlobalContext
from rx.helper.subprocess_helper import rx_subprocess
from rx.util import split_url


# def check_aws_cli_installed(ctx: GlobalContext = None) -> str:
#     aws_bin = os.environ.get("AWS_BIN", "/usr/local/bin/aws")
#     if os.path.exists(aws_bin) and os.access(aws_bin, os.X_OK):
#         return aws_bin
#
#     aws_bin = get_tool_path("aws")
#     if aws_bin:
#         return aws_bin
#     raise EnvironmentError("AWS CLI is not installed or not found in PATH.")


def handle_s3_run(run_cfg: RunConfig, ctx: GlobalContext):
    src = run_cfg.src
    dest = run_cfg.dest

    aws_cfg = run_cfg.extra.get("aws", {})
    aws_region = aws_cfg.get("region", config.AWS_REGION)
    aws_profile = aws_cfg.get("profile", config.AWS_PROFILE)
    #aws_access_key_id = aws_cfg.get("access_key_id", config.AWS_ACCESS_KEY_ID)
    #aws_secret_access_key = aws_cfg.get("secret_access_key", config.AWS_SECRET_ACCESS_KEY)

    # ensure aws cli is installed
    aws_bin = check_aws_cli_installed(ctx)

    # validate required fields
    [srcschema, src_hostpath] = split_url(src)
    if srcschema not in ["file"]:
        raise ValueError("Source URL must start with file://")
    srcpath = Path(ctx.cwd) / src_hostpath
    if not srcpath.exists():
        raise FileNotFoundError(f"Source path '{srcpath}' does not exist.")

    if not dest.startswith("s3://"):
        raise ValueError("S3 URL must start with s3://")

    cmd = [aws_bin, "s3", "sync"]
    #cmd += ["--delete"]
    cmd += ["--exact-timestamps"]
    if aws_region:
        cmd += ["--region", aws_region]
    if aws_profile:
        cmd += ["--profile", aws_profile]
    cmd += [f"{src}", dest]

    env = {}
    if config.AWS_ACCESS_KEY_ID:
        env["AWS_ACCESS_KEY_ID"] = config.AWS_ACCESS_KEY_ID
    if config.AWS_SECRET_ACCESS_KEY:
        env["AWS_SECRET_ACCESS_KEY"] = config.AWS_SECRET_ACCESS_KEY
    if config.AWS_ENDPOINT_URL:
        env["AWS_ENDPOINT_URL"] = config.AWS_ENDPOINT_URL
    if config.AWS_PROFILE:
        env["AWS_PROFILE"] = config.AWS_PROFILE
    if config.AWS_REGION:
        env["AWS_REGION"] = config.AWS_REGION

    return rx_subprocess(cmd, cwd=ctx.cwd, env=env)


handler = handle_s3_run
