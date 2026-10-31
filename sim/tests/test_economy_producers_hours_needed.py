"""`labour_state.producers_hours_needed`: each labour area's producers need, of each trade, the hours of the runs they expect
to sell, and the mint needs the hours its capacity takes in the capital's area (an England with no engraver in the capital's
labour area never struck a coin). Hand-written producers and recipes; the mint's two figures are recorders."""
QUICK_TOPIC = True

import types
import unittest
from unittest import mock

from sim.economy import labour_state
from sim.economy.setup import labour_area
from sim.economy.types import Recipe

CAPITAL = "capital"
FIELD = "field"
CURRENCY = object()


def setup():
    recipes = {"wheat": Recipe("wheat", {"grain": 1.0}, {}, {"farmer": 100.0}),
               "coin": Recipe("coin", {"coin": 1.0}, {}, {"engraver": 50.0, "smith": 10.0})}
    return types.SimpleNamespace(recipes=recipes, capital_tile=CAPITAL)


def record(*producers):
    return types.SimpleNamespace(
        currency=CURRENCY,
        producers={name: types.SimpleNamespace(recipe_id=recipe, tile=tile, expected_sales=sales, crew_runs={})
                   for name, recipe, tile, sales in producers})


def needed(the_record, mint_hours, capacity=12.0):
    with mock.patch.object(labour_state.mint, "capacity_fine_kilograms", return_value=capacity) as figure, \
            mock.patch.object(labour_state.mint_labour, "capacity_hours", return_value=mint_hours) as hours:
        result = labour_state.producers_hours_needed(setup(), the_record)
    return result, figure, hours


class ProducersHoursNeededTests(unittest.TestCase):
    def test_a_producer_needs_each_trades_hours_per_run_times_the_runs_it_expects_to_sell(self):
        result, _figure, _hours = needed(record(("a", "wheat", FIELD, 3.0), ("b", "wheat", FIELD, 2.0)), {})
        self.assertEqual(result[labour_area(FIELD)], {"farmer": 500.0})

    def test_producers_in_two_places_need_their_own_areas_hours(self):
        result, _figure, _hours = needed(record(("a", "wheat", FIELD, 1.0), ("b", "wheat", "town", 4.0)), {})
        self.assertEqual((result[labour_area(FIELD)], result[labour_area("town")]), ({"farmer": 100.0}, {"farmer": 400.0}))

    def test_the_mints_hours_are_needed_in_the_capitals_area(self):
        result, _figure, _hours = needed(record(("a", "wheat", FIELD, 1.0)), {"engraver": 600.0, "smith": 120.0})
        self.assertEqual(result[labour_area(CAPITAL)], {"engraver": 600.0, "smith": 120.0})

    def test_the_mints_hours_add_to_a_producers_in_the_same_trade_and_area(self):
        result, _figure, _hours = needed(record(("a", "coin", CAPITAL, 2.0)), {"engraver": 600.0})
        self.assertEqual(result[labour_area(CAPITAL)], {"engraver": 700.0, "smith": 20.0})

    def test_the_mint_is_asked_for_the_hours_of_the_capacity_it_can_strike(self):
        _result, figure, hours = needed(record(), {}, capacity=12.0)
        hours.assert_called_once()
        self.assertEqual(hours.call_args.args[2], 12.0)
        self.assertEqual(hours.call_args.args[1], CURRENCY)
        self.assertEqual(figure.call_count, 1)


if __name__ == "__main__":
    unittest.main()
