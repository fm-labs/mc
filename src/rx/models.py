from dataclasses import dataclass
from pathlib import Path

from rx.config import RunConfig, GlobalContext


@dataclass
class RxSource:
    url: str

    def validate(self) -> bool:
        if not "://" in self.url:
            raise ValueError(f"Invalid URL format: {self.url}")
        return bool(self.url)

    def get_scheme(self) -> str:
        if not self.validate():
            return ""
        return self.url.split("://")[0]

    def get_path(self) -> str:
        if not self.validate():
            return ""
        return self.url.split("://", 1)[1]

    def get_run_handler(self, run_cfg: RunConfig, ctx: GlobalContext):
        raise NotImplementedError("get_run_handler method not implemented.")


@dataclass
class RxDirectorySource(RxSource):
    SUPPORTED_SOURCE_SCHEMES = ["file"]
    SUPPORTED_TARGET_SCHEMES =  ["s3", "rsync", "scp", "file"]

    def validate(self) -> bool:
        if not super().validate():
            return False
        scheme = self.get_scheme()
        if scheme not in self.SUPPORTED_SOURCE_SCHEMES:
            raise ValueError(f"Unsupported scheme for directory source: {scheme}")

        path = self.get_path()
        if not path:
            raise ValueError("Path is required for directory source.")
        if not Path(path).exists():
            raise ValueError(f"Path {path} does not exist.")
        return True

    def get_run_handler(self, run_cfg: RunConfig, ctx: GlobalContext):
        # find the right handler based on scheme
        # todo dynamic import
        dest_scheme = self.get_scheme()
        if dest_scheme == "s3":
            #return s3_run_handler
            raise RuntimeError("Not implemented")
        elif dest_scheme in ["rsync", "ssh", "file"]:
            #return rsync_run_handler
            raise RuntimeError("Not implemented")
        elif dest_scheme == "scp":
            #return scp_run_handler
            raise RuntimeError("Not implemented")
        else:
            raise ValueError(f"Unsupported destination scheme {dest_scheme} for directory run.")
