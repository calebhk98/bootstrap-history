"""The charge on the coin a run ties up (coin_cost.py), where the year's kernels reckon a run's cost: the plan
(`plan_year.plans_of`) plans no more runs with it than without, and the close (`close_run.close_producers`) pulls a
producer's expected prices toward a cost that carries it. Random economies of year_close_fixture, no game."""

QUICK_TOPIC = True

import copy
import dataclasses
import unittest
from unittest import mock

import numpy as np

from sim.economy import close_pack, coin_cost, plan_year, rule_sets
from sim.economy.ask_ceiling import AskAlternatives
from sim.economy.close_kernel import K_COIN_CHARGE
from sim.economy.close_run import close_producers
from sim.economy.year_arrays import YearArrays
from sim.economy.year_arrays_costs import refreshed
from sim.tests.year_close_fixture import MONEY, economy_of

CHARGED = "search with a charge on coin"      # the search set, a run's advance costing half as much again: large, to show
SHARE = 0.5
SEEDS = range(4)


def planned_runs(setup, record, view, area_map):
    arrays = refreshed(YearArrays.build(setup, record, area_map, view), setup, record, view)
    return np.array(plan_year.plans_of(setup, record, view, arrays, MONEY).runs)


class TheChargeInThePlan(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rule_sets.RULE_SETS[CHARGED] = dataclasses.replace(rule_sets.RULE_SETS[rule_sets.SEARCH], coin_charge=lambda _setup, _view: SHARE)
        cls.plain, cls.charged = [], []
        for seed in SEEDS:
            setup, record, view, _ledger, area_map = economy_of(seed, producer_count=60)
            cls.plain.append(planned_runs(setup, record, view, area_map))
            charged_setup = copy.copy(setup)
            charged_setup.rule_set = CHARGED
            cls.charged.append(planned_runs(charged_setup, record, view, area_map))

    @classmethod
    def tearDownClass(cls):
        del rule_sets.RULE_SETS[CHARGED]

    def test_no_producer_plans_more_runs_with_the_charge(self):
        for plain, charged in zip(self.plain, self.charged):
            self.assertTrue(np.all(charged <= plain * (1.0 + 1e-12)))

    def test_some_producers_plan_fewer_runs_with_the_charge(self):
        fewer = sum(int(np.sum(charged < plain * (1.0 - 1e-9))) for plain, charged in zip(self.plain, self.charged))
        self.assertGreater(fewer, 0)

    def test_the_search_set_charges_nothing(self):
        self.assertIs(rule_sets.RULE_SETS[rule_sets.SEARCH].coin_charge, coin_cost.no_charge)
        self.assertIs(rule_sets.RULE_SETS[rule_sets.CLEARING].coin_charge, coin_cost.charge_at_the_going_rate)


def band_above_cost(_alternatives, good, tile):
    """The width of the band above cost the buyers give, a fixed figure per good and tile in place of the year's prices."""
    return 1.0 + (len(good) + len(tile)) % 4 * 0.75


def closed(seed, charge):
    setup, record, view, ledger, area_map = economy_of(seed, producer_count=60)
    arrays = YearArrays.build(setup, record, area_map, view)
    constants = close_pack.constants_array()
    constants[K_COIN_CHARGE] = charge
    with mock.patch.object(AskAlternatives, "multiple", band_above_cost):
        return close_producers(arrays, close_pack.pack(setup, record, view, ledger, arrays), None, constants)


class TheChargeInTheClose(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pairs = [(closed(seed, 0.0), closed(seed, 1.0)) for seed in SEEDS]

    def test_no_expected_price_is_lower_with_the_charge(self):
        for plain, charged in self.pairs:
            both = plain.written & charged.written & ~plain.exited[:, None] & ~charged.exited[:, None]
            self.assertTrue(np.all(charged.new_expected[both] >= plain.new_expected[both] * (1.0 - 1e-12)))

    def test_some_expected_prices_are_higher_with_the_charge(self):
        higher = 0
        for plain, charged in self.pairs:
            both = plain.written & charged.written & ~plain.exited[:, None] & ~charged.exited[:, None]
            higher += int(np.sum(charged.new_expected[both] > plain.new_expected[both] * (1.0 + 1e-9)))
        self.assertGreater(higher, 0)

    def test_the_search_constants_carry_no_charge(self):
        self.assertEqual(close_pack.constants_array()[K_COIN_CHARGE], 0.0)
        self.assertEqual(close_pack.constants_array_for_clearing()[K_COIN_CHARGE], 1.0)


if __name__ == "__main__":
    unittest.main()
