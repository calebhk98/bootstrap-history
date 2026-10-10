"""Complaints/416 (415): a mine names a deposit its seat has found and its output is bounded by that deposit;
prospecting finds hidden deposits and the finds are kept; a worked-out deposit closes its workings."""
QUICK_TOPIC = True

import json
import os
import types
import unittest

from sim.engine.economy_mining import MiningMixin
from sim.engine.state_holdings import HoldingsState
from sim.geography import api as geography

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _rome():
    with open(os.path.join(ROOT, "data", "civilizations", "rome_100ad.json"), encoding="utf-8") as handle:
        return json.load(handle)


class _Household:
    def __init__(self, holdings):
        self._holdings = holdings
        self.log = []
        self.capital = 1e15

    @property
    def mines(self):
        return self._holdings.mines


class _Market:
    def quote(self, trade, hours=0.0, employer=None, pay_premium=0.0):
        return 1.0


class _Host(MiningMixin):
    """Just enough of Sim to open, commission and draw down mines."""
    price_index = 1.0
    MINE_TRADE = "miner"

    def __init__(self):
        self.world_map = geography.open_map()
        self.civ = _rome()
        self.holdings = HoldingsState()
        self.household = _Household(self.holdings)
        self.state = types.SimpleNamespace(holdings=self.holdings, household=self.household,
                                           scenario=types.SimpleNamespace(year=100))
        self.cfg = {"start_year": 100}
        self.labour = types.SimpleNamespace(labour_market=_Market())
        self.paid = []

    def _normalize_material_name(self, mat):
        return mat

    def _mine_capex(self, mat):
        return 10.0

    def _mine_opex(self, mat):
        return 1.0

    def mining_cost_scale(self, mat):
        return 1.0

    def mine_land_ceiling(self, mat):
        return 1e12

    def spending_power(self, kind):
        return 1e18

    def pay_edge(self, edge, money, text):
        self.paid.append(money)

    def _farm_year_weather_seed(self, year, region=None):
        return 17

    def _ready(self):
        self.state.scenario.year += 10
        self.commission_mines()


class MineNamesADepositTests(unittest.TestCase):

    def setUp(self):
        self.host = _Host()

    def test_a_mine_is_bounded_by_the_deposits_found_and_each_tranche_names_one(self):
        rooms = {row["id"]: row["room_tonnes_per_year"] for row in self.host.found_deposits("iron")}
        self.assertTrue(rooms)
        opened = self.host.open_mine("iron", 1e12)
        self.assertAlmostEqual(opened, sum(rooms.values()))
        for tranche in self.host.holdings.mine_tranches:
            self.assertIn(tranche[5], rooms)
            self.assertLessEqual(tranche[1], rooms[tranche[5]] + 1e-9)

    def test_a_named_deposit_is_the_only_one_worked(self):
        row = self.host.found_deposits("iron")[0]
        opened = self.host.open_mine("iron", 1e12, deposit=row["id"])
        self.assertAlmostEqual(opened, row["room_tonnes_per_year"])
        self.assertEqual({tranche[5] for tranche in self.host.holdings.mine_tranches}, {row["id"]})

    def test_a_second_mine_on_a_deposit_gets_only_the_room_the_first_left(self):
        row = self.host.found_deposits("iron")[0]
        self.host.open_mine("iron", row["room_tonnes_per_year"] / 2.0, deposit=row["id"])
        again = self.host.open_mine("iron", 1e12, deposit=row["id"])
        self.assertAlmostEqual(again, row["room_tonnes_per_year"] / 2.0)
        self.assertEqual(self.host.open_mine("iron", 1.0, deposit=row["id"]), 0.0)

    def test_nothing_opens_where_no_deposit_is_known_and_the_refusal_says_to_prospect(self):
        self.assertEqual(self.host.found_deposits("coal"), [])
        self.assertEqual(self.host.open_mine("coal", 100.0), 0.0)
        self.assertIn("prospect", self.host.mine_refusal)

    def test_a_deposit_not_yet_first_worked_cannot_be_named(self):
        ids = {row["id"] for row in self.host.found_deposits("copper")}
        self.assertNotIn("neves_corvo_copper", ids)

    def test_a_deposit_worked_out_before_the_game_has_no_room(self):
        laurion = next(row for row in self.host.found_deposits("silver") if row["id"] == "laurion_silver")
        self.assertEqual(laurion["remaining_tonnes"], 0.0)
        self.assertEqual(laurion["room_tonnes_per_year"], 0.0)
        self.assertEqual(self.host.open_mine("silver", 1e12, deposit="laurion_silver"), 0.0)

    def test_a_deposit_of_unknown_size_is_not_listed(self):
        self.assertTrue(all(row["size_tonnes"] > 0.0 for row in self.host.found_deposits("lead")))

    def test_a_material_no_deposit_data_describes_is_bounded_by_the_ceiling_alone(self):
        self.assertEqual(self.host.found_deposits("aluminium_kg"), [])
        self.assertEqual(self.host.open_mine("aluminium_kg", 5.0), 5.0)
        self.assertIsNone(self.host.holdings.mine_tranches[0][5])


