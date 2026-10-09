import subprocess
import sys
import textwrap
from collections.abc import Iterator
from pathlib import Path

import pytest
from objbase import LocalDirectoryStorage, LocalFileStorage, SQLiteStorage

from inventorydb.settings import InventorySettings, configure_inventory, get_inventory_settings
from inventorydb.storage import build_objbase_storage, get_inventory_storage_instance

SRC_DIR = Path(__file__).resolve().parents[2] / "src"


@pytest.fixture
def restore_settings() -> Iterator[None]:
    settings = get_inventory_settings()
    yield
    configure_inventory(settings)


def test_defaults():
    settings = InventorySettings()
    assert settings.storage_type == "directory"
    assert settings.storage_dir == "inventory"
    assert settings.item_packages == ()
    assert settings.plugin_packages == ()
    assert settings.entry_point_group == "inventorydb.item_types"
    assert settings.user_dir is None
    assert settings.user_code is False
    assert settings.overrides_file is None


def test_configure(restore_settings):
    settings = InventorySettings(storage_dir="/x")
    configure_inventory(settings)
    assert get_inventory_settings() is settings


class TestStorage:
    @pytest.mark.parametrize(
        "storage_type, storage_class",
        [("directory", LocalDirectoryStorage), ("file", LocalFileStorage), ("sqlite", SQLiteStorage)],
    )
    def test_storage_types(self, tmp_path, storage_type, storage_class):
        storage_dir = tmp_path / "data" / "inventory"
        storage = build_objbase_storage(InventorySettings(storage_type=storage_type, storage_dir=str(storage_dir)))
        assert isinstance(storage, storage_class)
        assert storage_dir.is_dir()
        storage.write("thing", {"id": "a"})
        assert storage.read("thing", "a") == {"id": "a"}

    def test_unknown_storage_type(self, tmp_path):
        with pytest.raises(ValueError, match="Unknown storage type 'redis'"):
            build_objbase_storage(InventorySettings(storage_type="redis", storage_dir=str(tmp_path)))

    def test_shared_storage_follows_settings(self, tmp_path, restore_settings):
        before = get_inventory_storage_instance()
        assert get_inventory_storage_instance() is before
        configure_inventory(InventorySettings(storage_dir=str(tmp_path / "other")))
        after = get_inventory_storage_instance()
        assert after is not before
        after.write("thing", {"id": "a"})
        assert (tmp_path / "other" / "thing" / "a.json").exists()


def test_inventorydb_does_not_import_mc(tmp_path):
    """inventorydb is self-contained: using it with its default settings never imports mc."""
    code = textwrap.dedent(
        f"""
        import sys
        sys.path.insert(0, {str(SRC_DIR)!r})
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from inventorydb.registry import get_inventory_registry
        from inventorydb.routes import router
        from inventorydb.storage import get_inventory_storage_instance
        import inventorydb.handler, inventorydb.items, inventorydb.overrides, inventorydb.sources

        app = FastAPI()
        app.state.storage = get_inventory_storage_instance()
        app.include_router(router, prefix="/api")
        assert TestClient(app).get("/api/inventory/").json() == [], "no item types by default"
        assert get_inventory_registry().warnings == []

        loaded = sorted(m for m in sys.modules if m == "mc" or m.startswith("mc."))
        assert not loaded, loaded
        print("ok")
        """
    )
    result = subprocess.run([sys.executable, "-I", "-c", code], cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "ok"
    # the default storage dir is relative to the working directory
    assert (tmp_path / "inventory").is_dir()
