from pathlib import Path

import pytest

from inventorydb.itemtype import InventoryItemType
from inventorydb.overrides import ItemTypeOverride, load_overrides
from inventorydb.registry import InventoryRegistry


def write_toml(tmp_path: Path, content: str) -> str:
    path = tmp_path / "inventory.toml"
    path.write_text(content)
    return str(path)


class TestLoadOverrides:
    def test_missing_file(self, tmp_path):
        assert load_overrides(str(tmp_path / "missing.toml")) == ({}, [])

    def test_parses_types(self, tmp_path):
        path = write_toml(
            tmp_path,
            """
            [types.app-template]
            enabled = false

            [types.app_stack]
            title = "Stacks"
            icon = "layers"
            order = 1
            """,
        )
        overrides, warnings = load_overrides(path)
        assert warnings == []
        assert overrides == {
            "app-template": ItemTypeOverride(enabled=False),
            # names are normalized
            "app-stack": ItemTypeOverride(title="Stacks", icon="layers", order=1),
        }

    def test_invalid_toml(self, tmp_path):
        path = write_toml(tmp_path, "[types.x\n")
        overrides, warnings = load_overrides(path)
        assert overrides == {}
        assert warnings[0].startswith(f"Ignored {path}:")

    def test_invalid_values(self, tmp_path):
        path = write_toml(
            tmp_path,
            """
            [other]
            [types]
            plain = "x"
            [types.thing]
            enabled = "no"
            order = true
            colour = "red"
            title = "Thing"
            """,
        )
        overrides, warnings = load_overrides(path)
        # valid keys are kept
        assert overrides == {"thing": ItemTypeOverride(title="Thing")}
        assert warnings == [
            f"{path}: unknown section [other]",
            f"{path}: [types.plain] must be a table",
            f"{path}: [types.thing] 'enabled' must be bool",
            f"{path}: [types.thing] 'order' must be int",
            f"{path}: [types.thing] unknown key 'colour'",
        ]

    def test_types_must_be_a_table(self, tmp_path):
        path = write_toml(tmp_path, 'types = "x"\n')
        assert load_overrides(path) == ({}, [f"{path}: 'types' must be a table"])


class FakeSource:
    """A source with item types whose module loaders record that they ran."""

    def __init__(self, *names: str) -> None:
        self.names = names
        self.loaded: list[str] = []

    def load(self) -> tuple[list[InventoryItemType], list[str]]:
        def loader(name: str):
            def load():
                self.loaded.append(name)
                return None

            return load

        types = [
            InventoryItemType(
                name=n, schema={"title": n.title(), "$icon": "box"}, source="fake", module_loader=loader(n)
            )
            for n in self.names
        ]
        return types, []


class TestRegistryOverrides:
    def test_disabled_type_is_not_loaded(self, tmp_path):
        source = FakeSource("alpha", "beta")
        reg = InventoryRegistry([source], write_toml(tmp_path, "[types.beta]\nenabled = false\n"))
        assert [t.name for t in reg.types()] == ["alpha"]
        # the disabled type's code never ran
        assert source.loaded == ["alpha"]
        assert reg.warnings == []

    def test_disabled_type_is_disabled_in_all_sources(self, tmp_path):
        reg = InventoryRegistry(
            [FakeSource("alpha"), FakeSource("alpha")], write_toml(tmp_path, "[types.alpha]\nenabled = false\n")
        )
        assert reg.types() == []

    def test_title_and_icon(self, tmp_path):
        source = FakeSource("alpha")
        original_schema = {"title": "Alpha", "$icon": "box"}
        reg = InventoryRegistry([source], write_toml(tmp_path, '[types.alpha]\ntitle = "First"\nicon = "star"\n'))
        item_type = reg.get("alpha")
        assert item_type is not None
        assert item_type.info().title == "First"
        assert item_type.info().icon == "star"
        # the schema served to the UI has the new title too
        assert item_type.schema == {"title": "First", "$icon": "star"}
        assert original_schema == {"title": "Alpha", "$icon": "box"}

    def test_order(self, tmp_path):
        source = FakeSource("alpha", "beta", "gamma", "delta")
        toml = "[types.gamma]\norder = 1\n[types.delta]\norder = 2\n"
        reg = InventoryRegistry([source], write_toml(tmp_path, toml))
        assert [t.name for t in reg.types()] == ["gamma", "delta", "alpha", "beta"]

    def test_unknown_type(self, tmp_path):
        path = write_toml(tmp_path, "[types.nope]\nenabled = false\n")
        reg = InventoryRegistry([FakeSource("alpha")], path)
        assert reg.warnings == [f"{path}: [types.nope] matches no item type"]

    def test_file_warnings_are_reported(self, tmp_path):
        path = write_toml(tmp_path, "[types.alpha]\ncolour = 1\n")
        reg = InventoryRegistry([FakeSource("alpha")], path)
        assert reg.warnings == [f"{path}: [types.alpha] unknown key 'colour'"]

    def test_reload_rereads_file(self, tmp_path):
        path = write_toml(tmp_path, "")
        reg = InventoryRegistry([FakeSource("alpha")], path)
        assert "alpha" in reg
        write_toml(tmp_path, "[types.alpha]\nenabled = false\n")
        reg.load()
        assert "alpha" not in reg

    @pytest.mark.parametrize("overrides_file", [None, "/nonexistent/inventory.toml"])
    def test_no_overrides(self, overrides_file):
        reg = InventoryRegistry([FakeSource("alpha")], overrides_file)
        assert [t.name for t in reg.types()] == ["alpha"]
