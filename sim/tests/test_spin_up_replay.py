"""SCENARIO (Complaint 473): the spin-up replay prints, per year, what the opening's settle test measures, and the gap
it ends with is the one the saved opening reports. The replay and the run share the watched goods and the year's
state (sim/markets/spin_up_year.py)."""
QUICK_TOPIC = True

import types
import unittest
from unittest import mock

from sim.markets import spin_up_stages
from sim.markets.spin_up_gap import price_gaps, window_gaps, worst_price_change
from sim.markets.spin_up_year import watched_goods_of, year_state


class WatchedGoodsTests(unittest.TestCase):
    def test_the_goods_with_the_largest_spending_come_first_and_an_unpriced_good_spends_nothing(self):
        basket = {"wheat": 10.0, "salt": 1.0, "wool": 5.0, "air": 1000.0}
        prices = {"wheat": 1.0, "salt": 100.0, "wool": 1.0}
        self.assertEqual(watched_goods_of(basket, prices, 2), ["salt", "wheat"])


class YearStateTests(unittest.TestCase):
    def test_the_state_carries_the_quantities_and_only_the_watched_goods_that_were_priced(self):
        state = year_state({"real_output": 3.0, "food_need": 2.0}, 1.5, 0.04, {"wheat": 2.0, "salt": None, "iron": 9.0},
                           ["wheat", "salt", "wool"], {"wheat", "salt", "wool", "iron"})
        self.assertEqual(state, {"real_output": 3.0, "food_need": 2.0, "price_level": 1.5, "rate": 0.04,
                                 "prices": {"wheat": 2.0}, "unmeasured": {"salt": "no_price", "wool": "no_price"}})

    def test_a_watched_price_that_is_not_a_trade_is_left_out_with_its_cause(self):
        state = year_state({}, 1.0, None, {"wheat": 2.0, "salt": 5.0}, ["wheat", "salt"], {"wheat"})
        self.assertEqual(state["prices"], {"wheat": 2.0})
        self.assertEqual(state["unmeasured"], {"salt": "price_not_a_trade"})


class PriceGapsTests(unittest.TestCase):
    def test_each_good_has_its_own_change_and_a_good_unpriced_now_changes_wholly(self):
        gaps = price_gaps({"wheat": 1.1, "salt": None, "wool": 5.0}, {"wheat": 1.0, "salt": 2.0, "iron": None})
        self.assertAlmostEqual(gaps["wheat"], 0.1)
        self.assertEqual(gaps["salt"], 1.0)
        self.assertNotIn("wool", gaps)
        self.assertNotIn("iron", gaps)

    def test_the_worst_price_change_names_the_good_over_all_consecutive_years(self):
        states = [{"prices": {"wheat": 1.0, "salt": 1.0}}, {"prices": {"wheat": 1.1, "salt": 1.0}},
                  {"prices": {"wheat": 1.1, "salt": 1.5}}]
        good, gap = worst_price_change(states)
        self.assertEqual(good, "salt")
        self.assertAlmostEqual(gap, 0.5)


def _row(stage, year, level, hired):
    return {"stage": stage, "year": year, "price_level": level, "rate": 0.05, "real_output": 10.0, "hired_hours": hired,
            "idle_hours": 1.0, "inventory_value": 4.0, "unmet_need": 0.0, "food_need": 5.0, "prices": {"wheat": level}}


class EndGapTests(unittest.TestCase):
    def test_the_end_gaps_are_the_window_gaps_of_the_last_trimmed_years(self):
        rows = [_row("first", 0, 9.0, 1.0), _row("trimmed", 0, 1.0, 100.0), _row("trimmed", 1, 1.2, 100.0),
                _row("trimmed", 2, 1.2, 110.0), _row("trimmed", 3, 1.26, 110.0)]
        report = spin_up_stages.end_gaps(rows, 3)
        self.assertEqual(report["gaps"], window_gaps(rows[-3:]))
        self.assertEqual(report["measured_years"], 3)
        self.assertEqual(report["worst_price"][0], "wheat")
        self.assertAlmostEqual(report["worst_price"][1], 0.05)

    def test_fewer_than_two_trimmed_years_measure_no_gaps(self):
        report = spin_up_stages.end_gaps([_row("first", 0, 1.0, 1.0), _row("trimmed", 0, 1.0, 1.0)], 4)
        self.assertIsNone(report["gaps"])


class ReplayTests(unittest.TestCase):
    def test_the_workforce_is_trimmed_once_between_the_first_stage_and_the_trimmed_stage(self):
        calls = []

        class Economy:
            def step(self, inputs):
                calls.append("step")
                return types.SimpleNamespace(basket_price_level=1.0, money_supply=7.0, prices={"wheat": 1.0},
                                             wages={"labour": 2.0})

        def trim(economy):
            calls.append("trim")
        patches = {"spin_up_state": lambda economy, outcome: {"real_output": 1.0}, "interest_rate": lambda economy: 0.05,
                   "money_year_figures": lambda economy, outcome: {"struck": 0.0, "wear": 0.0},
                   "economy_book": lambda economy: None, "currency_id": lambda economy: "coin",
                   "trim_workforce_to_expected_hours": trim, "traded_price_goods": lambda economy: {"wheat"}}
        with mock.patch.multiple(spin_up_stages.economy_api, **patches), \
                mock.patch.object(spin_up_stages, "money_by_holder_columns", lambda book, currency: {}):
            rows = list(spin_up_stages.replay(Economy(), object(), ["wheat"], "labour", 2, 3))
        self.assertEqual(calls, ["step", "step", "trim", "step", "step", "step"])
        self.assertEqual([(row["stage"], row["year"]) for row in rows],
                         [("first", 0), ("first", 1), ("trimmed", 0), ("trimmed", 1), ("trimmed", 2)])
        self.assertEqual(rows[0]["wage"], 2.0)
        self.assertEqual(rows[0]["prices"], {"wheat": 1.0})


if __name__ == "__main__":
    unittest.main()
