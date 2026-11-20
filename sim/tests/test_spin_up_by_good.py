"""spin_up_by_good: which watched goods a spin-up's "prices" gap is made of, each good's trend and saw, and which goods
a change in stock or output is made of."""

QUICK_TOPIC = True

import unittest

from sim.markets.spin_up_by_good import (by_good, largest_moves, level_of, level_parts, mix_parts, price_level_parts, price_parts,
                                         price_trends, trend_and_saw, value_parts, worst_pair)
from sim.markets.spin_up_gap import price_gap


def state(prices, weights=None, stage="trimmed", **quantities):
    made = {"stage": stage, "prices": dict(prices), **quantities}
    if weights:
        made["price_weights"] = dict(weights)
    return made


class WorstPair(unittest.TestCase):
    def test_the_pair_of_years_with_the_largest_gap_in_the_quantity(self):
        first, second, third = (state({}, real_output=100.0), state({}, real_output=101.0), state({}, real_output=111.1))
        self.assertEqual(worst_pair([first, second, third], "real_output"), (second, third))

    def test_the_earliest_pair_of_equal_gaps(self):
        first, second, third = (state({}, real_output=100.0), state({}, real_output=110.0), state({}, real_output=121.0))
        self.assertEqual(worst_pair([first, second, third], "real_output"), (first, second))

    def test_fewer_than_two_states_have_no_pair(self):
        self.assertIsNone(worst_pair([state({})], "prices"))


class PriceParts(unittest.TestCase):
    def test_each_goods_part_is_its_share_of_the_spending_times_its_change_largest_first(self):
        before = state({"bread": 1.0, "cloth": 10.0, "cart": 100.0}, {"bread": 6.0, "cloth": 3.0, "cart": 1.0})
        after = state({"bread": 1.1, "cloth": 10.0, "cart": 150.0})
        parts = price_parts(before, after)
        self.assertEqual([good for good, _share, _gap, _part in parts], ["bread", "cart", "cloth"])
        bread, cart, cloth = parts
        self.assertAlmostEqual(bread[1], 0.6)
        self.assertAlmostEqual(bread[2], 0.1)
        self.assertAlmostEqual(bread[3], 0.06)
        self.assertAlmostEqual(cart[3], 0.05)
        self.assertEqual(cloth[3], 0.0)

    def test_the_parts_add_up_to_the_price_gap_of_the_pair(self):
        before = state({"bread": 1.0, "cloth": 10.0}, {"bread": 6.0, "cloth": 3.0, "cart": 1.0})
        after = state({"bread": 1.2, "cloth": 9.0})
        total = sum(part for _good, _share, _gap, part in price_parts(before, after))
        self.assertAlmostEqual(total, price_gap(after["prices"], before["prices"], before["price_weights"]))

    def test_with_no_shares_every_good_priced_counts_alike(self):
        parts = price_parts(state({"bread": 1.0, "cloth": 10.0}), state({"bread": 1.5, "cloth": 10.0}))
        self.assertEqual(parts[0], ("bread", 0.5, 0.5, 0.25))


class LargestMoves(unittest.TestCase):
    def test_each_goods_largest_change_between_consecutive_years(self):
        states = [state({"bread": 1.0, "cloth": 10.0}), state({"bread": 1.1, "cloth": 10.0}), state({"bread": 1.1, "cloth": 8.0})]
        moves = largest_moves(states)
        self.assertAlmostEqual(moves["bread"], 0.1)
        self.assertAlmostEqual(moves["cloth"], 0.2)


class TrendAndSaw(unittest.TestCase):
    def test_a_steady_rise_is_all_trend(self):
        trend, saw = trend_and_saw([100.0, 110.0, 121.0, 133.1])
        self.assertAlmostEqual(trend, 0.1)
        self.assertAlmostEqual(saw, 0.0)

    def test_a_price_that_goes_up_and_back_is_all_saw(self):
        trend, saw = trend_and_saw([100.0, 125.0, 100.0, 125.0, 100.0])
        self.assertAlmostEqual(trend, 0.025)        # up a quarter, down a fifth: the mean of the two
        self.assertAlmostEqual(saw, 0.225)

    def test_a_year_with_no_value_breaks_the_chain_there(self):
        trend, saw = trend_and_saw([100.0, None, 100.0, 110.0])
        self.assertAlmostEqual(trend, 0.1)
        self.assertAlmostEqual(saw, 0.0)

    def test_no_pair_of_years_gives_none(self):
        self.assertIsNone(trend_and_saw([100.0]))
        self.assertIsNone(trend_and_saw([100.0, None, 100.0]))


class PriceTrends(unittest.TestCase):
    def test_each_watched_good_priced_in_two_consecutive_rows(self):
        rows = [state({"bread": 1.0, "cart": 5.0}), state({"bread": 1.1}), state({"bread": 1.21})]
        trends = price_trends(rows)
        self.assertEqual(sorted(trends), ["bread"])
        self.assertAlmostEqual(trends["bread"][0], 0.1)


class ValueParts(unittest.TestCase):
    def test_each_goods_change_as_a_share_of_the_base_largest_in_size_first(self):
        parts = value_parts({"grain": 50.0, "cloth": 30.0, "ale": 5.0}, {"grain": 40.0, "cloth": 32.0, "ale": 5.0}, 200.0)
        self.assertEqual(parts, [("grain", -0.05), ("cloth", 0.01)])

    def test_a_good_in_one_year_only_changed_by_its_whole_value(self):
        self.assertEqual(value_parts({}, {"cart": 10.0}, 100.0), [("cart", 0.1)])

    def test_no_base_gives_nothing(self):
        self.assertEqual(value_parts({"grain": 1.0}, {"grain": 2.0}, 0.0), [])


