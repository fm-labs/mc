from importlib.metadata import version, PackageNotFoundError

def get_pkg_version(name: str) -> str:
    try:
        __version__ = version(name)  # works when dist name == package name
    except PackageNotFoundError:
        __version__ = "0.0.0+unknown"
    return __version__