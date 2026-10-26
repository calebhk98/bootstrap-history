"""The year's phases are a registry: the shipped order is fixed, a mod places its own phase by constraints."""

QUICK_TOPIC = True

import contextlib
import json
import unittest

from sim.engine import mod_code, year_phases
from sim.engine.mods import ModError
from sim.engine.year_phases import SEAT, SHIPPED, WORLD
from sim.tests.test_mod_removal_and_civs import ModTestBase

ALPHA, BETA = "test_alpha_p1xz", "test_beta_p1xz"
SHIPPED_ORDER = [
    "begin_seat_year", "trim_audit", "hear_of_other_seats", "begin_world_year", "apprenticeships", "staff", "money_seat", "money_world",
    "win_conditions", "dated_shocks", "drop_ended_seats", "seat_prelude", "start_projects", "materials", "material_shortage_notes", "seat_work", "market",
    "coin_revaluation", "wage_market_ratios", "wild_stock", "soil_nitrogen", "living_stock",
    "defence_stores", "random_events", "world_hazards", "campaigns", "revolts", "famine_watch", "credit_limit", "advance_year"]


class FakeSim:
    """Records which phase handlers ran."""
    events = False

    def __init__(self, ended=()):
        self.log = []
        self.ended = ended

    def playing_seats(self):
        return ["a", "b"]

    def ended_seats(self):
        return self.ended

    @contextlib.contextmanager
    def act_as(self, seat_id):
        yield


def mod_phase(owner, name, scope=SEAT, after=(), before=()):
    if scope == SEAT:
        def handler(sim, seat_id):
            sim.log.append((name, seat_id))
    else:
        def handler(sim, seats):
            sim.log.append((name, "world"))
    return year_phases.Phase(owner + ":" + name, scope, handler, owner, tuple(after), tuple(before))


class PhaseTestBase(unittest.TestCase):
    def setUp(self):
        year_phases.MOD_PHASES.clear()

    def tearDown(self):
        year_phases.MOD_PHASES.clear()

    def names(self):
        return [phase.name for phase in year_phases.ordered_phases()]


class OrderTests(PhaseTestBase):
    def test_shipped_order_without_mods(self):
        self.assertEqual(self.names(), SHIPPED_ORDER)
        self.assertEqual([phase.name for phase in SHIPPED], SHIPPED_ORDER)

    def test_after_runs_between_the_phase_and_its_successor(self):
        year_phases.register_mod_phase(mod_phase(ALPHA, "conflict", after=["market"]))
        names = self.names()
        self.assertEqual(names[names.index("market") + 1], ALPHA + ":conflict")
        self.assertEqual(names[names.index("market") + 2], "coin_revaluation")

    def test_before_runs_right_before_the_phase(self):
        year_phases.register_mod_phase(mod_phase(ALPHA, "magic", before=["seat_work"]))
        names = self.names()
        self.assertEqual(names[names.index("seat_work") - 1], ALPHA + ":magic")

    def test_two_mods_after_one_phase_keep_load_order(self):
        year_phases.register_mod_phase(mod_phase(ALPHA, "one", after=["market"]))
        year_phases.register_mod_phase(mod_phase(BETA, "two", after=["market"]))
        names = self.names()
        start = names.index("market")
        self.assertEqual(names[start + 1:start + 3], [ALPHA + ":one", BETA + ":two"])

    def test_a_mod_phase_can_follow_another_mods(self):
        year_phases.register_mod_phase(mod_phase(BETA, "late", after=[ALPHA + ":early"]))
        year_phases.register_mod_phase(mod_phase(ALPHA, "early", after=["market"]))
        names = self.names()
        start = names.index("market")
        self.assertEqual(names[start + 1:start + 3], [ALPHA + ":early", BETA + ":late"])

    def test_a_cycle_names_both_mods(self):
        year_phases.register_mod_phase(mod_phase(ALPHA, "x", after=[BETA + ":y"]))
        year_phases.register_mod_phase(mod_phase(BETA, "y", after=[ALPHA + ":x"]))
        with self.assertRaises(ModError) as caught:
            year_phases.ordered_phases()
        self.assertIn(ALPHA, str(caught.exception))
        self.assertIn(BETA, str(caught.exception))

    def test_an_unknown_phase_is_an_error(self):
        year_phases.register_mod_phase(mod_phase(ALPHA, "x", after=["no_such_phase"]))
        with self.assertRaises(ModError) as caught:
            year_phases.ordered_phases()
        self.assertIn("no_such_phase", str(caught.exception))
        self.assertIn(ALPHA, str(caught.exception))

    def test_constraints_that_cannot_both_hold_name_the_mod_and_the_shipped_phases(self):
        year_phases.register_mod_phase(mod_phase(ALPHA, "x", after=["market"], before=["staff"]))
        with self.assertRaises(ModError) as caught:
            year_phases.ordered_phases()
        for part in (ALPHA, "market", "staff"):
            self.assertIn(part, str(caught.exception))


