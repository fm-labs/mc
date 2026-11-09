import posixpath


def list_projects_from_containers(containers):
    """
    List all projects from list of containers.

    :param containers: list of containers
    :return: list of project names
    """
    return list(
        set([c.attrs.get("Config", {}).get("Labels", {}).get("com.docker.compose.project") for c in containers])
    )


def filter_containers_by_project(containers, project_name):
    """
    Filter containers by project name.

    :param containers: list of containers
    :param project_name: str
    :return: list of containers
    """
    return [
        c
        for c in containers
        if c.attrs.get("Config", {}).get("Labels", {}).get("com.docker.compose.project") == project_name
    ]


def filter_containers_by_status_text(containers, status):
    """
    Filter containers by status.

    :param containers: list of containers
    :param status: str
    :return: list of containers
    """
    return [c for c in containers if c.attrs.get("State", {}).get("Status") == status]


# POSIX sh script that lists one directory ($1) of a container. Uses only shell builtins for the
# entry types (works on busybox/alpine), plus a single `stat` call for sizes and mtimes when available.
#   T|<type>|<name>        type: d=dir, f=file, l=link, ld=link to a dir, o=other
#   S|<size>|<mtime>|<name>
_LIST_DIR_SCRIPT = r"""
cd -- "$1" 2>/dev/null || exit 2
for f in * .[!.]* ..?*; do
  [ -e "$f" ] || [ -L "$f" ] || continue
  if [ -L "$f" ]; then
    if [ -d "$f" ]; then t=ld; else t=l; fi
  elif [ -d "$f" ]; then t=d
  elif [ -f "$f" ]; then t=f
  else t=o
  fi
  printf 'T|%s|%s\n' "$t" "$f"
done
if command -v stat >/dev/null 2>&1; then
  stat -c 'S|%s|%Y|%n' -- * .[!.]* ..?* 2>/dev/null
fi
exit 0
"""

_ENTRY_TYPES = {"d": "dir", "f": "file", "l": "link", "ld": "link", "o": "other"}

MAX_DIR_ENTRIES = 5000


def normalize_container_path(path: str | None) -> str:
    """Absolute, normalized POSIX path ("/" by default)."""
    path = posixpath.normpath("/" + (path or "/").strip())
    # normpath keeps a leading "//"
    return "/" + path.lstrip("/")


def list_container_dir(container, path: str | None = "/") -> dict:
    """
    List the entries of one directory in a running container, by running a small sh script with exec.

    Returns {"path": ..., "entries": [{"name", "path", "type", "is_dir", "size", "mtime"}], "truncated": bool}.
    Directories (and links to directories) come first, then by name.
    Raises ValueError if the path is not a directory, or the container has no shell.
    """
    path = normalize_container_path(path)
    result = container.exec_run(["sh", "-c", _LIST_DIR_SCRIPT, "sh", path], stdout=True, stderr=False)
    output = (result.output or b"").decode("utf-8", errors="replace")

    if result.exit_code == 2:
        raise ValueError(f"Not a directory or not accessible: {path}")
    if result.exit_code in (126, 127):
        raise ValueError("Can't list files: the container has no shell (sh)")
    if result.exit_code not in (0, None):
        raise ValueError(f"Listing {path} failed (exit code {result.exit_code}): {output.strip()[:500]}")

    entries: dict[str, dict] = {}
    stats: dict[str, tuple[int | None, int | None]] = {}
    for line in output.splitlines():
        if line.startswith("T|"):
            parts = line.split("|", 2)
            if len(parts) == 3 and parts[2]:
                kind, name = parts[1], parts[2]
                entries[name] = {
                    "name": name,
                    "path": posixpath.join(path, name),
                    "type": _ENTRY_TYPES.get(kind, "other"),
                    "is_dir": kind in ("d", "ld"),
                }
        elif line.startswith("S|"):
            parts = line.split("|", 3)
            if len(parts) == 4:
                stats[parts[3]] = (_to_int(parts[1]), _to_int(parts[2]))

    items = []
    for name, entry in entries.items():
        size, mtime = stats.get(name, (None, None))
        items.append({**entry, "size": size, "mtime": mtime})
    items.sort(key=lambda e: (not e["is_dir"], e["name"].lower()))

    return {
        "path": path,
        "entries": items[:MAX_DIR_ENTRIES],
        "truncated": len(items) > MAX_DIR_ENTRIES,
    }


def _to_int(value: str) -> int | None:
    try:
        return int(value)
    except ValueError:
        return None
