"""Complaint 640 (from 558): real output is the quantity the economy clears valued at fixed opening prices. The
arithmetic (sim/engine/real_output_measure.py) is called on built baskets and volumes, so a failure names the line
of arithmetic and not a game."""
QUICK_TOPIC = True

import unittest

from sim.engine import real_output_measure as measure

BASKET = {"prices": {"grain": 2.0, "cloth": 5.0, "salt": 10.0}, "units": {"grain": 100.0, "cloth": 20.0, "salt": 5.0}}
BASELINE = {"grain": 50.0, "cloth": 10.0, "salt": 2.0}


def output(traded, scale, introduced=None, new_goods=(), volumes=None):
    lines = measure.output_lines(BASKET, traded, scale, introduced or {}, new_goods, volumes or {})
    return sum(units * price for _good, units, price in lines), lines


def value_of_basket(goods):
    return sum(BASKET["units"][good] * BASKET["prices"][good] for good in goods)


class TradedMeasureTests(unittest.TestCase):
    def test_before_any_year_closes_the_basket_stands_with_a_scale_of_one(self):
        traded, scale = measure.traded_measure(BASKET, {}, {})
        self.assertEqual(traded, BASKET["units"])
        self.assertEqual(scale, 1.0)

    def test_the_baseline_year_is_worth_the_opening_basket_whatever_the_economy_traded_then(self):
        traded, scale = measure.traded_measure(BASKET, BASELINE, dict(BASELINE))
        total, _lines = output(traded, scale)
        self.assertAlmostEqual(total, value_of_basket(BASKET["units"]), places=9)

    def test_only_goods_with_a_baseline_are_measured(self):
        traded, _scale = measure.traded_measure(BASKET, {"grain": 50.0}, {"grain": 60.0, "cloth": 99.0})
        self.assertEqual(set(traded), {"grain"})

    def test_a_good_the_economy_sold_half_as_much_again_of_adds_half_its_baseline_weight(self):
        volumes = dict(BASELINE)
        volumes["grain"] *= 1.5
        traded, scale = measure.traded_measure(BASKET, BASELINE, volumes)
        total, _lines = output(traded, scale)
        extra = 0.5 * BASELINE["grain"] * BASKET["prices"]["grain"] * scale
        self.assertAlmostEqual(total, value_of_basket(BASKET["units"]) + extra, places=9)

    def test_a_good_the_economy_stopped_trading_counts_for_nothing(self):
        volumes = dict(BASELINE)
        volumes["salt"] = 0.0
        traded, scale = measure.traded_measure(BASKET, BASELINE, volumes)
        total, _lines = output(traded, scale)
        lost = scale * BASELINE["salt"] * BASKET["prices"]["salt"]       # the scale stays the baseline year's
        self.assertAlmostEqual(total, value_of_basket(BASKET["units"]) - lost, places=9)

    def test_a_baseline_with_no_value_gives_a_scale_of_zero_not_a_division(self):
        _traded, scale = measure.traded_measure({"prices": {"grain": 2.0}, "units": {"grain": 1.0}}, {"other": 1.0}, {})
        self.assertEqual(scale, 0.0)


class OutputLinesTests(unittest.TestCase):
    def test_the_lines_add_up_to_the_output_and_each_is_units_at_its_opening_price(self):
        traded, scale = measure.traded_measure(BASKET, BASELINE, {"grain": 80.0, "cloth": 12.0, "salt": 2.0})
        total, lines = output(traded, scale)
        for good, units, price in lines:
            self.assertEqual(price, BASKET["prices"][good])
            self.assertAlmostEqual(units, traded[good] * scale)
        self.assertAlmostEqual(total, sum(units * price for _good, units, price in lines))

    def test_a_new_good_counts_at_its_introduction_price_once_the_economy_trades_it(self):
        traded, scale = measure.traded_measure(BASKET, BASELINE, dict(BASELINE))
        without, _lines = output(traded, scale)
        total, lines = output(traded, scale, {"glass": 7.0}, ["glass"], {"glass": 3.0})
        self.assertAlmostEqual(total - without, 21.0)
        self.assertIn(("glass", 3.0, 7.0), lines)

    def test_a_new_good_nobody_trades_or_with_no_introduction_price_adds_nothing(self):
        traded, scale = measure.traded_measure(BASKET, BASELINE, dict(BASELINE))
        without, _lines = output(traded, scale)
        self.assertEqual(output(traded, scale, {"glass": 7.0}, ["glass"], {"glass": 0.0})[0], without)
        self.assertEqual(output(traded, scale, {}, ["glass"], {"glass": 3.0})[0], without)


if __name__ == "__main__":
    unittest.main()
