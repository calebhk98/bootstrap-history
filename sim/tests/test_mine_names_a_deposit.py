"""Complaints/416 (415): a mine names a deposit its seat has found and its output is bounded by that deposit;
prospecting finds hidden deposits and the finds are kept; a worked-out deposit closes its workings."""
QUICK_TOPIC = True
UNDER_TEST = {"open_mine", "commission_mines"}

import types
import unittest

from sim.geography import api as geography
from sim.ledger.api import PayEdge
from sim.refusal import Refusal
from sim.reporting.api import RecordEvent
from sim.resources.api import DrawDeposit, OpenMine, Prospect
from sim.resources.state import ResourcesSeat
from sim.tests import module_harness, resources_stand_in


class _Host:
    """The resources module with the figures a mine's price and ceiling would read written out (capex ten, opex one, no
    ceiling), under the names the tests of mines use: `holdings` is the seat's state, `paid` what it paid."""

    def __init__(self, budget=1e18):
        self.year = 100
        self.module = resources_stand_in.build(budget=budget, views={"year": lambda: self.year})
        module = self.module
        module.mine_capex = lambda material: 10.0
        module.mine_opex = lambda material: 1.0
        module.mine_land_ceiling = lambda material: 1e12
        module.mine_trade = lambda: "miner"
        self.holdings = module.seat
        self.world_map, self.civ = geography.open_map(), resources_stand_in.rome()
        self.mine_refusal = None

    @property
    def paid(self):
        return resources_stand_in.paid(self.module)

    @property
    def household(self):
        return types.SimpleNamespace(log=[(self.year, command.text) for command in module_harness.sent(self.module)
                                          if isinstance(command, RecordEvent)])

    def open_mine(self, material, tonnes, partial=True, order="", deposit=None):
        answer = self.module.open_mine(OpenMine(material, tonnes, partial, order, deposit))
        self.mine_refusal = answer if isinstance(answer, Refusal) and answer.cause == "no_deposit_found" else None
        return 0.0 if isinstance(answer, Refusal) else answer

    def prospect_deposits(self, tile, material, person_days):
        answer = self.module.prospect(Prospect(tile, material, person_days))
        return (False, str(answer)) if isinstance(answer, Refusal) else (True, answer["message"])

    def draw_deposit(self, deposit_id, tonnes):
        return self.module.draw_deposit(DrawDeposit(deposit_id, tonnes))

    def deposit_catalogue(self):
        return self.module.needs.deposit_catalogue()

    def send(self, command):   # the timber commands of the port's hooks: no recipe here fells wood
        return None

    def view(self, name):
        return lambda: {}

    def __getattr__(self, name):
        return {"mine_yield_t_for": "yield_of"}.get(name) and getattr(self.module, {"mine_yield_t_for": "yield_of"}[name]) \
            or getattr(self.module, name)


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
        half = row["room_tonnes_per_year"] / 2.0
        self.host.holdings.mine_tranches = [["iron", half, 110, 0.0, "", row["id"]]]
        self.host.holdings.mine_pending = {"iron": half}
        again = self.host.open_mine("iron", 1e12, deposit=row["id"])
        self.assertAlmostEqual(again, half)

    def test_a_deposit_whose_room_is_all_taken_opens_nothing(self):
        row = self.host.found_deposits("iron")[0]
        self.host.holdings.mine_tranches = [["iron", row["room_tonnes_per_year"], 110, 0.0, "", row["id"]]]
        self.host.holdings.mine_pending = {"iron": row["room_tonnes_per_year"]}
        self.assertEqual(self.host.open_mine("iron", 1.0, deposit=row["id"]), 0.0)

    def test_nothing_opens_where_no_deposit_is_known_and_the_refusal_says_to_prospect(self):
        self.assertEqual(self.host.found_deposits("coal"), [])
        self.assertEqual(self.host.open_mine("coal", 100.0), 0.0)
        self.assertIn("prospect", self.host.mine_refusal)

    def test_a_deposit_not_yet_first_worked_cannot_be_named(self):
        ids = {row["id"] for row in self.host.found_deposits("copper")}
        self.assertNotIn("neves_corvo_copper", ids)

    def test_a_deposit_worked_out_before_the_game_has_no_room(self):
        # Cyprus copper: 3000 years at the rate the output model gives it, against 200 kt held (the data close it)
        cyprus = next(row for row in self.host.found_deposits("copper") if row["id"] == "cyprus_copper")
        self.assertAlmostEqual(cyprus["remaining_tonnes"], 0.0, delta=1e-6)
        self.assertAlmostEqual(cyprus["room_tonnes_per_year"], 0.0, delta=1e-6)
        self.assertAlmostEqual(self.host.open_mine("copper", 1e12, deposit="cyprus_copper"), 0.0, delta=1e-6)

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
        self.host.holdings.mines = [{"material": "iron", "capacity": row["room_tonnes_per_year"] / 2.0, "opened_year": 100,
                                     "capex_paid": 0.0, "order": "", "intensity_yrs": 0.0, "deposit": row["id"]}]
        self.host.year = 110

    def test_each_year_a_working_draws_its_yield_from_its_deposit(self):
        working = self.host.holdings.mines[0]
        before = self.host.holdings.deposit_drawn.get(self.row["id"], 0.0)
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

    def test_prospecting_finds_deposits_that_are_kept(self):
        ok, message = self.host.prospect_deposits(self.tile, "coal", 1e9)
        self.assertTrue(ok, message)
        self.assertTrue(self.host.holdings.deposits_found, message)

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
        copy = deserialize_state(serialize_state(self.host.holdings), ResourcesSeat)
        self.assertEqual(copy.deposits_found, self.host.holdings.deposits_found)
        self.assertEqual(copy.deposit_drawn, self.host.holdings.deposit_drawn)
        self.assertEqual(copy.prospected_person_days, self.host.holdings.prospected_person_days)


if __name__ == "__main__":
    unittest.main()
