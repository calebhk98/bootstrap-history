"""Each block read of the labour core's state (state_reads.py) gives, bit for bit, what the per-item readers gave through the dict views,
on a state written out here with awkward floats, empty pairs, a trade only one area has and an area the state does not number."""

QUICK_TOPIC = True

import math
import unittest

import numpy

from sim.economy import labour_state
from sim.labour.market import state_read_kernels, state_reads
from sim.labour.market.market_state import MarketState

BANDS = 3


def awkward_state() -> MarketState:
    """Three areas and three trades; an empty pair, a wage-only pair, a pair with a short band list, trainees in two pairs."""
    state = MarketState(
        workers={
            "work@b": {"smith": [0.1, 0.2, 0.3], "farmer": [1e16, 1.0, -1e16], "weaver": [0.0, 0.0, 0.0]},
            "work@a": {"smith": [0.7, 0.1, 0.2], "farmer": [3.3, 0.1, 0.01]},
            "work@c": {},
        },
        trainees={"work@a": {"smith": [[2.0, [0.1, 0.2, 0.7], 0.0], [1.0, [0.3, 0.3, 0.3], 0.5]]},
                  "work@b": {"farmer": [[1.0, [0.1, 0.1, 0.1], 0.0]]}},
        wages={"work@a": {"smith": 1.1, "farmer": 0.7, "weaver": 0.3}, "work@b": {"smith": 2.3, "farmer": 0.9}, "work@c": {"weaver": 0.4}},
        hired_hours={"work@a": {"smith": {"x": 0.1, "y": 0.2, "z": 0.3}, "farmer": {"x": 1e16, "y": 1.0, "z": -1e16}},
                     "work@b": {"smith": {}, "farmer": {"y": 7.5}}},
    )
    return state


def view_hours_cleared(state, area, trade):
    return math.fsum(state.hired_hours.get(area, {}).get(trade, {}).values())


def view_people(state, area, trade):
    return math.fsum(state.workers.get(area, {}).get(trade, ()))


