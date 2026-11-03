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
        ledger.note_plant_purchases(postings, "ironwork", {"mill": {"ironwork"}})
        self.assertEqual(ledger.money_out["mill"], 50.0)
        self.assertEqual(ledger.plant_spend["mill"], 30.0)
        self.assertEqual(ledger.running_costs("mill"), 20.0)

    def test_plant_spend_is_what_was_paid_whatever_the_market_mean(self):
        ledger = YearLedger()
        postings = [Transfer("mill", "cheap", "coin", 10.0, "sale of ironwork"),
                    Transfer("mill", "dear", "coin", 40.0, "sale of ironwork"),
                    GoodsMove("cheap", "mill", "ironwork", "t1", 5.0, "sale of ironwork"),
                    GoodsMove("dear", "mill", "ironwork", "t1", 5.0, "sale of ironwork")]
        ledger.note_plant_purchases(postings, "ironwork", {"mill": {"ironwork"}})
        self.assertEqual(ledger.plant_spend["mill"], 50.0)

    def test_inputs_that_are_not_plant_stay_in_the_costs(self):
        ledger = YearLedger()
        postings = [Transfer("mill", "farmer", "coin", 20.0, "sale of grain"),
                    GoodsMove("farmer", "mill", "grain", "t1", 2.0, "sale of grain")]
        ledger.note_postings(postings, "sales")
        ledger.note_plant_purchases(postings, "grain", {"mill": {"ironwork"}})
        self.assertEqual(ledger.running_costs("mill"), 20.0)

    def test_a_seller_paying_to_dump_a_negative_priced_good_is_not_plant_spend(self):
        ledger = YearLedger()
        postings = [Transfer("smelter", "mill", "coin", 8.0, "sale of ironwork"),
                    GoodsMove("smelter", "mill", "ironwork", "t1", 4.0, "sale of ironwork")]
        ledger.note_plant_purchases(postings, "ironwork", {"smelter": {"ironwork"}})
        self.assertEqual(ledger.plant_spend, {})


if __name__ == "__main__":
    unittest.main()
