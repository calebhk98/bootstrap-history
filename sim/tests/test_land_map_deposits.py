"""The land module's views of the deposits in the ground (sim/land/map_deposits.py): the catalogue of what is mined, the deposits a
party can name, what was worked before the game began, the most a deposit yields and what prospecting and the district's
expectation say. Called on a land module over the base map and Rome's tiles; no game."""
QUICK_TOPIC = True

import unittest

from sim.tests import land_host, resources_stand_in

ROME = resources_stand_in.rome()


def land():
    return land_host.build(ROME)


class DepositCatalogueTests(unittest.TestCase):
    def test_the_metals_are_the_resources_that_yield_ore_goods(self):
        catalogue = land().deposit_catalogue()
        self.assertEqual(catalogue["metals"], tuple(catalogue["ore_goods"]))
        self.assertIn("iron", catalogue["metals"])
        self.assertEqual(catalogue["ore_goods"]["iron"]["iron_ore_kg"], ("pig_iron_kg", "iron_bloom_kg"))

    def test_each_resource_gives_its_mechanism(self):
        mechanisms = land().deposit_catalogue()["mechanisms"]
        self.assertEqual((mechanisms["coal"], mechanisms["cattle"]), ("mineral_deposit", "herd_animal"))

    def test_a_mine_of_gold_supplies_gold_and_the_miners_trade_is_the_maps(self):
        catalogue = land().deposit_catalogue()
        self.assertEqual(catalogue["demand_goods"]["gold"], ("gold_kg",))
        self.assertEqual(catalogue["mining_trade"], "miner")

    def test_coal_is_priced_from_its_works_and_mercury_is_not(self):
        works = land().deposit_catalogue()["works_priced_materials"]
        self.assertIn("coal", works)
        self.assertNotIn("mercury", works)

    def test_the_catalogue_is_kept(self):
        module = land()
        self.assertIs(module.deposit_catalogue(), module.deposit_catalogue())


class DepositsListedTests(unittest.TestCase):
    def test_the_iron_deposits_on_romes_tiles_include_the_anatolian_one(self):
        module = land()
        rows = module.deposits_listed(module.tiles_listed_by(ROME), "iron", 100)
        anatolian = [row for row in rows if row["id"] == "anatolian_iron"]
        self.assertEqual([(row["tile_id"], row["grade_kg_per_tonne"]) for row in anatolian], [("turkey_07", 350.0)])

    def test_a_deposit_found_by_prospecting_is_listed_with_the_catalogues(self):
        module = land()
        found = module.prospect_finds("algeria_01", "iron", 1e12, "seed")
        rows = module.deposits_listed(module.tiles_listed_by(ROME), "iron", 100, found)
        self.assertTrue({row["id"] for row in found} < {row["id"] for row in rows})


class DepositWorkingRateTests(unittest.TestCase):
    def test_the_most_a_deposit_yields_a_year_grows_with_its_size(self):
        module = land()
        self.assertEqual(module.deposit_working_rate(1000.0), 4.0)
        self.assertEqual(module.deposit_working_rate(1.0e6), 4000.0)


class WorkedBeforeStartTests(unittest.TestCase):
    def test_what_was_worked_before_the_start_is_counted_by_the_deposits_on_the_tiles(self):
        module = land()
        mined = module.deposits_worked_before(module.tiles_listed_by(ROME), "gold", 100, {})
        self.assertEqual(set(mined), {"workings", "unworked", "deposits_in_tiles", "unit"})

    def test_a_year_later_gives_a_working_more_years_of_work(self):
        module = land()
        tiles = module.tiles_listed_by(ROME)
        early = module.deposits_worked_before(tiles, "gold", 100, {})
        late = module.deposits_worked_before(tiles, "gold", 300, {})
        self.assertGreaterEqual(sum(working["years_worked"] for working in late["workings"]),
                                sum(working["years_worked"] for working in early["workings"]))


class ProspectingTests(unittest.TestCase):
    def test_the_same_seed_and_effort_find_the_same_deposits(self):
        module = land()
        first = module.prospect_finds("algeria_01", "iron", 1e12, "seed")
        self.assertTrue(first)
        self.assertEqual(module.prospect_finds("algeria_01", "iron", 1e12, "seed"), first)
        self.assertTrue(all(row["tile_id"] == "algeria_01" and row["resource"] == "iron" for row in first))

    def test_the_district_is_expected_to_hold_more_than_is_known_of_it(self):
        held = land().tile_endowment("algeria_01", "iron")
        self.assertEqual((held["resource"], held["known"]), ("iron", 0))
        self.assertGreater(held["undiscovered_expected"], 0.0)


if __name__ == "__main__":
    unittest.main()
