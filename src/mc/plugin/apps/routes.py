import json
import logging
import os
import subprocess
from typing import AsyncGenerator, Literal

import pydantic
import yaml
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from starlette.requests import Request
from starlette.responses import StreamingResponse

from mc.docker.compose_runner import (
    DockerComposeArgs,
    DockerComposeDownArgs,
    DockerComposeStopArgs,
    DockerComposeUpArgs,
)
from mc.plugin.apps.apps_helper import (
    AppNetworkSpec,
    AppSpec,
    AppVolumeSpec,
    compose_declared_names,
    app_spec_exists,
    get_appspec_path,
    list_app_specs,
    load_app_spec,
    save_app_spec,
    validate_app_id,
    validate_compose_stackfile,
)
from mc.server.stream_helper import starlette_subprocess_stream, sse_event, streaming_response

logger = logging.getLogger(__name__)

router = APIRouter()


class CreateAppFromScratchRequest(BaseModel):
    id: str
    title: str | None = None
    description: str | None = None
    stackfile_content: str  # compose.yaml body
    volumes: list[AppVolumeSpec] = []
    networks: list[AppNetworkSpec] = []


class UpdateAppRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    stackfile_content: str | None = None  # compose.yaml body; omit to keep the current file
    volumes: list[AppVolumeSpec] | None = None  # omit to keep the current list
    networks: list[AppNetworkSpec] | None = None  # omit to keep the current list


class AppSpecDetails(BaseModel):
    spec: AppSpec
    spec_path: str
    stackfile_path: str | None = None
    stackfile_content: str | None = None
    # names declared at the top level of the compose file, as hints for the override editors
    compose_volumes: list[str] = []
    compose_networks: list[str] = []
    # compose.override.yaml generated from the spec on save
    override_path: str | None = None
    override_content: str | None = None
    # only set by create / update: overrides that couldn't be applied
    compile_warnings: list[str] = []


def _validation_error(e: pydantic.ValidationError) -> HTTPException:
    return HTTPException(status_code=422, detail=e.errors(include_url=False, include_context=False, include_input=False))


def _compile(spec: AppSpec) -> list[str]:
    """Regenerate the override files. The spec is already saved, so failures become warnings."""
    try:
        return spec.compile()
    except Exception as e:
        logger.exception(f"Compiling app {spec.id} failed")
        return [f"Generating compose.override.yaml failed: {e}"]


def _details(spec: AppSpec, compile_warnings: list[str] | None = None) -> AppSpecDetails:
    details = AppSpecDetails(
        spec=spec, spec_path=get_appspec_path(spec.id), compile_warnings=compile_warnings or []
    )
    if spec.stackfile:
        details.stackfile_path = spec.stackfile_path
        try:
            details.stackfile_content = spec.read_stackfile()
        except FileNotFoundError:
            details.stackfile_content = None
    if details.stackfile_content:
        try:
            stack = yaml.safe_load(details.stackfile_content)
        except yaml.YAMLError:
            stack = None
        details.compose_volumes, details.compose_networks = compose_declared_names(stack)
    if spec.type == "compose" and os.path.isfile(spec.override_path):
        details.override_path = spec.override_path
        with open(spec.override_path) as f:
            details.override_content = f.read()
    return details


