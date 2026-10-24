"""Complaint 493: base-rate world hazards hit every country, a dated world event log keeps a bounded number of years, and
the yearly checks run in a game of several countries. Complaint 640: each rule is called on a stand-in game; the checks in
the `world_events` command is test_world_events_command_and_save."""
QUICK_TOPIC = True

import types
import unittest
from unittest import mock

from sim.engine import invariants, world_events, world_hazard_data, world_hazards, year_run


def _game(year=100, partners=(), civ_id="rome", events=True):
    game = types.SimpleNamespace(
        state=types.SimpleNamespace(scenario=types.SimpleNamespace(year=year),
                                    economy=types.SimpleNamespace(world_events=[])),
        civ={"id": civ_id}, events=events, debug=False)
    game.partners_in_agent_economy = lambda: list(partners)
    game._farm_year_weather_seed = lambda salt: 12345
    game.playing_seats = lambda: []
    game.check_yearly_world = lambda: world_hazards.WorldHazardsMixin.check_yearly_world(game)
    return game


class WorldEventLogTests(unittest.TestCase):

    def test_a_record_carries_year_kind_actors_tiles_cause_and_facts(self):
        game = _game(year=210)
        entry = world_events.record(game, "flood", actors=["rome"], tiles=["t1"], cause="rain", died=3.0)
        self.assertEqual((entry["year"], entry["kind"], entry["actors"], entry["tiles"], entry["cause"], entry["facts"]),
                         (210, "flood", ["rome"], ["t1"], "rain", {"died": 3.0}))

    def test_records_older_than_the_kept_years_are_dropped(self):
        game = _game()
        world_events.record(game, "flood", actors=["x"])
        game.state.scenario.year += world_hazard_data.years_kept() + 1
        world_events.record(game, "flood", actors=["y"])
        self.assertEqual([row["actors"] for row in game.state.economy.world_events], [["y"]])

    def test_rows_filter_by_kind_year_and_actor_oldest_first(self):
        game = _game()
        world_events.record(game, "flood", actors=["a"])
        game.state.scenario.year = 105
        world_events.record(game, "famine", actors=["b"])
        world_events.record(game, "flood", actors=["b"])
        self.assertEqual(len(world_events.rows(game)), 3)
        self.assertEqual(len(world_events.rows(game, "flood")), 2)
        self.assertEqual(len(world_events.rows(game, since_year=105)), 2)
        self.assertEqual([row["kind"] for row in world_events.rows(game, actor="b")], ["famine", "flood"])


class DrawTests(unittest.TestCase):

    def test_a_countrys_draw_is_the_same_on_every_call_and_differs_between_countries(self):
        game = _game()
        self.assertEqual(world_hazards.draw(game, "han", "flood", 100), world_hazards.draw(game, "han", "flood", 100))
        self.assertNotEqual(world_hazards.draw(game, "han", "flood", 100), world_hazards.draw(game, "rome", "flood", 100))

    def test_the_draw_differs_between_years_and_kinds(self):
        game = _game()
        self.assertNotEqual(world_hazards.draw(game, "han", "flood", 100), world_hazards.draw(game, "han", "flood", 101))
        self.assertNotEqual(world_hazards.draw(game, "han", "flood", 100), world_hazards.draw(game, "han", "fire", 100))

    def test_the_countries_in_a_game_are_the_home_country_then_its_partners(self):
        self.assertEqual(world_hazards.countries_in_game(_game(partners=("han",), civ_id="rome")), ["rome", "han"])

    def test_a_game_without_events_draws_no_hazards(self):
        game = _game(events=False)
        with mock.patch.object(world_hazards, "hit") as hit:
            world_hazards.world_hazards_phase(game, [])
        hit.assert_not_called()

    def test_a_certain_hazard_hits_every_country_and_a_zero_chance_hits_none(self):
        game = _game(partners=("han",))
        flood = next(entry for entry in world_hazard_data.hazards() if entry["kind"] == "flood")
        with mock.patch.object(world_hazards, "hit") as hit, \
                mock.patch.object(world_hazard_data, "hazards", lambda: [dict(flood, annual_chance=1.0)]):
            world_hazards.world_hazards_phase(game, [])
        self.assertEqual([call.args[1] for call in hit.call_args_list], ["rome", "han"])
        with mock.patch.object(world_hazards, "hit") as hit, \
                mock.patch.object(world_hazard_data, "hazards", lambda: [dict(flood, annual_chance=0.0)]):
            world_hazards.world_hazards_phase(game, [])
        hit.assert_not_called()


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
        game = _game()
        game.debug = True
        game.verify_step_invariants = mock.Mock()
        with mock.patch.object(year_run, "run_phases", lambda target: None):
            year_run.run_year(game)
        game.verify_step_invariants.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
