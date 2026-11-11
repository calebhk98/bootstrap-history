"""A bill or a draw for one form of a pool is met from that form's stock, then from the pool's own flow only where that flow
yields that form, then the market: ore never meets a need for bar (Complaint 977, stage 3). `materials.rules`."""
QUICK_TOPIC = True

import unittest

from sim.materials import rules

POOLS = {"iron_bar_kg": ("iron", "mine:iron"), "iron_ore_kg": ("iron", "mine:iron")}
FLOW_KEY = {"iron": "iron_ore_kg"}


def bar_bill(stock, own_per_year, material="iron_bar_kg"):
    """The bill for 1000 kg (one tonne) of `material`, the seat holding `stock` {key: tonnes} and its mine raising ore."""
    return rules.material_bill(
        {material: 1000.0}, 1.0, lambda _material: 0.001, POOLS.__getitem__, lambda key: stock.get(key, 0.0),
        lambda _tag: own_per_year, lambda _material, tonnes, _bought=0.0: (tonnes * 10.0, 10.0), lambda _commodity: 100.0,
        lambda _tag: own_per_year, lambda material: material, FLOW_KEY.__getitem__)["rows"][0]


class BillByFormTests(unittest.TestCase):
    def test_ore_held_does_not_meet_a_need_for_bar(self):
        row = bar_bill({"iron_ore_kg": 5.0}, 0.0)
        self.assertEqual((row["held_from_stock_tonnes"], row["missing_tonnes"]), (0.0, 1.0))

    def test_the_mines_ore_flow_does_not_meet_a_need_for_bar(self):
        row = bar_bill({}, 5.0)
        self.assertEqual((row["held_from_own_output_tonnes"], row["missing_tonnes"]), (0.0, 1.0))

    def test_bar_held_meets_a_need_for_bar(self):
        row = bar_bill({"iron_bar_kg": 0.4}, 0.0)
        self.assertEqual((row["held_from_stock_tonnes"], row["missing_tonnes"]), (0.4, 0.6))

    def test_the_mines_ore_flow_meets_a_need_for_ore(self):
        row = bar_bill({}, 5.0, material="iron_ore_kg")
        self.assertEqual((row["held_from_own_output_tonnes"], row["missing_tonnes"]), (1.0, 0.0))

    def test_bar_held_does_not_meet_a_need_for_ore(self):
        row = bar_bill({"iron_bar_kg": 5.0}, 0.0, material="iron_ore_kg")
        self.assertEqual((row["held_from_stock_tonnes"], row["missing_tonnes"]), (0.0, 1.0))


def reading(industrial, opening, own_per_year, market=100.0):
    return rules.throttle_reading(industrial, {}, [("iron", "mine:iron")], 0.0, 0.0, opening, lambda _tag: own_per_year,
                                  lambda _commodity: market, FLOW_KEY.__getitem__, 0.05)


class DrawByFormTests(unittest.TestCase):
    def test_a_bar_need_is_not_met_by_ore_stock_or_the_ore_flow(self):
        result = reading({("iron", "mine:iron", "iron_bar_kg"): 4.0}, {"iron_ore_kg": 3.0}, 2.0, market=1.0)
        self.assertAlmostEqual(result.pace, 0.25)
        self.assertEqual(result.binding, "iron")

    def test_the_market_leg_buys_the_shortfall_of_the_named_form(self):
        result = reading({("iron", "mine:iron", "iron_bar_kg"): 4.0}, {}, 2.0)
        self.assertEqual(result.pace, 1.0)
        self.assertEqual([tonnes for _commodity, tonnes in result.draws if tonnes > 0], [4.0])

    def test_unused_flow_is_banked_as_ore_and_bar_stock_as_bar(self):
        result = reading({("iron", "mine:iron", "iron_bar_kg"): 1.0}, {"iron_bar_kg": 3.0}, 2.0)
        self.assertEqual(dict(result.banked), {"iron_bar_kg": 2.0, "iron_ore_kg": 2.0})

    def test_the_forms_of_one_pool_share_its_market_offer(self):
        industrial = {("iron", "mine:iron", "iron_bar_kg"): 3.0, ("iron", "mine:iron", "iron_bloom_kg"): 3.0}
        result = rules.throttle_reading(industrial, {}, [], 0.0, 0.0, {}, lambda _tag: 0.0, lambda _commodity: 4.0,
                                        FLOW_KEY.__getitem__, 0.05)
        self.assertAlmostEqual(result.pace, 1.0 / 3.0)


class DemandSplitTests(unittest.TestCase):
    def test_demand_is_keyed_by_the_form_it_asks_for(self):
        industrial, lab = rules.throttle_demand_split({"iron_bar_kg": 2.0, "iron_ore_kg": 3.0}, POOLS.__getitem__, lambda material: material)
        self.assertEqual(dict(industrial), {("iron", "mine:iron", "iron_bar_kg"): 2.0, ("iron", "mine:iron", "iron_ore_kg"): 3.0})
        self.assertEqual(dict(lab), {})


if __name__ == "__main__":
    unittest.main()
