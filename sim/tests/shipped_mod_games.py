"""Games built over the shipped code mods, for the smoke tests of each: the mod's folder is copied into a temporary mods directory,
consented there (the repository's own `mods/consent.json` is never written), and the game is built over that directory."""
import json
import shutil
import tempfile
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Sequence
from unittest import mock

from sim.engine import bridge_land, mod_code
from sim.engine.data import ROOT
from sim.tests import harness


class ModGames:
    """A temporary mods directory holding copies of shipped mods; `build` makes a game over it."""

    def __init__(self, mod_ids: Sequence[str], extra_mods: Optional[Dict[str, str]] = None):
        """`extra_mods` maps a mod id to the source of a small code mod written beside the shipped ones."""
        self.directory = tempfile.TemporaryDirectory()
        self.mods_dir = Path(self.directory.name) / "mods"
        self.mods_dir.mkdir()
        for mod_id in mod_ids:
            shutil.copytree(Path(ROOT) / "mods" / mod_id, self.mods_dir / mod_id, ignore=shutil.ignore_patterns("__pycache__"))
        for mod_id, source in (extra_mods or {}).items():
            (self.mods_dir / mod_id / "data").mkdir(parents=True)
            (self.mods_dir / mod_id / "mod.json").write_text(json.dumps({
                "id": mod_id, "name": mod_id, "version": "1", "dependencies": [], "conflicts": [], "code": ["hooks.py"], "permissions": ["code"]}))
            (self.mods_dir / mod_id / "hooks.py").write_text(source)
        for mod_id in list(mod_ids) + list(extra_mods or {}):
            mod_code.allow(str(self.mods_dir), mod_id)

    def build(self, factory: Callable[[], Any]) -> Any:
        with mock.patch.object(bridge_land, "MODS_DIR", str(self.mods_dir)):
            return factory()

    def unopened(self, **options: Any) -> Any:
        """A game whose agent economy has not opened (fast), over the mods."""
        return self.build(lambda: harness.unopened_sim(**options))

    def opened(self, **options: Any) -> Any:
        """A game whose agent economy has opened, over the mods."""
        return self.build(lambda: harness.sim(**options))

    def step(self, game: Any, years: int = 1) -> None:
        with mock.patch.object(bridge_land, "MODS_DIR", str(self.mods_dir)):
            for _year in range(years):
                game.step()

    def close(self) -> None:
        mod_code.LOADED.clear()
        mod_code.MOD_OPERATIONS.clear()
        self.directory.cleanup()
