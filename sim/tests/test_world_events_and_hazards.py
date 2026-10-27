"""Complaint 493: base-rate world hazards hit every country, a dated world event log keeps a bounded number of years, and
the yearly checks run in a game of several countries. Complaint 640: each rule is called on the hazards module over plain views,
and the checks in the `world_events` command are in test_world_events_command_and_save."""
QUICK_TOPIC = True

import types
import unittest
from unittest import mock

from sim.engine import invariants, year_run
from sim.engine.forward_hazards import HazardsForwardsMixin
from sim.hazards import world_data
from sim.hazards.commands import RecordWorldEvent
from sim.tests import hazards_host, module_harness


def _module(year=100, partners=(), civ_id="rome", events=True):
    return hazards_host.build(year=lambda: year_of[0], civilisation={"id": civ_id}, events_enabled=events,
                              partners_in_agent_economy=list(partners), weather_seed=lambda salt, region=None: 12345)


year_of = [100]


class WorldEventLogTests(unittest.TestCase):

    def setUp(self):
        year_of[0] = 100

    def record(self, module, kind, **fields):
        return module.record_world_event(RecordWorldEvent(kind, **fields))

    def test_a_record_carries_year_kind_actors_tiles_cause_and_facts(self):
        year_of[0] = 210
        entry = self.record(_module(), "flood", actors=("rome",), tiles=("t1",), cause="rain", facts={"died": 3.0})
        self.assertEqual((entry["year"], entry["kind"], entry["actors"], entry["tiles"], entry["cause"], entry["facts"]),
                         (210, "flood", ["rome"], ["t1"], "rain", {"died": 3.0}))

    def test_records_older_than_the_kept_years_are_dropped(self):
        module = _module()
        self.record(module, "flood", actors=("x",))
        year_of[0] += world_data.years_kept() + 1
        self.record(module, "flood", actors=("y",))
        self.assertEqual([row["actors"] for row in module.world.world_events], [["y"]])

    def test_rows_filter_by_kind_year_and_actor_oldest_first(self):
        module = _module()
        self.record(module, "flood", actors=("a",))
        year_of[0] = 105
        self.record(module, "famine", actors=("b",))
        self.record(module, "flood", actors=("b",))
        self.assertEqual(len(module.world_events()), 3)
        self.assertEqual(len(module.world_events("flood")), 2)
        self.assertEqual(len(module.world_events(since_year=105)), 2)
        self.assertEqual([row["kind"] for row in module.world_events(actor="b")], ["famine", "flood"])


class DrawTests(unittest.TestCase):

    def test_a_countrys_draw_is_the_same_on_every_call_and_differs_between_countries(self):
        module = _module()
        self.assertEqual(module.country_draw("han", "flood", 100), module.country_draw("han", "flood", 100))
        self.assertNotEqual(module.country_draw("han", "flood", 100), module.country_draw("rome", "flood", 100))

    def test_the_draw_differs_between_years_and_kinds(self):
        module = _module()
        self.assertNotEqual(module.country_draw("han", "flood", 100), module.country_draw("han", "flood", 101))
        self.assertNotEqual(module.country_draw("han", "flood", 100), module.country_draw("han", "fire", 100))

    def test_the_countries_in_a_game_are_the_home_country_then_its_partners(self):
        self.assertEqual(_module(partners=("han",), civ_id="rome").countries_in_game(), ["rome", "han"])

    def test_a_game_without_events_draws_no_hazards(self):
        module = _module(events=False)
        module.step_world_hazards([])
        self.assertEqual(module_harness.sent(module), [])

    def test_a_certain_hazard_hits_every_country_and_a_zero_chance_hits_none(self):
        flood = next(entry for entry in world_data.hazards() if entry["kind"] == "flood")
        for chance, expected in ((1.0, ["rome", "han"]), (0.0, [])):
            module, hit = _module(partners=("han",)), []
            module.hit_country = lambda country, hazard: hit.append(country)
            with mock.patch.object(world_data, "hazards", lambda: [dict(flood, annual_chance=chance)]):
                module.step_world_hazards([])
            self.assertEqual(hit, expected)


def _game(partners=(), debug=False):
    game = types.SimpleNamespace(debug=debug, view=lambda name: lambda: ["rome"] + list(partners))
    game.check_yearly_world = lambda: HazardsForwardsMixin.check_yearly_world(game)
    return game


class YearlyChecksTests(unittest.TestCase):

    def test_a_year_in_a_multi_country_game_runs_the_yearly_checks_with_debug_off(self):
        game = _game(partners=("han",))
        ran = []
        with mock.patch.object(invariants, "check_yearly_invariants", lambda target: ran.append(target) or True), \
                mock.patch.object(year_run, "run_phases", lambda target: None):
            year_run.run_year(game)
        self.assertEqual(ran, [game])

    def test_a_single_country_game_does_not_pay_for_them(self):
        game = _game()
        ran = []
        with mock.patch.object(invariants, "check_yearly_invariants", lambda target: ran.append(target) or True), \
                mock.patch.object(year_run, "run_phases", lambda target: None):
            year_run.run_year(game)
        self.assertEqual(ran, [])

    def test_debug_runs_the_full_step_invariants_instead(self):
        game = _game(debug=True)
        verified = []
        with mock.patch.object(year_run, "run_phases", lambda target: None), \
                mock.patch.object(year_run.year_steps, "verify_step_invariants", lambda target: verified.append(target)):
            year_run.run_year(game)
        self.assertEqual(verified, [game])


if __name__ == "__main__":
    unittest.main()
