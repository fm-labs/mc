from __future__ import annotations

import os
import re
from typing import List, Optional, Callable, Mapping, Any


def split_url(url: str) -> tuple[str, str]:
    if "://" in url:
        protocol, path = url.split("://", 1)
    else:
        protocol = ""
        path = url
    return protocol, path



def split_container_image_url(image_url: str):
    """
    Splits a container image URL into its components: scheme, registry, image name, and tag.
    Example formats:
    - docker://registry/repo/image:tag
    - registry/repo/image:tag
    - repo/image:tag
    - image:tag
    - image
    """
    scheme = "https"
    registry = "" #"docker.io"
    image = ""
    tag = "latest"

    if "://" in image_url:
        scheme, rest = image_url.split("://", 1)
    else:
        rest = image_url

    if "/" in rest:
        parts = rest.split("/")
        if len(parts) > 2 or (len(parts) == 2 and ('.' in parts[0] or ':' in parts[0])):
            registry = parts[0]
            image = "/".join(parts[1:])
        else:
            image = rest
    else:
        image = rest

    if ":" in image:
        image, tag = image.rsplit(":", 1)

    return [scheme, registry, image, tag]




def parse_image_ref(ref: str) -> List[Optional[str]]:
    """
    Parse a Docker/OCI image reference and return:
        [registryhost, port, namespace, name, tag, digest]
    Return None for any component that's not present in the input.

    Supported forms (examples):
      - "ubuntu"
      - "ubuntu:22.04"
      - "nginx@sha256:deadbeef..."
      - "docker.io/library/ubuntu:latest"
      - "ghcr.io/org/app:1.2.3@sha256:..."
      - "registry.example.com:5000/team/app"
      - "http://unsecure-registry.example.com:5000/team/app"
      - "localhost:5000/app"
      - "docker://quay.io/org/sub/app:dev"
      - "[2001:db8::1]:5000/ns/app:tag"

    Notes:
      - No defaults are applied (e.g., no implicit docker.io or library).
      - If the first path segment does not look like a registry (no '.' or ':'
        and not 'localhost'), registryhost and port are returned as None.
    """
    if not ref or not isinstance(ref, str):
        return [None, None, None, None, None, None, None]

    s = ref.strip()

    # Strip optional transport scheme like docker://, oci://
    s = re.sub(r'^[a-zA-Z][a-zA-Z0-9+.-]*://', '', s)

    # Split out digest (everything after first '@')
    digest = None
    if '@' in s:
        s, digest = s.split('@', 1)
        digest = digest or None

    # Identify tag: the last colon *after* the last slash separates the tag
    tag = None
    last_slash = s.rfind('/')
    last_colon = s.rfind(':')
    if last_colon > last_slash:
        s, tag = s[:last_colon], s[last_colon + 1:] or None

    # Split into path parts
    parts = s.split('/') if s else []

    scheme = split_url(ref.strip())[0] if '://' in ref else None
    registryhost = None
    port = None
    remainder_idx = 0

    def looks_like_registry(p: str) -> bool:
        # A registry segment usually has a dot or a colon, or is 'localhost'
        # (per Docker's heuristics).
        return '.' in p or ':' in p or p == 'localhost' or p.startswith('[')

    if parts and looks_like_registry(parts[0]):
        registry_part = parts[0]
        remainder_idx = 1

        # Handle IPv6 in brackets: [::1]:5000 or [2001:db8::1]
        if registry_part.startswith('['):
            close = registry_part.find(']')
            if close != -1:
                host_inside = registry_part[1:close]
                registryhost = host_inside or None
                # Optional :port after ]
                rest = registry_part[close + 1 :]
                if rest.startswith(':'):
                    port_str = rest[1:]
                    port = port_str if port_str else None
            else:
                # Malformed bracket use; treat whole as host
                registryhost = registry_part
        else:
            # Non-bracketed: split host:port on the last colon
            if ':' in registry_part:
                host, p = registry_part.rsplit(':', 1)
                registryhost = host or None
                port = p or None
            else:
                registryhost = registry_part or None

    # Remaining path components
    path_parts = parts[remainder_idx:]
    name = None
    namespace = None
    if path_parts:
        name = path_parts[-1] or None
        if len(path_parts) > 1:
            namespace = '/'.join(path_parts[:-1]) or None

    return [scheme, registryhost, port, namespace, name, tag, digest]


# Matches ${{var_name}} where var_name is letters/numbers/underscore and doesn't start with a digit
#DOUBLE_BRACE_PATTERN = re.compile(r"\$\{\{([A-Za-z_.]\w*)\}\}")
DOUBLE_BRACE_PATTERN = re.compile(r"\$\{\{([A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*)\}\}")


class MissingVar(KeyError):
    pass


def substitute_double_brace(
        template: str,
        variables: Mapping[str, Any],
        on_missing: Callable[[str], str] | None = None,
) -> str:
    """
    Replace ${{var}} in `template` using `variables`.

    - variables: mapping of names to values; non-strings are str()-ed.
    - on_missing: optional function(name) -> replacement string.
                  If not provided, raises MissingVar on missing keys.
    """
    if not template or not isinstance(template, str):
        return template

    def _repl(m: re.Match) -> str:
        name = m.group(1)
        print("Substituting variable:", name)
        # env variable override
        if name.startswith("env."):
            env_var = name[4:].upper()
            if env_var in os.environ and len(str(os.environ[env_var]).strip()) > 0:
                print("Using environment variable override for", env_var)
                return str(os.environ[env_var])

        if name in variables:
            val = variables[name]
            return "" if val is None else str(val)
        if on_missing is not None:
            return on_missing(name)
        raise MissingVar(f"Missing variable: {name}")

    return DOUBLE_BRACE_PATTERN.sub(_repl, template)


