import shutil
from pathlib import Path

from rx.config import RunConfig, GlobalContext
from rx.util import split_url


def copy_recursive(src: Path, dest: Path, exclude: list[str] = None):
    if not src.exists():
        raise FileNotFoundError(f"Source path '{src}' does not exist.")
    if not src.is_dir():
        raise NotADirectoryError(f"Source path '{src}' is not a directory.")

    dest.mkdir(parents=True, exist_ok=True)

    for item in src.iterdir():
        print(f"Copying {item.name} to {dest.name}")
        if exclude and item.name in exclude:
            print(f"Excluding {item.name}")
            continue

        s = item
        d = dest / item.name
        if item.is_dir():
            copy_recursive(s, d)
        else:
            shutil.copy2(s, d)


def handle_file_run(run_cfg: RunConfig, ctx: GlobalContext):
    src = run_cfg.src
    dest = run_cfg.dest

    [srcschema, srcpath] = split_url(src)
    [destschema, destpath] = split_url(dest)

    src_path = Path(ctx.cwd) / srcpath
    dest_path = Path(ctx.cwd) / destpath
    #copy_recursive(src_path, dest_path)
    raise ValueError("xx")


handler = handle_file_run
