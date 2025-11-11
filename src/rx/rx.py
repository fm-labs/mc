import subprocess
import tempfile
import shutil
import os

from rx.config import RunConfig, GlobalContext


def get_run_handler(run_cfg: RunConfig, ctx: GlobalContext):
    if not run_cfg.action:
        return None
    module_name = "rx.handler." + run_cfg.action.replace("-", "_")
    handler_name = "handler"
    try:
        module = __import__(module_name, fromlist=[handler_name])
        handler = getattr(module, handler_name)
    except (ImportError, AttributeError) as e:
        print(f"Error importing handler for {run_cfg.action}: {e}")
        handler = None
    return handler



def rx_run(run_cfg: RunConfig, ctx: GlobalContext) -> int:
    handler = get_run_handler(run_cfg, ctx)
    if not handler:
        raise ValueError(f"No handler found for run type: {run_cfg.action}")

    print(f"Using run handler: {handler.__module__}.{handler.__name__}")
    return handler(run_cfg, ctx)




def rx_dir_to_dir(src_dir: str, dest_dir: str, exclude: list = None) -> int:
    if not os.path.exists(src_dir):
        raise ValueError(f"Source directory does not exist: {src_dir}")
    if not os.path.isdir(src_dir):
        raise ValueError(f"Source path is not a directory: {src_dir}")

    if exclude is None:
        exclude = []

    def ignore_patterns(path, names):
        ignored_names = []
        for pattern in exclude:
            ignored_names.extend(shutil.fnmatch.filter(names, pattern))
        return set(ignored_names)

    try:
        shutil.copytree(src_dir, dest_dir, dirs_exist_ok=True, ignore=ignore_patterns)
        return 0
    except Exception as e:
        print(f"Error copying directory from {src_dir} to {dest_dir}: {e}")
        return 1


def rx_dir_to_remote_dir(src_dir: str, dest: str, exclude: list = None) -> int:
    if not os.path.exists(src_dir):
        raise ValueError(f"Source directory does not exist: {src_dir}")
    if not os.path.isdir(src_dir):
        raise ValueError(f"Source path is not a directory: {src_dir}")

    if exclude is None:
        exclude = []

    rsync_cmd = ["rsync", "-avz", "--delete"]
    for pattern in exclude:
        rsync_cmd.extend(["--exclude", pattern])
    rsync_cmd.append(src_dir + "/")  # Ensure trailing slash to copy contents
    rsync_cmd.append(dest)

    try:
        result = subprocess.run(rsync_cmd, check=True)
        return result.returncode
    except subprocess.CalledProcessError as e:
        print(f"Error syncing directory to remote {dest}: {e}")
        return e.returncode
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1


def rx_dir_to_s3_dir(src_dir: str, dest_dir: str, exclude: list = None) -> int:
    if not os.path.exists(src_dir):
        raise ValueError(f"Source directory does not exist: {src_dir}")
    if not os.path.isdir(src_dir):
        raise ValueError(f"Source path is not a directory: {src_dir}")

    if exclude is None:
        exclude = []

    aws_cmd = ["aws", "s3", "sync", src_dir + "/", dest_dir, "--delete"]
    for pattern in exclude:
        aws_cmd.extend(["--exclude", pattern])

    try:
        result = subprocess.run(aws_cmd, check=True)
        return result.returncode
    except subprocess.CalledProcessError as e:
        print(f"Error syncing directory to S3 {dest_dir}: {e}")
        return e.returncode
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1


def rx_dir_to_temp_dir(src_dir: str, exclude: list = None) -> tuple[str, int]:
    if not os.path.exists(src_dir):
        raise ValueError(f"Source directory does not exist: {src_dir}")
    if not os.path.isdir(src_dir):
        raise ValueError(f"Source path is not a directory: {src_dir}")

    if exclude is None:
        exclude = []

    def ignore_patterns(path, names):
        ignored_names = []
        for pattern in exclude:
            ignored_names.extend(shutil.fnmatch.filter(names, pattern))
        return set(ignored_names)

    try:
        temp_dir = tempfile.mkdtemp()
        shutil.copytree(src_dir, temp_dir, dirs_exist_ok=True, ignore=ignore_patterns)
        return temp_dir, 0
    except Exception as e:
        print(f"Error copying directory to temp dir from {src_dir}: {e}")
        return "", 1