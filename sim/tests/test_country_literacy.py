"""Complaint 604: the people who can read govern hiring and research together."""
import unittest
from unittest.mock import patch

from sim.agents.api import ActorRecord, CountryProfile, seed_strata
from sim.engine.agents_port import SimWorld
from sim.engine.agents_port_cast import seed_opening_cast
from sim.tests.harness import unopened_sim


class CountryLiteracyTests(unittest.TestCase):
    def test_strata_literacy_changes_hiring_and_research_output(self):
        game = unopened_sim()
        seed_opening_cast(game)
        seed_strata(game.actors, None)
        home = [actor for actor in game.actors.of_kind("stratum")
                if actor.record.country is None]
        self.assertTrue(home)
        for actor in home:
            actor.record.literacy = 0.1
        hiring_before = game.labour.literate_capacity("scholar")
        with patch.object(game.labour, "market_supply", return_value=100.0):
            research_before = game.labour.hours_you_can_call_on("scholar")
            for actor in home:
                actor.record.literacy = 0.7
            research_after = game.labour.hours_you_can_call_on("scholar")
        self.assertGreater(game.labour.literate_capacity("scholar"), hiring_before)
        self.assertGreater(research_after, research_before)

    def test_paid_research_hours_make_more_project_progress(self):
        game = unopened_sim()
        plan = {"scholar": {"left": 1000.0, "nominal": 1.0, "ceiling": 1000.0}}
        with patch.object(game, "trade_draw_plan", return_value=plan), \
                patch.object(game.labour, "market_supply", return_value=100.0):
            game.set_literacy("literacy_elite", 0.1)
            lower = {"lab_left": {"scholar": 1000.0}, "yrs": 0}
            game.lab_year_draw("corpus_written", lower, 1.0, 1e9)
            game.state.projects.trade_hours_used.clear()
            game.set_literacy("literacy_elite", 0.7)
            higher = {"lab_left": {"scholar": 1000.0}, "yrs": 0}
            game.lab_year_draw("corpus_written", higher, 1.0, 1e9)
        self.assertLess(higher["lab_left"]["scholar"], lower["lab_left"]["scholar"])

    def test_foreign_player_research_reads_its_own_country(self):
        game = unopened_sim()
        game.actors.state.countries["other"] = CountryProfile(
            country="other", population=100, strata=[
                {"name": "readers", "share": 1.0, "literacy": 0.1}])
        seed_strata(game.actors, None)
        player = game.actors.add("player:other", ActorRecord(kind="player", country="other"))
        world = game.actors.world_for(player, SimWorld(game))
        home_before = game.literacy("literacy_elite")

        def progress():
            player.works["research"] = {"chain": ["research"], "hours": {}, "money": 0.0,
                                        "labour_cost": 0.0, "years": 10, "progress": 0.0,
                                        "stalled": 0.0}
            player.work_on_research(world)
            return player.works["research"]["progress"]

        before = progress()
        game.set_literacy("literacy_elite", 0.7, country="other")
        after = progress()
        self.assertGreater(after, before)
        self.assertAlmostEqual(game.literacy("literacy_elite"), home_before)
        self.assertAlmostEqual(world.literacy("literacy_elite"), 0.7)

    def test_technology_changes_the_source_records_and_not_civilisation_data(self):
        game = unopened_sim()
        before = game.literacy("literacy_general")
        game.apply_tech_effects("printing_press")
        self.assertGreater(game.literacy("literacy_general"), before)
        self.assertNotIn("literacy_general", game.civ)
        self.assertNotIn("literacy_elite", game.civ)
