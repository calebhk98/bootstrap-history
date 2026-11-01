"""SCENARIO (Complaint 473, speed): the rent-covering prices of the opening cost one full household solve, not one a
pass. The opening agrees with the one that re-solved the households at every covering pass (the loop is written out here
as the reference) within COVERAGE_TOLERANCE on prices, producers' capacities, households' purses and the posted rent."""
import dataclasses
import unittest
from unittest import mock

from sim.economy import opening, opening_rent, opening_runs
from sim.tests import economy_fixture as fixture

QUICK_TOPIC = True

# relative, float rounding only: on these fixtures the households' plans do not change with the covered prices (the hiring
# pattern and milled grains are discrete choices a price level a few per cent higher does not move), so the passes that
# keep the first solve's plans open the same economy as the ones that settled them again. Where a rent-bearing price
# did move a plan, the gap would be the second-order effect of that plan on a rent share already within
# COVERING_PRICE_TOLERANCE of its fixed point
COVERAGE_TOLERANCE = 1e-6


def resolved_every_pass(setup):
    """The opening as it was solved before: the whole household solve again at each covering price, until they stop moving."""
    current = setup
    for _pass in range(opening.COVERING_PRICE_PASSES):
        settled = opening._solve_opening(current)[0]
        record = settled[0]
        covered = opening_rent.covering_prices(
            setup.recipes, setup.opening_prices, setup.opening_wages, opening_rent.shares_of_revenue(current, record),
            {producer.recipe_id for producer in record.producers.values()}, opening_runs.mean_yields(setup, setup.recipes))
        if all(abs(price - current.opening_prices.get(good, 0.0)) <= opening.COVERING_PRICE_TOLERANCE * price
               for good, price in covered.items()):
            break
        current = dataclasses.replace(setup, opening_prices=covered)
    return settled[0]


def figures(setup, record):
    money = setup.currency_id
    return {"price": dict(record.memory.prices),
            "capacity": {agent_id: producer.capacity_runs for agent_id, producer in record.producers.items()},
            "purse": {agent_id: record.book.balance(agent_id, money) for agent_id in record.cohorts},
            "rent": dict(record.land_rent)}


def worst_relative_gap(reference, other):
    worst = 0.0
    for group, values in reference.items():
        assert set(values) == set(other[group]), group
        for key, value in values.items():
            worst = max(worst, abs(other[group][key] - value) / max(abs(value), 1e-9))
    return worst


class OpeningRentOneSolveTests(unittest.TestCase):
    def check(self, setup):
        reference = figures(setup, resolved_every_pass(setup))
        with mock.patch.object(opening, "_solve_opening", wraps=opening._solve_opening) as solve:
            record, _areas, _carriage = opening.open_economy(setup)
        self.assertEqual(solve.call_count, 1)
        self.assertLessEqual(worst_relative_gap(reference, figures(setup, record)), COVERAGE_TOLERANCE)

    def test_the_stationary_fixture_opens_in_one_solve_and_agrees_with_resolving_each_pass(self):
        self.check(fixture.stationary_setup())

    def test_the_small_fixture_with_rent_to_cover_opens_in_one_solve_and_agrees_with_resolving_each_pass(self):
        self.check(fixture.small_setup(land_per_run={fixture.FARM: 1.0}))

    def test_the_small_fixture_opens_in_one_solve_and_agrees_with_resolving_each_pass(self):
        self.check(fixture.small_setup())


if __name__ == "__main__":
    unittest.main()
