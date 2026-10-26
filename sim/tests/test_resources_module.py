"""The resources module's commands on the module with written-out views: mothballing cuts the worst-value material and pays the
saving back, closing names the saving, the timber commands change the felled ledger, and the money phase's note is added."""
QUICK_TOPIC = True
UNDER_TEST = {"mothball_mines", "close_mine", "fell_timber", "regrow_timber", "note_mine_cost_paid"}

import unittest

from sim.geography import api as geography
from sim.geography import forest_timber
from sim.ledger.api import ReceiveFromEdge
from sim.refusal import Refusal
from sim.resources.api import CloseMine, FellTimber, MothballMines, NoteMineCostPaid, RegrowTimber
from sim.resources.state import ResourcesSeat, ResourcesWorld
from sim.tests import module_harness, resources_stand_in


def working(material, capacity):
    return {"material": material, "capacity": capacity, "opened_year": 1, "capex_paid": 0.0, "intensity_yrs": 0.0}


def miner(balance, mines):
    def refund(command):
        balance[0] += command.amount
    module = resources_stand_in.build(seat=ResourcesSeat(mines=mines), views={"acting_balance": lambda: balance[0]},
                                      answers={ReceiveFromEdge: refund})
    module.mine_opex = lambda material: {"tin": 3.0, "coal": 1.0}[material]
    module.mine_trade = lambda: "miner"
    return module


class Mothballing(unittest.TestCase):
    def test_nothing_is_cut_while_the_balance_is_not_negative(self):
        module = miner([0.0], [working("tin", 10.0)])
        module.mothball_mines(MothballMines())
        self.assertEqual(module.seat.mines[0]["capacity"], 10.0)

    def test_the_worst_value_material_is_halved_and_the_running_cost_it_saves_is_paid_back(self):
        module = miner([-5.0], [working("coal", 10.0), working("tin", 10.0)])
        module.mothball_mines(MothballMines())
        by_material = {row["material"]: row["capacity"] for row in module.seat.mines}
        self.assertEqual(by_material, {"coal": 10.0, "tin": 5.0})
        (refund,) = [command for command in module_harness.sent(module) if isinstance(command, ReceiveFromEdge)]
        self.assertEqual(refund.amount, 5.0 * 3.0 * 1.0)

    def test_a_working_cut_below_one_tonne_a_year_is_gone(self):
        module = miner([-5.0], [working("tin", 1.5)])
        module.mothball_mines(MothballMines())
        self.assertEqual(module.seat.mines, [])


class Closing(unittest.TestCase):
    def test_closing_names_the_saving_and_drops_the_workings_and_the_shafts_being_sunk(self):
        module = miner([0.0], [working("tin", 10.0), working("coal", 4.0)])
        module.seat.mine_tranches = [["tin", 2.0, 110, 0.0, "", None], ["coal", 1.0, 110, 0.0, "", None]]
        answer = module.close_mine(CloseMine("tin"))
        self.assertEqual(answer, {"material": "tin", "saved_per_year": 30.0})
        self.assertEqual(([row["material"] for row in module.seat.mines], [row[0] for row in module.seat.mine_tranches]),
                         (["coal"], ["coal"]))

    def test_closing_a_material_nothing_is_worked_of_is_refused_with_its_cause(self):
        answer = miner([0.0], []).close_mine(CloseMine("tin"))
        self.assertTrue(isinstance(answer, Refusal) and answer.cause == "no_workings")


class Accounting(unittest.TestCase):
    def test_the_running_cost_paid_adds_up(self):
        module = miner([0.0], [])
        module.note_mine_cost_paid(NoteMineCostPaid(4.0))
        module.note_mine_cost_paid(NoteMineCostPaid(1.5))
        self.assertEqual(module.seat.mine_cost_paid, 5.5)


class Timber(unittest.TestCase):
    def test_felling_takes_each_cut_off_its_tile_and_regrowth_restores_the_stock(self):
        module = resources_stand_in.build(world=ResourcesWorld())
        world_map = module.needs.legacy_world_map()
        tile = max(geography.tile_ids(world_map), key=lambda each: forest_timber.full_tonnes(world_map, each))
        full = forest_timber.full_tonnes(world_map, tile)
        module.fell_timber(FellTimber(((tile, full / 8.0), (tile, full / 8.0))))
        self.assertAlmostEqual(module.timber_felled()[tile], full / 4.0)
        module.regrow_timber(RegrowTimber())
        self.assertLess(module.timber_felled().get(tile, 0.0), full / 4.0)


if __name__ == "__main__":
    unittest.main()
