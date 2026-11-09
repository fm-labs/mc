import pytest
from fastapi import HTTPException

from mc.plugin.containers.routes import post_compose_action


class FakeContainer:
    def __init__(self, name, project, status, fail=False):
        self.id = name
        self.name = name
        self.attrs = {"State": {"Status": status}, "Config": {"Labels": {"com.docker.compose.project": project}}}
        self.calls = []
        self.fail = fail

    def _call(self, action):
        if self.fail:
            raise RuntimeError("boom")
        self.calls.append(action)

    def start(self):
        self._call("start")

    def stop(self):
        self._call("stop")

    def restart(self):
        self._call("restart")

    def unpause(self):
        self._call("unpause")

    def remove(self, force=False):
        self._call(f"remove force={force}")


class FakeClient:
    def __init__(self, containers):
        self.containers = self
        self.items = containers

    def list(self, all=False):
        assert all is True
        return self.items


@pytest.fixture
def containers():
    return {
        "web": FakeContainer("web", "shop", "running"),
        "db": FakeContainer("db", "shop", "exited"),
        "cache": FakeContainer("cache", "shop", "paused"),
        "other": FakeContainer("other", "blog", "exited"),
    }


@pytest.mark.parametrize(
    "action, expected",
    [
        ("up", {"web": [], "db": ["start"], "cache": ["unpause"]}),
        ("stop", {"web": ["stop"], "db": [], "cache": ["stop"]}),
        ("restart", {"web": ["restart"], "db": ["restart"], "cache": ["restart"]}),
        ("down", {"web": ["remove force=True"], "db": ["remove force=True"], "cache": ["remove force=True"]}),
    ],
)
def test_compose_actions(containers, action, expected):
    result = post_compose_action("local", "shop", action, FakeClient(list(containers.values())))
    assert result["status"] == "ok" and result["containers"] == 3
    assert {name: c.calls for name, c in containers.items() if name != "other"} == expected
    # other projects are not touched
    assert containers["other"].calls == []


def test_unknown_action(containers):
    with pytest.raises(HTTPException) as e:
        post_compose_action("local", "shop", "explode", FakeClient(list(containers.values())))
    assert e.value.status_code == 404


def test_unknown_project(containers):
    with pytest.raises(HTTPException) as e:
        post_compose_action("local", "nope", "up", FakeClient(list(containers.values())))
    assert e.value.status_code == 404


def test_partial_failure(containers):
    containers["db"].fail = True
    with pytest.raises(HTTPException) as e:
        post_compose_action("local", "shop", "restart", FakeClient(list(containers.values())))
    assert e.value.status_code == 400
    assert "1 of 3" in e.value.detail and "db: boom" in e.value.detail
    # the other containers were still restarted
    assert containers["web"].calls == ["restart"]