class RunTests(PhaseTestBase):
    def test_a_mod_phase_runs_once_for_the_world_or_once_per_seat(self):
        year_phases.register_mod_phase(mod_phase(ALPHA, "seatly", after=["market"]))
        year_phases.register_mod_phase(mod_phase(BETA, "worldly", WORLD, after=["advance_year"]))
        sim = FakeSim()
        year_phases.run_phases(sim, [phase for phase in year_phases.ordered_phases() if phase.owner])
        self.assertEqual(sim.log, [("seatly", "a"), ("seatly", "b"), ("worldly", "world")])

    def test_when_every_seat_has_ended_the_rest_of_the_year_does_not_run(self):
        year_phases.register_mod_phase(mod_phase(ALPHA, "last", after=["advance_year"]))
        sim = FakeSim(ended=("a", "b"))
        phases = [phase for phase in year_phases.ordered_phases() if phase.name in ("drop_ended_seats", ALPHA + ":last")]
        year_phases.run_phases(sim, phases)
        self.assertEqual(sim.log, [])

    def test_ended_seats_leave_the_seat_phases(self):
        year_phases.register_mod_phase(mod_phase(ALPHA, "seatly", after=["drop_ended_seats"]))
        sim = FakeSim(ended=("a",))
        phases = [phase for phase in year_phases.ordered_phases() if phase.name in ("drop_ended_seats", ALPHA + ":seatly")]
        year_phases.run_phases(sim, phases)
        self.assertEqual(sim.log, [("seatly", "b")])


class LoadTests(ModTestBase):
    def tearDown(self):
        year_phases.MOD_PHASES.clear()
        mod_code.LOADED.clear()
        mod_code.COMMAND_REGISTRATIONS.clear()
        super().tearDown()

    def add_code_mod(self, mod_id, source):
        self.add_mod(mod_id)
        folder = self.mods_dir / mod_id
        (folder / "hooks.py").write_text(source)
        manifest = json.loads((folder / "mod.json").read_text())
        manifest.update(code=["hooks.py"], permissions=["code"])
        (folder / "mod.json").write_text(json.dumps(manifest))
        mod_code.allow(str(self.mods_dir), mod_id)

    def register_phase(self, arguments):
        self.add_code_mod(ALPHA, 'def register(api):\n    api.phase("conflict", "world", lambda sim, seats: None%s)\n' % arguments)
        mod_code.run_mod_code(str(self.mods_dir))

    def test_a_mod_registers_a_phase_through_the_api(self):
        self.register_phase(', after="market"')
        names = [phase.name for phase in year_phases.ordered_phases()]
        self.assertEqual(names[names.index("market") + 1], ALPHA + ":conflict")

    def test_a_bad_constraint_is_a_load_error(self):
        with self.assertRaises(ModError):
            self.register_phase(', after="nope"')

    def test_a_phase_without_constraints_is_refused(self):
        with self.assertRaises(ModError):
            self.register_phase("")


if __name__ == "__main__":
    unittest.main()