class DrawDownTests(unittest.TestCase):

    def setUp(self):
        self.host = _Host()
        row = self.host.found_deposits("iron")[0]
        self.row = row
        self.host.open_mine("iron", row["room_tonnes_per_year"] / 2.0, deposit=row["id"])
        self.host._ready()

    def test_a_commissioned_working_names_its_deposit_and_each_year_draws_its_yield(self):
        working = self.host.holdings.mines[0]
        self.assertEqual(working["deposit"], self.row["id"])
        before = self.host.holdings.deposit_drawn[self.row["id"]]
        expected = self.host.mine_yield_t_for(working)
        self.host.commission_mines()
        self.assertAlmostEqual(self.host.holdings.deposit_drawn[self.row["id"]] - before, expected)

    def test_a_working_yields_no_more_than_its_deposit_has_left(self):
        working = self.host.holdings.mines[0]
        self.host.holdings.deposit_drawn[self.row["id"]] = self.row["size_tonnes"] - 5.0
        self.assertLessEqual(self.host.mine_yield_t_for(working), 5.0 + 1e-9)

    def test_a_worked_out_deposit_closes_its_workings(self):
        self.host.holdings.deposit_drawn[self.row["id"]] = self.row["size_tonnes"]
        self.host.commission_mines()
        self.assertEqual(self.host.holdings.mines, [])
        self.assertTrue(any("worked out" in text for _year, text in self.host.household.log))

    def test_firms_and_the_seat_draw_from_the_same_deposit(self):
        before = self.host.found_deposits("iron")[0]["remaining_tonnes"]
        self.host.draw_deposit(self.row["id"], 100.0)
        after = next(found for found in self.host.found_deposits("iron") if found["id"] == self.row["id"])
        self.assertAlmostEqual(before - after["remaining_tonnes"], 100.0)


class ProspectingTests(unittest.TestCase):

    def setUp(self):
        self.host = _Host()
        tiles = geography.tiles_held(self.host.civ, self.host.world_map)
        self.tile = max(tiles, key=lambda tile: geography.endowment(tile, "coal", self.host.world_map)["undiscovered_expected"])

    def test_prospecting_finds_deposits_that_are_kept_and_can_then_be_named(self):
        ok, message = self.host.prospect_deposits(self.tile, "coal", 1e9)
        self.assertTrue(ok, message)
        found = self.host.holdings.deposits_found
        self.assertTrue(found, message)
        rows = self.host.found_deposits("coal")
        self.assertTrue(rows)
        self.assertGreater(self.host.open_mine("coal", 1e12), 0.0)

    def test_more_effort_finds_a_superset_and_repeats_add_nothing_twice(self):
        self.host.prospect_deposits(self.tile, "coal", 1e5)
        small = {deposit["id"] for deposit in self.host.holdings.deposits_found}
        self.host.prospect_deposits(self.tile, "coal", 1e9)
        large = {deposit["id"] for deposit in self.host.holdings.deposits_found}
        self.assertTrue(small <= large)
        self.assertEqual(len(self.host.holdings.deposits_found), len(large))

    def test_prospecting_costs_money_and_needs_a_held_tile(self):
        self.host.prospect_deposits(self.tile, "coal", 50.0)
        self.assertGreater(sum(self.host.paid), 0.0)
        self.assertFalse(self.host.prospect_deposits("no_such_tile", "coal", 50.0)[0])
        self.assertFalse(self.host.prospect_deposits(self.tile, "aluminium_kg", 50.0)[0])

    def test_the_automatic_mine_prospects_when_no_deposit_has_room_and_not_otherwise(self):
        self.assertTrue(self.host.auto_prospect("coal"))
        self.assertTrue(self.host.found_deposits("coal"))
        paid = len(self.host.paid)
        self.assertFalse(self.host.auto_prospect("coal"))
        self.assertEqual(len(self.host.paid), paid)
        self.assertFalse(self.host.auto_prospect("aluminium_kg"))

    def test_the_finds_survive_save_and_load(self):
        from sim.engine.state import deserialize_state, serialize_state
        self.host.prospect_deposits(self.tile, "coal", 1e9)
        self.host.draw_deposit("anywhere", 3.0)
        copy = deserialize_state(serialize_state(self.host.holdings), HoldingsState)
        self.assertEqual(copy.deposits_found, self.host.holdings.deposits_found)
        self.assertEqual(copy.deposit_drawn, self.host.holdings.deposit_drawn)
        self.assertEqual(copy.prospected_person_days, self.host.holdings.prospected_person_days)


if __name__ == "__main__":
    unittest.main()
