"""A producer's running costs for the loss test leave out what it paid to build plant this year."""

QUICK_TOPIC = True

import unittest

from sim.economy.types import GoodsMove, Transfer
from sim.economy.year_ledger import YearLedger


class PlantCostTests(unittest.TestCase):
    def test_plant_purchases_are_not_running_costs(self):
        ledger = YearLedger()
        postings = [Transfer("mill", "smith", "coin", 30.0, "sale of ironwork"),
                    GoodsMove("smith", "mill", "ironwork", "t1", 3.0, "sale of ironwork")]
        ledger.note_postings(postings, "sales")
        ledger.note_postings([Transfer("mill", "farmer", "coin", 20.0, "sale of grain")], "sales")
        ledger.note_plant_purchases(postings, 10.0, {"mill": {"ironwork"}})
        self.assertEqual(ledger.money_out["mill"], 50.0)
        self.assertEqual(ledger.plant_spend["mill"], 30.0)
        self.assertEqual(ledger.running_costs("mill"), 20.0)

    def test_inputs_that_are_not_plant_stay_in_the_costs(self):
        ledger = YearLedger()
        postings = [Transfer("mill", "farmer", "coin", 20.0, "sale of grain"),
                    GoodsMove("farmer", "mill", "grain", "t1", 2.0, "sale of grain")]
        ledger.note_postings(postings, "sales")
        ledger.note_plant_purchases(postings, 10.0, {"mill": {"ironwork"}})
        self.assertEqual(ledger.running_costs("mill"), 20.0)


if __name__ == "__main__":
    unittest.main()
