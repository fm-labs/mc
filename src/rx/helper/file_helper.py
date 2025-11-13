import shutil
from pathlib import Path


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
