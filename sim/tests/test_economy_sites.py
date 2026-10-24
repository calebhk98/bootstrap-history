"""Site limits: what a site imposes on a recipe, handed in from outside; the economy models no deposit."""

QUICK_TOPIC = True

import unittest
from dataclasses import replace
from types import SimpleNamespace

from sim.economy import location, opening, sites
from sim.economy.opening import open_economy
from sim.economy.producers import Producer
from sim.economy.recipes import recipe_from_entry
from sim.economy.types import MarketArea, Recipe, SiteLimit
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


class OpeningSitesTests(unittest.TestCase):
    def _setup(self, limits):
        recipes = fixture.recipes()
        recipes[fixture.MINE] = replace(recipes[fixture.MINE], site_bound=True)
        return fixture.small_setup(recipes=recipes, site_limits=limits)

    def test_without_limits_extraction_stays_where_it_was(self):
        record, _areas, _carriage = open_economy(self._setup(()))
        mines = [p for p in record.producers.values() if p.recipe_id == fixture.MINE]
        self.assertEqual([p.tile for p in mines], [fixture.TOWN])
        self.assertGreater(mines[0].capacity_runs, 0.0)

    def test_the_opening_counts_the_limit_not_the_anchor(self):
        record, _areas, _carriage = open_economy(self._setup((SiteLimit(fixture.MINE, fixture.HILLS, 5000.0),)))
        self.assertEqual({p.tile for p in record.producers.values() if p.recipe_id == fixture.MINE},
                         {fixture.HILLS})


class OpeningSplitTests(unittest.TestCase):
    def _area(self, tiles):
        return MarketArea(area_id="a", good_id="ore", tiles=tuple(tiles), anchor_tile=tiles[0])

    def test_an_area_with_sites_is_served_by_its_own_sites(self):
        limits = (SiteLimit("dig", "town", 1e6), SiteLimit("dig", "hills", 1e9))
        setup = fixture.small_setup(recipes={"dig": _bound()}, site_limits=limits)
        split = location.opening_split(setup, _bound(), self._area(["town"]), 10.0)
        self.assertEqual(split, {"town": 10.0})

    def test_an_area_without_sites_draws_on_every_site_by_capacity(self):
        limits = (SiteLimit("dig", "farms", 1e6), SiteLimit("dig", "hills", 3e6))
        setup = fixture.small_setup(recipes={"dig": _bound()}, site_limits=limits)
        split = location.opening_split(setup, _bound(), self._area(["town"]), 8.0)
        self.assertAlmostEqual(split["farms"], 2.0)
        self.assertAlmostEqual(split["hills"], 6.0)

    def test_areas_without_sites_pool_their_runs_and_the_others_keep_theirs(self):
        limits = {"town": SiteLimit("dig", "town", 1.0)}
        shares = [(self._area(["town"]), 3.0), (self._area(["farms"]), 2.0), (self._area(["hills"]), 4.0)]
        pooled = opening._sited_shares(shares, limits)
        self.assertEqual([(area.tiles, runs) for area, runs in pooled], [(("town",), 3.0), (("farms",), 6.0)])


class OrderTests(unittest.TestCase):
    def test_producers_are_summed_in_id_order_whatever_order_they_were_stored_in(self):
        # a reloaded record holds its producers in saved (sorted) order, the live one in the order they arose
        producers = {"b": Producer("b", "owner", "farm", "town", 1.0), "a": Producer("a", "owner", "farm", "town", 2.0)}
        self.assertEqual([each.agent_id for each in sites.in_id_order(producers)], ["a", "b"])


if __name__ == "__main__":
    unittest.main()
