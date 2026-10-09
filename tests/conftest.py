import atexit
import os
import shutil
import sys
import tempfile
import types
from pathlib import Path
from typing import Any

# mc.config reads these at import time, so they must be set before any project import
_TEST_DATA_DIR = tempfile.mkdtemp(prefix="mc-test-")
atexit.register(shutil.rmtree, _TEST_DATA_DIR, ignore_errors=True)
os.environ["DATA_DIR"] = _TEST_DATA_DIR
os.environ["CONFIG_DIR"] = f"{_TEST_DATA_DIR}/etc"
os.environ["RESOURCES_DIR"] = str(Path(__file__).resolve().parent.parent / "resources")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret")

# ruff: noqa: E402 (the imports below depend on the environment set above)
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from objbase import LocalDirectoryStorage


@pytest.fixture
def storage(tmp_path) -> LocalDirectoryStorage:
    """A fresh, empty inventory storage per test."""
    return LocalDirectoryStorage(base_dir=str(tmp_path))


@pytest.fixture
def client(storage) -> TestClient:
    """A client for an app with only the inventory router mounted (no auth, no lifespan)."""
    from inventorydb.routes import router

    app = FastAPI()
    app.state.storage = storage
    app.include_router(router, prefix="/api")
    return TestClient(app)


class FakeItemModule(types.ModuleType):
    actions: dict[str, Any]
    views: dict[str, Any]


@pytest.fixture
def item_module(monkeypatch) -> FakeItemModule:
    """
    Register a fake item module for the 'variable' item type (which has a schema but no module),
    so tests can control the actions and views it exposes.
    """
    module = FakeItemModule("mc.inventory.item.variable")
    module.actions = {}
    module.views = {}
    monkeypatch.setitem(sys.modules, "mc.inventory.item.variable", module)
    return module