def _load_or_404(app_id: str) -> AppSpec:
    try:
        return load_app_spec(app_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.get("/apps")
def apps_list() -> list[AppSpec]:
    """List app specs."""
    return list_app_specs()


@router.post("/apps/new/scratch")
def create_app_from_scratch(body: CreateAppFromScratchRequest) -> AppSpecDetails:
    """New compose app from a hand-written compose.yaml."""
    try:
        validate_app_id(body.id)
        if app_spec_exists(body.id):
            raise HTTPException(status_code=409, detail=f"App '{body.id}' already exists")
        spec = AppSpec.create_from_string(
            body.id, body.stackfile_content, title=body.title, description=body.description,
            volumes=body.volumes, networks=body.networks,
        )
    except pydantic.ValidationError as e:
        raise _validation_error(e) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return _details(spec, _compile(spec))


@router.post("/apps/new/bundle")
def create_app_from_bundle():
    """New app from a tar bundle file"""
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/apps/{app_id}")
def apps_get(app_id: str) -> AppSpecDetails:
    """Get an app spec with its compose file."""
    return _details(_load_or_404(app_id))


@router.put("/apps/{app_id}")
def apps_update(app_id: str, body: UpdateAppRequest) -> AppSpecDetails:
    """Update an app spec and (optionally) its compose file."""
    spec = _load_or_404(app_id)
    try:
        if body.stackfile_content is not None:
            if spec.type != "compose":
                raise ValueError("Only compose apps have a stackfile")
            validate_compose_stackfile(body.stackfile_content)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    fields = body.model_dump(exclude_unset=True, exclude={"stackfile_content"})
    try:
        # re-validate the whole spec, model_copy() would skip the validators
        spec = AppSpec.model_validate({**spec.model_dump(), **fields})
    except pydantic.ValidationError as e:
        raise _validation_error(e) from e
    if body.stackfile_content is not None:
        spec.write_stackfile(body.stackfile_content)
    save_app_spec(spec)
    return _details(spec, _compile(spec) if spec.type == "compose" else None)


class CompiledFile(BaseModel):
    name: str
    path: str
    content: str


class CompiledAppSpec(BaseModel):
    # compose files passed to docker compose, in order
    files: list[CompiledFile]
    # `docker compose config` output: the files merged, with variables resolved
    merged: str | None = None
    merged_error: str | None = None


COMPOSE_CONFIG_TIMEOUT = 30


def _compose_config(spec: AppSpec) -> tuple[str | None, str | None]:
    """(merged config, error) from `docker compose config`."""
    cmd, env = spec.compose_runner(global_args=["--ansi", "never"]).compose_cmd("config")
    try:
        r = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=COMPOSE_CONFIG_TIMEOUT)
    except FileNotFoundError:
        return None, "docker CLI not found"
    except subprocess.TimeoutExpired:
        return None, f"docker compose config timed out after {COMPOSE_CONFIG_TIMEOUT}s"
    if r.returncode != 0:
        return None, (r.stderr or r.stdout).strip() or f"docker compose config exited with {r.returncode}"
    return r.stdout, None


@router.get("/apps/{app_id}/compiled")
def apps_compiled(app_id: str) -> CompiledAppSpec:
    """The compose files an app runs with, and their merged result."""
    spec = _load_or_404(app_id)
    if spec.type != "compose" or not spec.stackfile:
        raise HTTPException(status_code=400, detail="Only compose apps have compiled specs")
    if not os.path.isfile(spec.stackfile_path):
        raise HTTPException(status_code=400, detail=f"Compose file not found: {spec.stackfile_path}")

    files = []
    for path in spec.stackfile_paths():
        with open(path) as f:
            files.append(CompiledFile(name=os.path.basename(path), path=path, content=f.read()))
    try:
        merged, merged_error = _compose_config(spec)
    except ValueError as e:  # e.g. project dir outside MC_HOME
        merged, merged_error = None, str(e)
    return CompiledAppSpec(files=files, merged=merged, merged_error=merged_error)


# Line-based, uncolored compose output for streaming
STREAM_GLOBAL_ARGS = ["--progress", "plain", "--ansi", "never"]

AppAction = Literal["up", "down", "stop", "restart"]


def _action_cmd(spec: AppSpec, action: AppAction) -> tuple[list[str], dict[str, str]]:
    runner = spec.compose_runner(global_args=STREAM_GLOBAL_ARGS)
    if action == "up":
        # always detach: an attached `up` never exits, and a client disconnect would stop the containers
        return runner.up_cmd(DockerComposeUpArgs(detach=True, remove_orphans=True, yes=True, no_color=True))
    if action == "down":
        return runner.compose_cmd("down", **DockerComposeDownArgs().model_dump())
    if action == "stop":
        return runner.compose_cmd("stop", **DockerComposeStopArgs().model_dump())
    return runner.compose_cmd("restart", **DockerComposeArgs().model_dump())


@router.post("/apps/{app_id}/action/{action}")
async def apps_action_stream(request: Request, app_id: str, action: AppAction,
                             format: Literal["sse", "json"] = "json") -> StreamingResponse:
    """
    Run a docker compose action for an app and stream its output.

    :param request: the webserver request object
    :param app_id: the app id
    :param action: compose action (up, down, stop, restart)
    :param format: format of the output (json or sse)
    :return: streaming response with STDOUT lines, then RC (or ERROR)
    """
    spec = _load_or_404(app_id)
    try:
        if spec.stackfile and not os.path.isfile(spec.stackfile_path):
            raise ValueError(f"Compose file not found: {spec.stackfile_path}")
        cmd, env = _action_cmd(spec, action)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    async def _stream_process_async() -> AsyncGenerator[str]:
        async for line in starlette_subprocess_stream(cmd, env=env, request=request):
            split = line.split(":", 1)
            if len(split) < 2:
                print("WARN: Unknown subprocess stream output: ", line)
                continue
            if format == "sse":
                yield sse_event(event=split[0], data=split[1])
            else:
                yield json.dumps({"event": split[0], "data": split[1]}) + "\n"

    return streaming_response(generator=_stream_process_async(), format=format)
