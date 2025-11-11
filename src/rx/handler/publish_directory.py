from dataclasses import dataclass
from pathlib import Path

from rx.config import RunConfig, GlobalContext
from rx.util import split_url

from rx.plugin.s3 import handler as s3_run_handler
from rx.plugin.rsync import handler as rsync_run_handler
from rx.plugin.scp import handler as scp_run_handler


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
            return s3_run_handler
        elif dest_scheme in ["rsync", "ssh", "file"]:
            return rsync_run_handler
        elif dest_scheme == "scp":
            return scp_run_handler
        else:
            raise ValueError(f"Unsupported destination scheme {dest_scheme} for directory run.")


# def delegate_dir_run(run_cfg: RunConfig, ctx: GlobalContext):
#     src = RxDirectorySource(url=run_cfg.src)
#     if not src.validate():
#         raise ValueError(f"Invalid source configuration: {run_cfg.src}")
#     handler = src.get_run_handler(run_cfg, ctx)
#     print(f"Using directory run handler: {handler.__module__}.{handler.__name__}")
#     raise NotImplementedError("Directory run handler is not implemented yet.")
#     #return handler(run_cfg, ctx)
#
# handler = delegate_dir_run

def handle_directory_run(run_cfg: RunConfig, ctx: GlobalContext):
    src = run_cfg.src
    dest = run_cfg.dest

    # validate the source directory
    if not src:
        raise ValueError("Source directory is required for directory run.")
    if not dest:
        raise ValueError("Destination directory is required for directory run.")

    if dest.startswith("/"):
        # local absolute path, use rsync
        return rsync_run_handler(run_cfg, ctx)
    elif "://" in dest:
        # likely a URL
        [dest_scheme, _] = split_url(dest)

        # find the right handler based on scheme
        if dest_scheme == "s3":
            return s3_run_handler(run_cfg, ctx)
        elif dest_scheme in ["rsync", "ssh", "file"]:
            return rsync_run_handler(run_cfg, ctx)
        elif dest_scheme == "scp":
            return scp_run_handler(run_cfg, ctx)
        else:
            raise ValueError(f"Unsupported destination scheme {dest_scheme} for directory run.")
    else:
        raise ValueError(f"Unsupported destination format for directory run: {dest}")

handler = handle_directory_run
