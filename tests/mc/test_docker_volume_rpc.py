from unittest.mock import MagicMock, patch

import pytest
from docker.errors import NotFound

from mc.docker.helper import docker_volume_backup, docker_volume_clone, docker_volume_restore
from mc.rpc import RPC_HANDLERS, dispatch_rpc_method, rpc_schemas


def make_client(existing_volumes=()):
    client = MagicMock()

    def get_volume(name):
        if name not in existing_volumes:
            raise NotFound(f"no such volume: {name}")
        return MagicMock(name=name)

    client.volumes.get.side_effect = get_volume
    client.containers.run.return_value = b""
    return client


# --- helpers ---------------------------------------------------------------


def test_backup_mounts_directory_and_writes_file():
    client = make_client(existing_volumes={"data"})
    docker_volume_backup(client, "data", "/srv/backups/data.tar.gz")

    args, kwargs = client.containers.run.call_args
    assert args[0] == "alpine"
    assert args[1] == ["tar", "czf", "/backup/data.tar.gz", "--numeric-owner", "-C", "/data", "."]
    assert kwargs["volumes"] == {
        "data": {"bind": "/data", "mode": "ro"},
        "/srv/backups": {"bind": "/backup", "mode": "rw"},
    }
    assert kwargs["remove"] is True


def test_backup_rejects_missing_volume():
    client = make_client()
    with pytest.raises(ValueError, match="does not exist"):
        docker_volume_backup(client, "nope", "/srv/backups/x.tar.gz")
    client.containers.run.assert_not_called()


@pytest.mark.parametrize("path", ["relative.tar.gz", "/srv/backups/"])
def test_backup_rejects_bad_paths(path):
    client = make_client(existing_volumes={"data"})
    with pytest.raises(ValueError):
        docker_volume_backup(client, "data", path)
    client.containers.run.assert_not_called()


def test_backup_file_name_is_not_shell_interpreted():
    client = make_client(existing_volumes={"data"})
    docker_volume_backup(client, "data", "/srv/x';rm -rf ~;'.tar.gz")
    cmd = client.containers.run.call_args.args[1]
    assert isinstance(cmd, list)
    assert cmd[2] == "/backup/x';rm -rf ~;'.tar.gz"


def test_restore_mounts_backup_read_only():
    client = make_client()
    docker_volume_restore(client, "data", "/srv/backups/data.tar.gz")

    args, kwargs = client.containers.run.call_args
    assert args[1] == ["tar", "xzf", "/backup/data.tar.gz", "--numeric-owner", "-C", "/data"]
    assert kwargs["volumes"] == {
        "data": {"bind": "/data", "mode": "rw"},
        "/srv/backups": {"bind": "/backup", "mode": "ro"},
    }


def test_clone_creates_target_and_copies():
    client = make_client(existing_volumes={"src"})
    docker_volume_clone(client, "src", "dst")

    client.volumes.create.assert_called_once_with("dst")
    args, kwargs = client.containers.run.call_args
    assert args[1] == ["cp", "-a", "/from/.", "/to/"]
    assert kwargs["volumes"] == {
        "src": {"bind": "/from", "mode": "ro"},
        "dst": {"bind": "/to", "mode": "rw"},
    }


def test_clone_refuses_existing_target():
    client = make_client(existing_volumes={"src", "dst"})
    with pytest.raises(ValueError, match="already exists"):
        docker_volume_clone(client, "src", "dst")
    client.volumes.create.assert_not_called()
    client.containers.run.assert_not_called()


# --- rpc -------------------------------------------------------------------


@pytest.mark.parametrize("method", ["docker.volume.backup", "docker.volume.restore", "docker.volume.clone"])
def test_volume_methods_are_registered(method):
    assert method in RPC_HANDLERS
    assert any(s["method"] == method for s in rpc_schemas())


def test_rpc_backup_success():
    client = make_client(existing_volumes={"data"})
    with patch("docker.from_env", return_value=client):
        result = dispatch_rpc_method(
            "docker.volume.backup", {"volume": "data", "backup_file": "/srv/backups/data.tar.gz"}
        )
    assert result["status"] == "success"
    assert result["stdout"] == ""


def test_rpc_clone_returns_error_instead_of_raising():
    client = make_client()
    with patch("docker.from_env", return_value=client):
        result = dispatch_rpc_method("docker.volume.clone", {"source_volume": "nope", "target_volume": "dst"})
    assert "does not exist" in result["error"]


def test_rpc_restore_schema_requires_volume_and_file():
    schema = next(s for s in rpc_schemas() if s["method"] == "docker.volume.restore")
    assert set(schema["inputSchema"]["required"]) == {"volume", "backup_file"}