class BlockReadsEqualViewReads(unittest.TestCase):
    def test_hours_cleared_at_each_market_is_the_fsum_of_its_employers(self):
        state = awkward_state()
        pairs = [("work@a", "smith"), ("work@a", "farmer"), ("work@b", "smith"), ("work@b", "farmer"), ("work@c", "weaver"),
                 ("work@a", "weaver"), ("work@z", "smith"), ("work@a", "baker")]
        rows = state_reads.grid_rows_of(state, [area for area, _ in pairs], [trade for _, trade in pairs])
        self.assertEqual(rows.tolist()[-2:], [-1, -1])
        found = state_reads.hours_cleared_at(state, rows)
        self.assertEqual(found.tolist(), [view_hours_cleared(state, area, trade) for area, trade in pairs])

    def test_people_at_each_pair_is_the_fsum_of_its_bands(self):
        state = awkward_state()
        pairs = [("work@a", "smith"), ("work@b", "farmer"), ("work@b", "weaver"), ("work@c", "weaver"), ("work@z", "smith")]
        rows = state_reads.grid_rows_of(state, [area for area, _ in pairs], [trade for _, trade in pairs])
        self.assertEqual(state_reads.people_at(state, rows).tolist(), [view_people(state, area, trade) for area, trade in pairs])

    def test_people_by_trade_over_areas_adds_area_by_area_and_keeps_empty_pairs(self):
        state = awkward_state()
        areas = ["work@b", "work@a", "work@c", "work@z"]
        expected = {}
        for area in areas:
            for trade, bands in state.workers.get(area, {}).items():
                expected[trade] = expected.get(trade, 0.0) + math.fsum(bands)
        found = state_reads.people_by_trade_over(state, areas)
        self.assertEqual(found, dict(sorted(expected.items())))
        self.assertIn("weaver", found)

    def test_people_by_trade_in_each_area_is_one_area_at_a_time(self):
        state = awkward_state()
        areas = ["work@b", "work@a", "work@c", "work@z"]
        totals, seen = state_reads.people_by_trade_in_each_area(state, areas)
        names = state.ids.trades.names
        for place, area in enumerate(areas):
            single = state_reads.people_by_trade_over(state, [area])
            self.assertEqual({names[trade]: float(totals[place, trade]) for trade in numpy.flatnonzero(seen[place]).tolist()}, single)
        self.assertEqual(totals[3].tolist(), [0.0] * len(names))        # an area the state does not number holds nobody
        self.assertTrue(seen[2].sum() == 0 and seen[0].sum() == 3)

    def test_people_by_tile_reads_each_tile_as_people_by_trade_does(self):
        state = awkward_state()
        by_tile = labour_state.PeopleByTile(state)
        for tile, area in (("c", "work@c"), ("a", "work@a"), ("b", "work@b")):
            self.assertEqual(by_tile[tile], labour_state.people_by_trade(state, area))
        self.assertEqual(by_tile["b"]["weaver"], 0.0)

    def test_people_in_pairs_is_the_dict_read_of_each_pair(self):
        state = awkward_state()
        pairs = [("work@a", "smith"), ("work@b", "weaver"), ("work@c", "weaver"), ("work@z", "smith"), ("work@a", "baker")]
        found = labour_state.people_in_pairs(state, [area for area, _ in pairs], [trade for _, trade in pairs])
        self.assertEqual(found.tolist(), [labour_state.people_by_trade(state, area).get(trade, 0.0) for area, trade in pairs])

    def test_people_by_trade_matrix_has_a_row_per_area_in_trade_name_order(self):
        state = awkward_state()
        totals, names = labour_state.people_by_trade_matrix(state, ["work@b", "work@z"])
        self.assertEqual(names, ["farmer", "smith", "weaver"])
        self.assertEqual(totals[0].tolist(), [math.fsum([1e16, 1.0, -1e16]), math.fsum([0.1, 0.2, 0.3]), 0.0])
        self.assertEqual(totals[1].tolist(), [0.0, 0.0, 0.0])

    def test_scale_people_in_areas_is_scale_people_in_area_for_each(self):
        areas, factors = ["work@a", "work@z", "work@b", "work@c"], numpy.array([1.7, 3.0, 0.3, 2.0])
        block, single = awkward_state(), awkward_state()
        state_reads.scale_people_in_areas(block, areas, factors)
        for area, factor in zip(areas, factors.tolist()):
            state_reads.scale_people_in_area(single, area, factor)
        self.assertEqual(block.to_plain(), single.to_plain())
        self.assertNotEqual(block.to_plain(), awkward_state().to_plain())

    def test_follow_working_people_adds_to_an_empty_area_and_scales_the_rest(self):
        state, added = awkward_state(), []
        areas, people = ["work@c", "work@a", "work@b"], numpy.array([5.0, 0.7 + 0.1 + 0.2 + 3.3 + 0.1 + 0.01 + 2.0 + 1.0 + 0.5, 2.0])
        held = state_reads.people_in_areas(state, areas).tolist()
        labour_state.follow_working_people(state, areas, people, "farmer", lambda area, trade, count: added.append((area, trade, count)))
        self.assertEqual(added, [("work@c", "farmer", 5.0)])
        expected = awkward_state()
        state_reads.scale_people_in_area(expected, "work@a", people[1] / held[1])
        state_reads.scale_people_in_area(expected, "work@b", 2.0 / held[2])
        self.assertEqual(state.to_plain(), expected.to_plain())

    def test_working_people_in_areas_is_fsum_of_fsums(self):
        state = awkward_state()
        areas = ["work@a", "work@b", "work@c", "work@z"]
        expected = [math.fsum(math.fsum(bands) for bands in state.workers.get(area, {}).values()) for area in areas]
        self.assertEqual(state_reads.working_people_in_areas(state, areas).tolist(), expected)

    def test_people_in_areas_follows_the_order_of_the_views(self):
        state = awkward_state()
        areas = ["work@b", "work@a", "work@c", "work@z"]
        for include_trainees in (True, False):
            expected = []
            for area in areas:
                total = 0.0
                for bands in state.workers.get(area, {}).values():
                    total += sum(list(bands))
                if include_trainees:
                    for cohorts in state.trainees.get(area, {}).values():
                        for cohort in cohorts:
                            total += sum(list(cohort[1]))
                expected.append(total)
            self.assertEqual(state_reads.people_in_areas(state, areas, include_trainees).tolist(), expected)

    def test_people_in_areas_with_no_trades_numbered_is_zero(self):
        self.assertEqual(state_reads.people_in_areas(MarketState(), ["work@a"]).tolist(), [0.0])

    def test_scale_people_in_area_scales_workers_and_cohorts_of_that_area_only(self):
        state, other = awkward_state(), awkward_state()
        state_reads.scale_people_in_area(state, "work@a", 0.37)
        for bands in other.workers["work@a"].values():
            bands[:] = [count * 0.37 for count in bands]
        for cohorts in other.trainees["work@a"].values():
            for cohort in cohorts:
                cohort[1] = [count * 0.37 for count in cohort[1]]
        self.assertEqual(state.to_plain(), other.to_plain())
        state_reads.scale_people_in_area(state, "work@nowhere", 0.5)
        self.assertEqual(state.to_plain(), other.to_plain())

    def test_wages_in_view_order_lists_areas_and_trades_in_the_order_they_were_given(self):
        state = awkward_state()
        state.wages["work@a"]["baker"] = 0.0
        state.wages["work@c"]["smith"] = 5.0
        areas, trades, wages = state_reads.wages_in_view_order(state, 0.0)
        expected = [(area, trade, wage) for area, by_trade in state.wages.items() for trade, wage in by_trade.items() if wage > 0.0]
        self.assertEqual(list(zip(areas, trades, wages.tolist())), expected)

    def test_people_weighted_wage_by_area_equals_the_mean_over_the_views(self):
        state = awkward_state()
        found = state_reads.people_weighted_wage_by_area(state)
        expected = {}
        for area, wages in sorted(state.wages.items()):
            trades = sorted(wages)
            people = [math.fsum(state.workers.get(area, {}).get(trade, ())) for trade in trades]
            total = math.fsum(people)
            if total > 0.0:
                expected[area] = math.fsum(wages[trade] * count for trade, count in zip(trades, people)) / total
            else:
                expected[area] = math.fsum(wages[trade] for trade in trades) / len(trades)
        self.assertEqual(found, expected)
        self.assertNotIn("work@z", found)


