"""The stock accounting of the material throttle, called with figures built here (Complaint 640): unused own output
banks once per year, old inventory covers later demand, the market's standing offer never banks, and a shortfall slows
work to the share it covers but not below the floor."""
QUICK_TOPIC = True

import unittest

from sim.engine.material_throttle import draw_one_material, year_opening_record

FLOOR = 0.05


def draw(opening=0.0, own=0.0, market=0.0, lab=0.0, industrial=0.0):
    return draw_one_material(opening, own, market, lab, industrial, FLOOR)


class BankingTests(unittest.TestCase):
    def test_unused_own_output_banks_in_full(self):
        self.assertEqual(draw(own=100.0).banked, 100.0)

    def test_prior_stock_and_own_output_both_bank_when_nothing_is_drawn(self):
        self.assertEqual(draw(opening=60.0, own=100.0).banked, 160.0)

    def test_old_stock_covers_demand_without_production_and_the_rest_stays(self):
        result = draw(opening=100.0, industrial=50.0)
        self.assertIsNone(result.pace)
        self.assertAlmostEqual(result.banked, 50.0)

    def test_the_markets_standing_offer_is_drawn_but_never_banked(self):
        result = draw(market=500.0, industrial=50.0)
        self.assertIsNone(result.pace)
        self.assertEqual(result.banked, 0.0)
        unused = draw(market=500.0)
        self.assertEqual(unused.banked, 0.0)

    def test_a_draw_from_the_market_is_a_net_draw_beyond_what_was_owned(self):
        self.assertAlmostEqual(draw(own=10.0, market=500.0, industrial=50.0).net_draw, 40.0)
        self.assertAlmostEqual(draw(own=100.0, industrial=50.0).net_draw, -50.0)


class ShortfallTests(unittest.TestCase):
    def test_a_shortfall_slows_work_to_the_share_it_covers(self):
        result = draw(own=30.0, industrial=100.0)
        self.assertAlmostEqual(result.pace, 0.3)
        self.assertEqual(result.banked, 0.0)

    def test_a_shortfall_never_stops_work_below_the_floor(self):
        self.assertEqual(draw(own=0.1, industrial=1000.0).pace, FLOOR)

    def test_laboratory_scale_need_is_met_first_and_never_sets_the_pace(self):
        result = draw(own=10.0, lab=4.0)
        self.assertIsNone(result.pace)
        self.assertAlmostEqual(result.lab_drawn, 4.0)
        self.assertAlmostEqual(result.banked, 6.0)

    def test_laboratory_need_comes_off_what_industry_can_use(self):
        result = draw(own=100.0, lab=40.0, industrial=100.0)
        self.assertAlmostEqual(result.pace, 0.6)

    def test_a_need_above_everything_held_draws_all_of_it(self):
        result = draw(opening=5.0, own=5.0, market=5.0, lab=100.0)
        self.assertEqual(result.lab_drawn, 15.0)

    def test_no_industrial_need_leaves_no_pace(self):
        self.assertIsNone(draw(own=1.0).pace)


class OpeningRecordTests(unittest.TestCase):
    def test_a_new_year_takes_a_fresh_copy_of_the_stock(self):
        stock = {"iron": 100.0}
        record = year_opening_record(None, 1000, stock)
        stock["iron"] = 5.0
        self.assertEqual(record, {"year": 1000, "tonnes": {"iron": 100.0}})

    def test_the_same_year_keeps_the_record_so_output_banks_once(self):
        first = year_opening_record(None, 1000, {"iron": 100.0})
        again = year_opening_record(first, 1000, {"iron": 300.0})
        self.assertIs(again, first)
        self.assertEqual(again["tonnes"]["iron"], 100.0)

    def test_the_next_year_banks_another_years_output(self):
        first = year_opening_record(None, 1000, {"iron": 100.0})
        second = year_opening_record(first, 1001, {"iron": 200.0})
        self.assertEqual(second, {"year": 1001, "tonnes": {"iron": 200.0}})
        self.assertEqual(draw(opening=second["tonnes"]["iron"], own=100.0).banked, 300.0)


if __name__ == "__main__":
    unittest.main()