class MixParts(unittest.TestCase):
    def test_the_stock_change_by_good_in_the_pair_where_stock_moved_most_against_the_earlier_years_output(self):
        states = [state({}, real_output=100.0, inventory_value=50.0, mix={"stock_by_good": {"grain": 30.0, "cloth": 20.0}}),
                  state({}, real_output=100.0, inventory_value=50.5, mix={"stock_by_good": {"grain": 30.5, "cloth": 20.0}}),
                  state({}, real_output=200.0, inventory_value=60.5, mix={"stock_by_good": {"grain": 28.5, "cloth": 32.0}})]
        self.assertEqual(mix_parts(states, "inventory_value", "stock_by_good"), [("cloth", 0.12), ("grain", -0.02)])

    def test_rows_that_carry_no_mix_give_nothing(self):
        self.assertEqual(mix_parts([state({}, real_output=1.0), state({}, real_output=2.0)], "real_output", "output_by_good"), [])


class LevelOf(unittest.TestCase):
    def test_the_basket_cost_now_over_its_cost_at_the_base(self):
        self.assertAlmostEqual(level_of({"bread": (30.0, 20.0), "cloth": (90.0, 80.0)}), 1.2)

    def test_nothing_counted_is_level_one(self):
        self.assertEqual(level_of({}), 1.0)


class LevelParts(unittest.TestCase):
    def test_a_good_whose_price_moved_by_what_the_level_would_be_at_its_earlier_cost(self):
        before = {"bread": (20.0, 20.0), "cloth": (80.0, 80.0)}
        after = {"bread": (30.0, 20.0), "cloth": (80.0, 80.0)}
        self.assertEqual(level_parts(before, after), [("bread", "moved", 1.1 - 1.0)])

    def test_a_dear_good_that_enters_the_count_raises_the_level_and_one_that_leaves_lowers_it(self):
        base = {"cloth": (80.0, 80.0)}
        with_glass = {"cloth": (80.0, 80.0), "glass": (60.0, 20.0)}       # glass at three times its base price
        entered = level_parts(base, with_glass)
        self.assertEqual([(good, kind) for good, kind, _effect in entered], [("glass", "entered")])
        self.assertAlmostEqual(entered[0][2], 1.4 - 1.0)
        left = level_parts(with_glass, base)
        self.assertEqual([(good, kind) for good, kind, _effect in left], [("glass", "left")])
        self.assertAlmostEqual(left[0][2], 1.0 - 1.4)

    def test_the_largest_effect_comes_first_and_a_good_that_did_not_move_is_left_out(self):
        before = {"bread": (20.0, 20.0), "cloth": (80.0, 80.0), "ale": (10.0, 10.0)}
        after = {"bread": (22.0, 20.0), "cloth": (60.0, 80.0), "ale": (10.0, 10.0)}
        self.assertEqual([good for good, _kind, _effect in level_parts(before, after)], ["cloth", "bread"])


class PriceLevelParts(unittest.TestCase):
    def test_the_parts_of_the_pair_where_the_level_moved_most_as_shares_of_the_earlier_level(self):
        states = [state({}, price_level=1.0, mix={"basket_costs": {"cloth": (80.0, 80.0)}}),
                  state({}, price_level=1.01, mix={"basket_costs": {"cloth": (80.8, 80.0)}}),
                  state({}, price_level=1.5, mix={"basket_costs": {"cloth": (80.8, 80.0), "glass": (69.2, 20.0)}})]
        parts = price_level_parts(states)
        self.assertEqual([(good, kind) for good, kind, _effect in parts], [("glass", "entered")])
        self.assertAlmostEqual(parts[0][2], (1.5 - 1.01) / 1.01)

    def test_rows_that_carry_no_mix_give_nothing(self):
        self.assertEqual(price_level_parts([state({}, price_level=1.0), state({}, price_level=1.2)]), [])


class ByGood(unittest.TestCase):
    def test_the_measured_years_give_share_move_and_part_and_the_whole_trimmed_stage_trend_and_saw(self):
        weights = {"bread": 3.0, "cloth": 1.0}
        rows = [state({"bread": 9.0}, weights, stage="first"),
                state({"bread": 1.0, "cloth": 10.0}, weights), state({"bread": 2.0, "cloth": 10.0}, weights),
                state({"bread": 2.0, "cloth": 11.0}, weights), state({"bread": 2.2, "cloth": 11.0}, weights)]
        table = by_good(rows, 3)
        self.assertAlmostEqual(table["bread"]["share"], 0.75)
        self.assertAlmostEqual(table["bread"]["move"], 0.1)          # the doubling is before the three measured years
        self.assertAlmostEqual(table["bread"]["part"], 0.075)        # the worst measured pair is bread's tenth, at three quarters of the spending
        self.assertAlmostEqual(table["cloth"]["part"], 0.0)          # cloth did not move in that pair
        self.assertAlmostEqual(table["cloth"]["move"], 0.1)
        self.assertAlmostEqual(table["bread"]["trend"], (1.0 + 0.0 + 0.1) / 3)


if __name__ == "__main__":
    unittest.main()
