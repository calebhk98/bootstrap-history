"""A concern's volume, takings and the household's real income, called with entries, prices and baskets built here
(Complaint 640): the volume and value ratios against the opening, the held-technique choice, takings as the product
of their factors, and the real-income ratio's reading of the basket."""
QUICK_TOPIC = True

import unittest
from sim.tests import market_stand_in
from types import SimpleNamespace

from sim.agents import supply
from sim.production import volume_rules as concern_volume
from sim.production.concern_earnings import takings_at
from sim.markets.api import MEAN_INCOME_HOURS_PER_CAPITA
from sim.markets.module import Markets
from sim.tests import module_harness

OPENING_PRICES = {"lime": 3.0, "limestone": 1.0}
STAFF = 4.0


def lime_entry(labour_per_batch, requires_node, outputs=None):
    return {"outputs": outputs or {"lime": 100.0}, "inputs": {"limestone": 150.0},
            "labour_hours": {"burner": labour_per_batch}, "requires_node": requires_node, "operated_by": []}


NODE = {"id": "kiln", "sch": 0.0, "art": STAFF}
OWN_ONLY = frozenset({"kiln"})


def ratios_with(production, held_now, prices_now=None):
    return concern_volume.ratios(NODE, production, (OWN_ONLY, OPENING_PRICES),
                                 (frozenset(held_now), prices_now or OPENING_PRICES))


class HeldTechniqueTests(unittest.TestCase):
    def test_a_concern_with_nothing_new_held_is_at_its_opening(self):
        production = dict(base=lime_entry(10.0, "kiln"), better=lime_entry(5.0, "new_kiln"))
        volume, value, baskets = ratios_with(production, OWN_ONLY)
        self.assertEqual((volume, value), (1.0, 1.0))
        self.assertIsNotNone(baskets)

    def test_halving_the_labour_per_unit_doubles_what_the_same_staff_turn_out(self):
        production = dict(base=lime_entry(10.0, "kiln"), better=lime_entry(5.0, "new_kiln"))
        volume, value, _ = ratios_with(production, OWN_ONLY | {"new_kiln"})
        self.assertAlmostEqual(volume, 2.0)
        self.assertAlmostEqual(value, 2.0)

    def test_the_staff_are_unchanged_by_the_better_technique(self):
        production = dict(base=lime_entry(10.0, "kiln"), better=lime_entry(5.0, "new_kiln"))
        before = concern_volume.baskets_for(NODE, production, OWN_ONLY, OPENING_PRICES)
        after = concern_volume.baskets_for(NODE, production, OWN_ONLY | {"new_kiln"}, OPENING_PRICES)
        self.assertAlmostEqual(before.labour_hours["burner"], after.labour_hours["burner"])

    def test_a_technique_for_another_line_does_not_enter_the_concern(self):
        production = dict(base=lime_entry(10.0, "kiln"), other=lime_entry(1.0, "new_kiln", outputs={"brick": 100.0}))
        volume, value, _ = ratios_with(production, OWN_ONLY | {"new_kiln"})
        self.assertEqual((volume, value), (1.0, 1.0))

    def test_a_dearer_technique_cannot_lower_the_volume_below_the_best_held(self):
        production = dict(base=lime_entry(10.0, "kiln"), worse=lime_entry(20.0, "new_kiln"))
        volume, _, _ = ratios_with(production, OWN_ONLY | {"new_kiln"})
        self.assertEqual(volume, 1.0)

    def test_a_node_with_no_production_entry_has_ratios_of_one_and_no_baskets(self):
        self.assertEqual(concern_volume.ratios(NODE, {}, (OWN_ONLY, OPENING_PRICES), (OWN_ONLY, OPENING_PRICES)),
                         (1.0, 1.0, None))

    def test_entries_held_are_the_nodes_own_and_those_of_held_nodes_for_its_lines(self):
        base, better, unheld = lime_entry(10.0, "kiln"), lime_entry(5.0, "new_kiln"), lime_entry(2.0, "unknown_kiln")
        production = dict(base=base, better=better, unheld=unheld)
        held = concern_volume.entries_held_for("kiln", production, OWN_ONLY | {"new_kiln"})
        self.assertIn(base, held)
        self.assertIn(better, held)
        self.assertNotIn(unheld, held)

    def test_volume_is_read_at_the_opening_prices_and_value_at_the_prices_now(self):
        production = dict(base=lime_entry(10.0, "kiln"))
        dearer_lime = dict(OPENING_PRICES, lime=6.0)
        volume, value, _ = ratios_with(production, OWN_ONLY, prices_now=dearer_lime)
        self.assertEqual(volume, 1.0)
        # net per batch: lime 100 * 6 less limestone 150 * 1, against 100 * 3 less 150 * 1
        self.assertAlmostEqual(value, (600.0 - 150.0) / (300.0 - 150.0))


