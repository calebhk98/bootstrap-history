"""Complaint 545: the opening sizes producers for what households do not grow themselves."""

import dataclasses
import unittest
from unittest import mock

from sim.economy import opening
from sim.economy.economy import Economy
from sim.tests import economy_fixture as fixture

TOLERANCE = 0.1      # relative: the opening's hired-hours estimate is a stand-in for the placed producers (545)


def setup_with_plots():
    return fixture.small_setup(land_per_run={fixture.FARM: 1.0})


def floor_units(setup):
    need = next(each for each in setup.basket.needs if each.need_id == fixture.FOOD)
    return need.subsistence_per_person * sum(setup.opening_population_by_tile.values())


def opening_grown(setup):
    """Need units grown at the opening, as the last final demand struck saw them."""
    seen = {}
    original = opening._final_demand

    def spy(*arguments):
        seen["grown"] = arguments[4] if len(arguments) > 4 else None
        return original(*arguments)

    with mock.patch.object(opening, "_final_demand", spy):
        record, _areas, _carriage = opening.open_economy(setup)
    total = sum(units.get(fixture.FOOD, 0.0) for units in (seen["grown"] or {}).values())
    return record, total


def first_year_grown(setup):
    economy = Economy(setup)
    seen = {}
    original = Economy._grow_own

    def spy(self, offers, ledger, harvest_factor=1.0, kept=None):
        original(self, offers, ledger, harvest_factor, kept)
        seen["units"] = {agent: dict(units) for agent, units in ledger.grown_units.items()}

    with mock.patch.object(Economy, "_grow_own", spy):
        economy.step(fixture.quiet_year(setup))
    return sum(units.get(fixture.FOOD, 0.0) for units in seen.get("units", {}).values())


class OpeningGrowsItsOwnTests(unittest.TestCase):
    def test_final_demand_for_the_floor_food_is_less_what_households_grow(self):
        without = opening.open_economy(fixture.small_setup())[0].opening_basket.get(fixture.GRAIN, 0.0)
        setup = setup_with_plots()
        record, grown = opening_grown(setup)
        self.assertGreater(grown, 0.0)
        self.assertLess(record.opening_basket.get(fixture.GRAIN, 0.0), without)
        # at least what they grow: their lower income buys less besides
        self.assertGreaterEqual(without - record.opening_basket.get(fixture.GRAIN, 0.0), grown * (1.0 - TOLERANCE))

    def test_self_grown_share_and_market_floor_at_the_opening_are_the_first_years(self):
        setup = setup_with_plots()
        floor = floor_units(setup)
        _record, at_opening = opening_grown(setup)
        in_year = first_year_grown(setup)
        self.assertGreater(in_year, 0.0)
        self.assertAlmostEqual(at_opening / floor, in_year / floor, delta=TOLERANCE)
        self.assertAlmostEqual(floor - at_opening, floor - in_year, delta=TOLERANCE * floor)

    def test_a_partly_self_fed_economy_agrees_with_the_first_year(self):
        # few hours offered: the plots feed part of the floor and the market the rest
        setup = dataclasses.replace(setup_with_plots(), working_hours_per_year=120.0)
        floor = floor_units(setup)
        _record, at_opening = opening_grown(setup)
        in_year = first_year_grown(setup)
        self.assertTrue(0.0 < in_year / floor < 1.0)
        self.assertAlmostEqual(at_opening / floor, in_year / floor, delta=TOLERANCE)
        self.assertAlmostEqual(floor - at_opening, floor - in_year, delta=TOLERANCE * floor)

    def test_a_scenario_without_plots_is_unchanged(self):
        record, grown = opening_grown(fixture.small_setup())
        self.assertEqual(grown, 0.0)


if __name__ == "__main__":
    unittest.main()