class WageMeansByGroup(unittest.TestCase):
    def test_hours_then_people_then_plain_weights_per_group_over_kept_places(self):
        wage = numpy.array([1.0, 2.0, 4.0, 0.1, 0.2, 0.3, 5.0, 6.0])
        hours = numpy.array([1.0, 0.0, 3.0, 0.0, 0.0, 0.0, 0.0, 0.0])
        people = numpy.array([0.0, 0.0, 0.0, 2.0, 0.5, 0.1, 0.0, 0.0])
        kept = numpy.array([True, True, True, True, True, True, True, False])
        means, exists = state_reads.wage_means_by_group([3, 6, 8, 8], kept, wage, hours, people)
        self.assertEqual(exists.tolist(), [True, True, True, False])
        self.assertEqual(means.tolist()[:3], [math.fsum([1.0 * 1.0, 4.0 * 3.0]) / 4.0,
                                              math.fsum([0.1 * 2.0, 0.2 * 0.5, 0.3 * 0.1]) / math.fsum([2.0, 0.5, 0.1]), 5.0])


class RowNumbers(unittest.TestCase):
    def test_numbers_of_gives_the_place_among_sorted_names_and_minus_one_for_a_stranger(self):
        self.assertEqual(state_reads.numbers_of(["a", "c", "e"], ["c", "a", "b", "z", "e"]).tolist(), [1, 0, -1, -1, 2])
        self.assertEqual(state_reads.numbers_of([], ["a"]).tolist(), [-1])
        self.assertEqual(state_reads.numbers_of(["a"], []).tolist(), [])


class KernelsWithoutTheJit(unittest.TestCase):
    def test_exact_sum_of_an_empty_market_is_zero(self):
        found = state_read_kernels.hired_hours_at(numpy.array([0, -1]), numpy.array([0]), numpy.array([0]), numpy.zeros(0))
        self.assertEqual(found.tolist(), [0.0, 0.0])


if __name__ == "__main__":
    unittest.main()