class TakingsTests(unittest.TestCase):
    def test_takings_are_the_product_of_ramp_hazard_price_level_value_and_learning(self):
        self.assertAlmostEqual(takings_at(100.0, 0.5, 0.8, 1.1, 2.0, 1.25), 100.0 * 0.5 * 0.8 * 1.1 * 2.0 * 1.25)

    def test_takings_rise_in_proportion_to_the_value_ratio(self):
        low = takings_at(100.0, 1.0, 1.0, 1.0, 1.0, 1.0)
        self.assertAlmostEqual(takings_at(100.0, 1.0, 1.0, 1.0, 1.5, 1.0), 1.5 * low)

    def test_a_concern_with_nothing_run_better_earns_what_its_tree_figure_says(self):
        self.assertEqual(takings_at(100.0, 1.0, 1.0, 1.0, 1.0, 1.0), 100.0)


class MarketOutputTests(unittest.TestCase):
    def test_a_concern_puts_on_the_market_in_proportion_to_what_its_staff_turn_out(self):
        node = {"annual_output_t": 0.0}
        once = supply.concern_output_tonnes(node, "kiln", "lime", 1.0, 1.0, derived_tonnes=10.0)
        twice = supply.concern_output_tonnes(node, "kiln", "lime", 1.0, 1.0, derived_tonnes=20.0)
        self.assertAlmostEqual(twice, 2.0 * once)

    def test_it_is_scaled_by_ramp_and_by_the_share_of_staff_found(self):
        node = {"annual_output_t": 0.0}
        self.assertAlmostEqual(supply.concern_output_tonnes(node, "kiln", "lime", 0.5, 0.5, derived_tonnes=10.0), 2.5)


class RealIncomeTests(unittest.TestCase):
    """household_real_income_ratio reads the basket, today's household prices, money per hour and the wage ratio."""

    def ratio(self, now_prices, wage_ratio=1.0, per_hour=1.0):
        basket = {"units": {"grain": 10.0, "cloth": 2.0}, "prices": {"grain": 1.0, "cloth": 5.0}}
        game = market_stand_in.markets_over(goods_market=SimpleNamespace(household_cost_prices=lambda: now_prices),
                                            money_per_labour_hour=per_hour)
        game.static_book_basket = lambda: basket
        game.household_income_hours_per_capita = lambda: MEAN_INCOME_HOURS_PER_CAPITA * wage_ratio
        return game.household_real_income_ratio()

    def test_at_the_opening_prices_and_wage_it_is_one(self):
        self.assertAlmostEqual(self.ratio({"grain": 1.0, "cloth": 5.0}), 1.0)

    def test_cheaper_goods_raise_what_an_income_buys(self):
        self.assertGreater(self.ratio({"grain": 0.8, "cloth": 4.0}), 1.0)

    def test_dearer_goods_lower_it(self):
        self.assertLess(self.ratio({"grain": 1.5, "cloth": 5.0}), 1.0)

    def test_a_higher_wage_raises_it_in_proportion(self):
        self.assertAlmostEqual(self.ratio({"grain": 1.0, "cloth": 5.0}, wage_ratio=1.2), 1.2)

    def test_a_good_nobody_prices_is_left_out_of_both_costs(self):
        self.assertAlmostEqual(self.ratio({"grain": 1.0}), 1.0)

    def test_with_nothing_priced_it_is_one(self):
        self.assertEqual(self.ratio({}), 1.0)

    def test_prices_are_taken_into_hours_by_money_per_hour(self):
        self.assertAlmostEqual(self.ratio({"grain": 2.0, "cloth": 10.0}, per_hour=2.0), 1.0)


if __name__ == "__main__":
    unittest.main()
