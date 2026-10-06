"""Site limits: what a site imposes on a recipe, handed in from outside; the economy models no deposit."""

QUICK_TOPIC = True

import unittest
from dataclasses import replace
from types import SimpleNamespace

from sim.economy import sites
from sim.economy.opening import open_economy
from sim.economy.producers import Producer
from sim.economy.recipes import recipe_from_entry
from sim.economy.types import Recipe, SiteLimit
from sim.tests import economy_fixture as fixture


def _bound(recipe_id="dig"):
    return Recipe(recipe_id, {"ore": 10.0}, {}, {"miner": 5.0}, site_bound=True)


def _free(recipe_id="farm"):
    return Recipe(recipe_id, {"grain": 10.0}, {}, {"labourer": 5.0})


class RulesTests(unittest.TestCase):
    def test_extracted_from_marks_a_recipe_site_bound(self):
        entry = {"outputs": {"ore": 1.0}, "labour_hours": {"miner": 1.0}, "extracted_from": "copper"}
        self.assertTrue(recipe_from_entry("dig", entry).site_bound)
        self.assertFalse(recipe_from_entry("dig", {"outputs": {"ore": 1.0}}).site_bound)

    def test_a_bound_recipe_with_limits_runs_only_where_declared(self):
        by_recipe = sites.limits_by_recipe((SiteLimit("dig", "hills", 5.0),))
        self.assertEqual(sites.allowed_tiles(_bound(), by_recipe, ("town", "hills")), ("hills",))

    def test_a_bound_recipe_without_limits_runs_anywhere(self):
        self.assertEqual(sites.allowed_tiles(_bound(), {}, ("town", "hills")), ("town", "hills"))
        other = sites.limits_by_recipe((SiteLimit("other", "hills", 1.0),))
        self.assertEqual(sites.allowed_tiles(_bound(), other, ("town", "hills")), ("town", "hills"))

    def test_an_unbound_recipe_ignores_limits(self):
        by_recipe = sites.limits_by_recipe((SiteLimit("farm", "hills", 5.0),))
        self.assertEqual(sites.allowed_tiles(_free(), by_recipe, ("town", "hills")), ("town", "hills"))

    def test_headroom_is_the_limit_less_capacity_already_there(self):
        by_recipe = sites.limits_by_recipe((SiteLimit("dig", "hills", 5.0),))
        self.assertEqual(sites.headroom_runs(_bound(), "hills", by_recipe, 2.0), 3.0)
        self.assertEqual(sites.headroom_runs(_bound(), "town", by_recipe, 0.0), 0.0)
        self.assertEqual(sites.headroom_runs(_bound(), "town", {}, 0.0), float("inf"))


class ApplyTests(unittest.TestCase):
    def _record(self, producers):
        return SimpleNamespace(producers={producer.agent_id: producer for producer in producers}, expansion_runs={})

    def test_capacity_is_capped_and_yield_follows_the_limit(self):
        setup = fixture.small_setup(recipes={"dig": _bound()})
        record = self._record([Producer("p1", "o", "dig", "hills", 9.0), Producer("p2", "o", "dig", "town", 4.0)])
        sites.apply_site_limits(record, setup, (SiteLimit("dig", "hills", 5.0, 0.5),))
        self.assertEqual(record.producers["p1"].capacity_runs, 5.0)
        self.assertEqual(record.producers["p1"].yield_factor, 0.5)
        self.assertEqual(record.producers["p2"].capacity_runs, 0.0)

    def test_empty_limits_keep_the_last_declared(self):
        setup = fixture.small_setup(recipes={"dig": _bound()}, site_limits=(SiteLimit("dig", "hills", 5.0),))
        record = self._record([Producer("p1", "o", "dig", "hills", 9.0)])
        sites.apply_site_limits(record, setup, ())
        self.assertEqual(record.producers["p1"].capacity_runs, 5.0)
        sites.apply_site_limits(record, setup, (SiteLimit("dig", "hills", 2.0),))
        self.assertEqual(record.producers["p1"].capacity_runs, 2.0)
        self.assertEqual(setup.site_limits, (SiteLimit("dig", "hills", 2.0),))

    def test_planned_plant_growth_is_cut_to_the_headroom(self):
        setup = fixture.small_setup(recipes={"dig": _bound()})
        record = self._record([Producer("p1", "o", "dig", "hills", 4.0)])
        record.expansion_runs["p1"] = 3.0
        sites.apply_site_limits(record, setup, (SiteLimit("dig", "hills", 5.0),))
        self.assertEqual(record.expansion_runs["p1"], 1.0)

    def test_extraction_by_tile_reports_runs_worked_by_site_bound_recipes(self):
        setup = fixture.small_setup(recipes={"dig": _bound(), "farm": _free()})
        record = self._record([replace(Producer("p1", "o", "dig", "hills", 9.0), last_runs=4.0),
                               replace(Producer("p2", "o", "dig", "hills", 9.0), last_runs=1.0),
                               replace(Producer("p3", "o", "farm", "town", 9.0), last_runs=7.0),
                               Producer("p4", "o", "dig", "town", 9.0)])
        self.assertEqual(sites.extraction_by_tile(record, setup), {("dig", "hills"): 5.0, ("dig", "town"): 0.0})


class FixtureScenarioTests(unittest.TestCase):
    def _setup(self, limits):
        recipes = fixture.recipes()
        recipes[fixture.MINE] = replace(recipes[fixture.MINE], site_bound=True)
        return fixture.small_setup(recipes=recipes, site_limits=limits)

    def test_a_limit_on_hills_puts_every_ore_producer_there_within_capacity(self):
        limit = SiteLimit(fixture.MINE, fixture.HILLS, 800.0, 0.8)
        economy, _outcomes = fixture.run(self._setup((limit,)), years=6)
        mines = [p for p in economy.record.producers.values() if p.recipe_id == fixture.MINE]
        self.assertTrue(mines)
        self.assertEqual({p.tile for p in mines}, {fixture.HILLS})
        self.assertLessEqual(sum(p.capacity_runs for p in mines), 800.0 + 1e-6)
        self.assertTrue(all(abs(p.yield_factor - 0.8) < 1e-9 for p in mines))
        self.assertEqual(economy.record.book.check_conservation(1e-6).breaches, ())

    def test_without_limits_extraction_stays_where_it_was(self):
        economy, _outcomes = fixture.run(self._setup(()), years=0)
        mines = [p for p in economy.record.producers.values() if p.recipe_id == fixture.MINE]
        self.assertEqual([p.tile for p in mines], [fixture.TOWN])
        self.assertGreater(mines[0].capacity_runs, 0.0)

    def test_the_opening_counts_the_limit_not_the_anchor(self):
        record, _areas, _carriage = open_economy(self._setup((SiteLimit(fixture.MINE, fixture.HILLS, 5000.0),)))
        self.assertEqual({p.tile for p in record.producers.values() if p.recipe_id == fixture.MINE},
                         {fixture.HILLS})


class OrderTests(unittest.TestCase):
    def test_producers_are_summed_in_id_order_whatever_order_they_were_stored_in(self):
        # a reloaded record holds its producers in saved (sorted) order, the live one in the order they arose
        producers = {"b": Producer("b", "owner", "farm", "town", 1.0), "a": Producer("a", "owner", "farm", "town", 2.0)}
        self.assertEqual([each.agent_id for each in sites.in_id_order(producers)], ["a", "b"])


if __name__ == "__main__":
    unittest.main()
