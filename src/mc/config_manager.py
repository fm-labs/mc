import abc
import os
from pathlib import Path

from mc.util.yaml_util import yaml_dump

def detect_format(path: str) -> str:
    extparts = os.path.splitext(path)
    if len(extparts) == 2:
        _, ext = extparts
    else:
        ext = ""

    ext = ext.lower()
    if ext == ".toml":
        return "toml"
    if ext in (".yaml", ".yml"):
        return "yaml"
    return "yaml"

class Config(abc.ABC):

    def __init__(self):
        self.configs = {}

    def set(self, key, value):
        """Add a config to the manager."""
        self.configs[key] = value

    def get(self, key):
        """Retrieve a config by its key."""
        return self.configs.get(key)

    def delete(self, key):
        """Delete a config by its key."""
        if key in self.configs:
            del self.configs[key]

    def lists(self):
        """List all stored config keys."""
        return list(self.configs.keys())

    @abc.abstractmethod
    def read(self):
        """Load configs from a storage."""
        raise NotImplementedError()

    @abc.abstractmethod
    def dump(self):
        """Save configs to a storage."""
        raise NotImplementedError()


class FileConfig(Config):
    """A simple file-based configs manager using plain yaml/toml files to store configs."""

    def __init__(self, filepath):
        super().__init__()
        self.filepath = filepath
        self.read()

    def read(self):
        """Load configs from a yaml file (stub implementation)."""
        path = self.filepath
        fmt = detect_format(path)
        if not os.path.exists(path):
            return

        with open(path, "rb") as f:
            content = f.read()

        if fmt == "toml":
            # Prefer stdlib tomllib if available (Python 3.11+)
            try:
                import tomllib  # type: ignore
                data = tomllib.loads(content.decode("utf-8"))
            except ModuleNotFoundError:
                try:
                    import toml  # type: ignore
                except ModuleNotFoundError:
                    raise RuntimeError("Error: Need 'tomllib' (Python 3.11+) or 'toml' package to read TOML.")
                data = toml.loads(content.decode("utf-8"))
        else:
            try:
                import yaml  # type: ignore
            except ModuleNotFoundError:
                raise RuntimeError("Error: Need 'PyYAML' (package 'yaml') to read YAML.")
            data = yaml.safe_load(content) or {}

        self.configs.update(data)

    def dump(self) -> None:
        path = self.filepath
        data = self.configs
        fmt = detect_format(path)

        Path(path).parent.mkdir(parents=True, exist_ok=True)
        print(f"Writing {fmt} data to {path}...")
        try:
            with open(path, "w") as f:
                if fmt == "toml":
                    try:
                        import tomli_w
                        tomli_w.dump(data, f)
                    except ModuleNotFoundError:
                        try:
                            import toml  # type: ignore
                        except ModuleNotFoundError:
                            raise RuntimeError("Error: Need 'tomli-w' or 'toml' package to write TOML.")
                        f.write(toml.dumps(data))
                else:
                    try:
                        import yaml  # type: ignore
                    except ModuleNotFoundError:
                        raise RuntimeError("Error: Need 'PyYAML' (package 'yaml') to write YAML.")
                    yaml_dump(data, f, sort_keys=True)
        except Exception:
            print("Error writing data, removing temporary file.")
            raise
