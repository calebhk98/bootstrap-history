"""Speed: what the year does outside the economy's step. Each rule is called on its own inputs beside the plain code it
replaced; no game is built."""

QUICK_TOPIC = True

import random
import types
import unittest
from unittest import mock

from sim.economy import quiet_year
from sim.markets import port_cropland, port_sites, unit_mass
from sim.economy.api import goods_specs, recipe_tile_key


def old_followed_factors(factors, changed):
    """The scan `follow_farm_sites` ran before: every key tested against every changed tile's suffix."""
    ends = {recipe_tile_key("", tile): fertility for tile, fertility in changed.items()}
    return {key: next((fertility for suffix, fertility in ends.items() if key.endswith(suffix)), factor)
            for key, factor in factors.items()}


class FollowedFactors(unittest.TestCase):
    def test_equals_the_suffix_scan(self):
        rng = random.Random(3)
        tiles = ["t%d" % number for number in range(12)] + ["ab", "b"]
        factors = {recipe_tile_key("recipe%d" % rng.randrange(6), rng.choice(tiles)): rng.random() for _ in range(80)}
        changed = {tile: rng.random() for tile in rng.sample(tiles, 5)}
        self.assertEqual(port_cropland.followed_factors(factors, changed), old_followed_factors(factors, changed))

    def test_nothing_changed_keeps_every_factor(self):
        factors = {recipe_tile_key("wheat", "a"): 0.5}
        self.assertEqual(port_cropland.followed_factors(factors, {}), factors)


class QuietYear(unittest.TestCase):
    def economy(self, years_stepped):
        return types.SimpleNamespace(years_stepped=years_stepped, setup=object())

    def test_computes_every_time_until_settled(self):
        economy, calls = self.economy(1), []
        quiet_year.kept(economy, "figure", lambda: calls.append(1) or 7)
        quiet_year.kept(economy, "figure", lambda: calls.append(1) or 7)
        self.assertEqual(len(calls), 2)

    def test_keeps_one_answer_per_key_while_settled(self):
        economy, calls = self.economy(1), []
        quiet_year.settle(economy)
        answers = [quiet_year.kept(economy, key, lambda: calls.append(1) or len(calls)) for key in ("a", "b", "a")]
        self.assertEqual(answers, [1, 2, 1])

    def test_a_step_drops_the_answers(self):
        economy, calls = self.economy(1), []
        quiet_year.settle(economy)
        quiet_year.kept(economy, "a", lambda: calls.append(1))
        economy.years_stepped += 1
        quiet_year.kept(economy, "a", lambda: calls.append(1))
        self.assertEqual(len(calls), 2)

    def test_a_new_setup_drops_the_answers(self):
        economy, calls = self.economy(1), []
        quiet_year.settle(economy)
        quiet_year.kept(economy, "a", lambda: calls.append(1))
        economy.setup = object()
        quiet_year.kept(economy, "a", lambda: calls.append(1))
        self.assertEqual(len(calls), 2)

    def test_a_memory_write_drops_the_answers(self):
        from sim.economy.market_memory import note_written
        economy, calls = self.economy(1), []
        quiet_year.settle(economy)
        quiet_year.kept(economy, "a", lambda: calls.append(1))
        note_written()
        quiet_year.kept(economy, "a", lambda: calls.append(1))
        self.assertEqual(len(calls), 2)


class UnitMass(unittest.TestCase):
    def test_equals_the_goods_spec_mass(self):
        for good in ("wheat_kg", "iron_ore", "silver_kg", "no_such_good_at_all"):
            expected = goods_specs({good: ""}, {})[good].unit_mass_kg
            self.assertEqual(unit_mass.unit_mass_kg(good), expected)
            self.assertEqual(unit_mass.unit_mass_kg(good), expected)


class FakeDeposits:
    """A store of deposit rows that `draw_deposit` lowers, as the seat's ledger does; counts the reads."""

    def __init__(self, rows):
        self.rows = rows
        self.reads = 0

    def found_deposits(self, resource_id):
        self.reads += 1
        return [dict(row) for row in self.rows if row["resource"] == resource_id]

    def partner_deposits(self, resource_id, tile_ids):
        return []

    def draw_deposit(self, deposit_id, tonnes):
        for row in self.rows:
            if row["id"] == deposit_id:
                row["remaining_tonnes"] -= tonnes


def old_deplete(sim, extraction, recipes):
    """`port_sites.deplete` before the rows were read once per resource."""
    worked_tiles = {tile for _recipe_id, tile in extraction}
    for (recipe_id, tile), runs in sorted(extraction.items()):
        if recipe_id not in recipes or runs <= 0.0:
            continue
        resource_id, ore_kg_per_run = recipes[recipe_id]
        ore_tonnes = runs * ore_kg_per_run / 1000.0
        rows = sim.foreign.found_deposits(resource_id) + sim.foreign.partner_deposits(resource_id, worked_tiles)
        for row in sorted((row for row in rows if row["tile_id"] == tile), key=lambda row: (-row["remaining_tonnes"], row["id"])):
            take = min(ore_tonnes / 1.0, row["remaining_tonnes"])
            if take > 0.0:
                sim.foreign.draw_deposit(row["id"], take)
                ore_tonnes -= take
            if ore_tonnes <= 1e-12:
                break


class Deplete(unittest.TestCase):
    def build(self, seed):
        rng = random.Random(seed)
        rows = [{"id": "d%d" % number, "resource": rng.choice(("iron", "tin")), "tile_id": rng.choice(("a", "b", "c")),
                 "remaining_tonnes": rng.uniform(1.0, 50.0)} for number in range(14)]
        recipes = {"mine_%d" % number: (rng.choice(("iron", "tin")), 1000.0) for number in range(5)}
        extraction = {(recipe, tile): rng.uniform(0.0, 30.0) for recipe in recipes for tile in ("a", "b", "c") if rng.random() < 0.7}
        return rows, recipes, extraction

    def run_new(self, rows, recipes, extraction):
        sim = types.SimpleNamespace(foreign=FakeDeposits(rows))
        with mock.patch.object(port_sites, "_ore_recipes", return_value=recipes), \
                mock.patch.object(port_sites.port_timber, "fell"), mock.patch.object(port_sites.port_timber, "regrow"), \
                mock.patch.object(port_sites, "ore_tonnes_per_tonne", return_value=1.0):
            port_sites.deplete(sim, extraction, {})
        return sim

    def test_draws_what_the_per_item_reading_drew(self):
        for seed in range(20):
            rows, recipes, extraction = self.build(seed)
            old_rows = [dict(row) for row in rows]
            old_deplete(types.SimpleNamespace(foreign=FakeDeposits(old_rows)), extraction, recipes)
            self.run_new(rows, recipes, extraction)
            self.assertEqual([row["remaining_tonnes"] for row in rows], [row["remaining_tonnes"] for row in old_rows], seed)

    def test_reads_each_resource_once_unless_a_tile_is_met_again(self):
        rows, recipes, extraction = self.build(1)
        sim = self.run_new(rows, recipes, extraction)
        items = sum(1 for (recipe, _tile), runs in extraction.items() if runs > 0.0)
        self.assertLess(sim.foreign.reads, items)


if __name__ == "__main__":
    unittest.main()
