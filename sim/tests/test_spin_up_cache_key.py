"""The cached spin-ups (the agent economy's hidden years, the labour market's trade split) are keyed on
what they start from and on the source that runs them, and on nothing else.

sim/engine/economy_port_key.py, sim/labour/workforce_spinup.py.
"""
QUICK_TOPIC = True

import dataclasses
import os
import shutil
import tempfile
import unittest
from typing import Any, Dict

from sim.engine import economy_port_key, solve_cache, source_closure
from sim.labour import workforce_spinup

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@dataclasses.dataclass
class _Setup:
    civ_id: str = "rome_100ad"
    working_hours_per_year: float = 2400.0
    prices: Dict[str, float] = dataclasses.field(default_factory=lambda: {"wheat": 1.0})
    world_map: Any = dataclasses.field(default_factory=lambda: {"tiles": [1, 2]})


def _write(root, relative, text):
    path = os.path.join(root, relative)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a") as handle:
        handle.write(text)


class SetupDigestTests(unittest.TestCase):
    def test_every_field_changes_the_key(self):
        base = economy_port_key.setup_digest(_Setup())
        self.assertEqual(base, economy_port_key.setup_digest(_Setup()))
        for change in ({"civ_id": "china_100ad"}, {"working_hours_per_year": 2500.0},
                       {"prices": {"wheat": 1.1}}, {"world_map": {"tiles": [1, 3]}}):
            self.assertNotEqual(base, economy_port_key.setup_digest(_Setup(**change)), change)


class _Map:
    def __init__(self, map_id, tiles, folder):
        self.map_id, self.tiles, self.folders = map_id, tiles, (folder,)


class ObjectContentTests(unittest.TestCase):
    """An object inside the setup (the world map) is keyed on what it holds, never on its address."""

    def test_equal_maps_built_separately_give_one_digest(self):
        first = _Setup(world_map=_Map("m", {"a": {"food": 1}}, os.path.join(ROOT, "data", "maps")))
        second = _Setup(world_map=_Map("m", {"a": {"food": 1}}, os.path.join(ROOT, "data", "maps")))
        self.assertIsNot(first.world_map, second.world_map)
        self.assertEqual(economy_port_key.setup_digest(first), economy_port_key.setup_digest(second))

    def test_a_different_map_gives_a_different_digest(self):
        first = _Setup(world_map=_Map("m", {"a": {"food": 1}}, ROOT))
        second = _Setup(world_map=_Map("m", {"a": {"food": 2}}, ROOT))
        self.assertNotEqual(economy_port_key.setup_digest(first), economy_port_key.setup_digest(second))

    def test_paths_inside_the_checkout_do_not_depend_on_where_it_is(self):
        plain = economy_port_key._plain(os.path.join(ROOT, "data", "maps"))
        self.assertEqual(plain, os.path.join("data", "maps"))

    def test_a_value_with_no_content_to_key_on_is_refused(self):
        with self.assertRaises(TypeError):
            economy_port_key.setup_digest(_Setup(world_map=object()))


class ScopedSourceTests(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="spin_up_key_")
        self.original_root = solve_cache._ROOT
        self.original_modules = economy_port_key.SPIN_UP_SOURCE_MODULES
        for relative, text in {"data/a.json": "1", "sim/__init__.py": "",
                               "sim/engine/__init__.py": "",
                               "sim/engine/year.py": "from sim.economy import api\n",
                               "sim/economy/__init__.py": "", "sim/economy/api.py": "x = 1\n",
                               "sim/ui/__init__.py": "", "sim/ui/screen.py": "y = 1\n"}.items():
            _write(self.root, relative, text)
        solve_cache._ROOT = self.root
        economy_port_key.SPIN_UP_SOURCE_MODULES = ("sim.engine.year",)
        solve_cache.forget_environment_digest()

    def tearDown(self):
        solve_cache._ROOT = self.original_root
        economy_port_key.SPIN_UP_SOURCE_MODULES = self.original_modules
        solve_cache.forget_environment_digest()
        shutil.rmtree(self.root, ignore_errors=True)

    def _key_after_edit(self, relative):
        before = economy_port_key.spin_up_key(_Setup())
        _write(self.root, relative, "z = 1\n")
        solve_cache.forget_environment_digest()
        return before, economy_port_key.spin_up_key(_Setup())

    def test_editing_the_ui_keeps_the_key(self):
        before, after = self._key_after_edit("sim/ui/screen.py")
        self.assertEqual(before, after)

    def test_editing_what_the_spin_up_imports_changes_the_key(self):
        for relative in ("sim/economy/api.py", "sim/engine/year.py", "data/a.json"):
            before, after = self._key_after_edit(relative)
            self.assertNotEqual(before, after, relative)

    def test_a_setup_input_changes_the_key(self):
        self.assertNotEqual(economy_port_key.spin_up_key(_Setup()),
                            economy_port_key.spin_up_key(_Setup(working_hours_per_year=2500.0)))


class RealClosureTests(unittest.TestCase):
    def test_the_spin_up_closure_holds_the_economy_and_not_the_ui(self):
        files = source_closure.source_files(ROOT, economy_port_key.SPIN_UP_SOURCE_MODULES)
        relative = {os.path.relpath(path, ROOT) for path in files}
        self.assertIn(os.path.join("sim", "engine", "economy_port_year.py"), relative)
        self.assertIn(os.path.join("sim", "economy", "api.py"), relative)
        self.assertFalse([path for path in relative if path.startswith(os.path.join("sim", "ui") + os.sep)])


class WorkforceSpinUpKeyTests(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="workforce_key_")
        self.original_root = workforce_spinup._REPOSITORY_ROOT
        for relative in ("sim/labour/a.py", "sim/ui/b.py", "sim/tests/c.py"):
            _write(self.root, relative, "x = 1\n")
        workforce_spinup._REPOSITORY_ROOT = self.root
        workforce_spinup.forget_in_process_cache()

    def tearDown(self):
        workforce_spinup._REPOSITORY_ROOT = self.original_root
        workforce_spinup.forget_in_process_cache()
        shutil.rmtree(self.root, ignore_errors=True)

    def _digest_after_edit(self, relative):
        before = workforce_spinup._source_digest()
        _write(self.root, relative, "y = 2\n")
        workforce_spinup.forget_in_process_cache()
        return before, workforce_spinup._source_digest()

    def test_editing_source_changes_the_digest(self):
        before, after = self._digest_after_edit("sim/labour/a.py")
        self.assertNotEqual(before, after)

    def test_editing_tests_or_the_ui_keeps_it(self):
        for relative in ("sim/ui/b.py", "sim/tests/c.py"):
            before, after = self._digest_after_edit(relative)
            self.assertEqual(before, after, relative)


if __name__ == "__main__":
    unittest.main()
