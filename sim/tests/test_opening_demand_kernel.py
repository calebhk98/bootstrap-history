"""Numba port, the opening's final demand: `opening_demand.OpeningDemand` (the kernel over every cohort) agrees with the old
per-cohort path (`households.goods_orders` through `OwnPlots.resting_orders`, then `goods_market.quantity_at` of each bid),
kept here as `reference_final_demand`, on random cohorts, needs, goods, prices and plots; no game.

The kernel sums exactly where the old code used `math.fsum` (and compensates where it used `sum`), because the bids
at the edge of what a cohort can afford exist or not by the last bit of a sum; what is left is the order of a few plain
sums and `pow`, so figures agree to a tight relative tolerance, not always bit for bit. The old path searches for a purse in
at most three passes and so can jump under a one-ulp change of its input: a case where it does is no test of the kernel
and is skipped (`is_stable`), and most cases must be compared."""

QUICK_TOPIC = True

import math
import random
import types
import unittest

from sim.economy import households, opening_demand, opening_own
from sim.economy.goods_market import quantity_at
from sim.economy.households_cohort import Cohort
from sim.economy.opening_own import OwnPlots
from sim.economy.types import GoodSpec
from sim.tests.economy_view_defaults import ViewDefaults
from sim.world import need_basket

TOLERANCE = 1e-12
NEED_DATA = {
    "needs": {
        "food": {"surplus_budget_share": 0.4, "subsistence_per_capita_per_year": 200.0, "satiation_per_capita_per_year": 450.0},
        "cloth": {"surplus_budget_share": 0.2, "subsistence_per_capita_per_year": 4.0},
        "light": {"surplus_budget_share": 0.1},
        "tools": {"surplus_budget_share": 0.2},
        "ornament": {"surplus_budget_share": 0.1, "satiation_per_capita_per_year": 0.4},
    },
    "goods": {
        "bread": {"satisfies": {"food": 1.0}},
        "millet": {"satisfies": {"food": 0.7}},
        "wool": {"satisfies": {"cloth": 1.0}},
        "linen": {"satisfies": {"cloth": 1.5}},
        "tallow": {"satisfies": {"light": 1.0}, "quality": {"light": {"factor": 0.7}}},
        "oil": {"satisfies": {"light": 1.3}, "quality": {"light": {"factor": 0.85}}},
        "wax": {"satisfies": {"light": 0.9}},
        "hoe": {"satisfies": {"tools": 1.0}},
        "gold": {"satisfies": {"ornament": 1.0}},
    },
}
SPECS = {name: GoodSpec(name, mass, spoilage, life, "x") for name, mass, spoilage, life in (
    ("bread", 1.0, 0.1, 0.0), ("millet", 1.0, 0.05, 0.0), ("wool", 1.0, 0.0, 0.0), ("linen", 1.0, 0.0, 0.0),
    ("tallow", 1.0, 0.1, 0.0), ("oil", 1.0, 0.0, 0.0), ("wax", 1.0, 0.0, 0.0), ("hoe", 2.0, 0.0, 10.0),
    ("gold", 0.05, 0.0, 200.0))}
TILES = ("north", "south")


class View(ViewDefaults):
    year = 1

    def __init__(self, prices, held, rate):
        self.prices, self.held, self.rate = prices, held, rate

    def price(self, good, area):
        return self.prices.get(good)

    def usual_price(self, good, area):
        return None

    def interest_rate(self, currency):
        return self.rate

    def area_of(self, good, tile):
        return "area:" + good

    def currency_of(self, area):
        return "coin"

    def stock(self, agent, good, tile):
        return self.held.get((agent, good), 0.0)


def random_world(rng, need_data=None):
    """The need data is an argument, not a patched module attribute: a topic module can be loaded twice in one process (as another topic's helper, then as itself), and a patch on one copy does not reach a function of the other."""
    basket = need_basket.make_basket(NEED_DATA if need_data is None else need_data, {})
    prices = {"bread": rng.uniform(0.2, 0.6), "millet": rng.uniform(0.15, 0.7), "wool": rng.uniform(2.0, 9.0),
              "linen": rng.uniform(3.0, 12.0), "tallow": rng.uniform(0.5, 2.0), "oil": rng.uniform(0.8, 3.0),
              "wax": rng.uniform(1.0, 6.0), "hoe": rng.uniform(5.0, 40.0), "gold": rng.uniform(300.0, 900.0)}
    if rng.random() < 0.2:
        del prices["millet"]
    cohorts, held = [], {}
    for tile in TILES:
        for index in range(rng.randint(1, 3)):
            people = rng.uniform(200.0, 5000.0)
            income = people * rng.uniform(40.0, 400.0)
            agent = "household:%s:%d" % (tile, index)
            cohorts.append(Cohort(
                agent, tile, index, people, people * 0.4, 0.3, expected_inflation=rng.choice([0.0, 0.03]),
                cash_target=rng.choice([0.0, income * rng.uniform(0.0, 0.5)]),
                last_year_income=income, share_wealth=rng.choice([None, income * rng.uniform(0.5, 6.0)]),
                expected_spending=rng.choice([0.0, income * rng.uniform(0.6, 1.4)]),
                expected_floor_cost=rng.choice([0.0, income * rng.uniform(0.2, 0.7)])))
            if rng.random() < 0.3:
                held[(agent, "bread")] = rng.uniform(0.0, 300.0)
            if rng.random() < 0.08:
                held[(agent, "hoe")] = rng.uniform(0.0, 40.0)
    return basket, View(prices, held, rng.choice([0.04, 0.08, None])), cohorts


def parts_of(basket, view, cohorts):
    parts = []
    for cohort in cohorts:
        shared = {}
        parts.append((cohort, basket, households.need_prices(basket, view, cohort.tile), shared))
    return parts


def random_units(rng, cohorts, basket):
    units = {}
    for cohort in cohorts:
        grown = {}
        for need in basket.needs:
            if need.subsistence_per_person > 0.0 and rng.random() < 0.5:
                grown[need.need_id] = need.subsistence_per_person * cohort.people * rng.uniform(0.0, 1.3)
        units[cohort.agent_id] = grown
    return units


def plots_of(units):
    """An `OwnPlots` whose plots grow the given units (the plot rules have their own tests)."""
    own = OwnPlots.__new__(OwnPlots)
    own.in_kind, own.share_hired = 0.0, 0.0
    own.grown, own.hectares, own.sold = {}, {}, {}
    own.grow = lambda record, cohort, priced, own_work=None: units[cohort.agent_id]
    own.own_work_hours = lambda record, cohort, priced: 0.0
    return own


def reference_final_demand(parts, view, own):
    """The old path: each cohort's orders through `resting_orders`, each bid's quantity at the price the view quotes."""
    final = {}
    for cohort, basket, priced, shared in sorted(parts, key=lambda part: part[0].agent_id):
        income = cohort.last_year_income

        def make(cash=income, grown_units=None, cohort=cohort, basket=basket, priced=priced, shared=shared, income=income):
            return households.goods_orders(cohort, view, cash, income, basket, SPECS, priced, shared_store=shared,
                                           stationary_durables=True, grown_units=grown_units)
        for bid in own.resting_orders(None, cohort, income, basket, priced, make).bids:
            price = view.price(bid.good, bid.area)
            if price:
                demand = final.setdefault(cohort.tile, {})
                demand[bid.good] = demand.get(bid.good, 0.0) + quantity_at(bid, price)
    return final


def kernel_final_demand(parts, view, own, cohorts):
    packed = opening_demand.OpeningDemand(parts, view, SPECS, own)
    record = types.SimpleNamespace(cohorts={cohort.agent_id: cohort for cohort in cohorts})
    return packed, packed.final_demand(record)


def is_stable(parts, view, units, cohorts, final):
    """Whether the old path gives the same demand when every income is nudged by a relative 1e-12."""
    import dataclasses
    nudged_cohorts = [dataclasses.replace(cohort, last_year_income=cohort.last_year_income * (1.0 + 1e-12)) for cohort in cohorts]
    nudged_parts = [(nudged, basket, priced, {}) for nudged, (_c, basket, priced, _s) in zip(nudged_cohorts, parts)]
    nudged = reference_final_demand(nudged_parts, view, plots_of(units))
    return all(abs(nudged.get(tile, {}).get(good, 0.0) - quantity) <= 1e-6 * max(demand.values())
               for tile, demand in final.items() for good, quantity in demand.items())


class FinalDemandAgreesTests(unittest.TestCase):
    def test_kernel_and_old_path_agree_on_random_cohorts(self):
        rng = random.Random(7)
        compared = skipped = 0
        for _case in range(60):
            basket, view, cohorts = random_world(rng)
            units = random_units(rng, cohorts, basket)
            parts = parts_of(basket, view, cohorts)
            packed_parts = parts_of(basket, view, cohorts)
            expected = reference_final_demand(parts, view, plots_of(units))
            if not is_stable(parts, view, units, cohorts, expected):
                skipped += 1
                continue
            packed, got = kernel_final_demand(packed_parts, view, plots_of(units), cohorts)
            if not packed.supported:
                skipped += 1
                continue
            self.assertEqual(list(got), list(expected), "tiles in the order the old path met them")
            for tile, demand in expected.items():
                # a bid whose budget is a few ulps either side of nothing exists in one path and not the other: its
                # quantity is nothing, and only the goods that count are compared, in the order they were met
                significant = max(demand.values())
                counts = lambda found: [good for good, quantity in found.items() if quantity > 1e-9 * significant]
                self.assertEqual(counts(got[tile]), counts(demand), "goods in the order the old path met them")
                for good, quantity in demand.items():
                    self.assertAlmostEqual(got[tile].get(good, 0.0), quantity, delta=TOLERANCE * significant,
                                           msg="%s %s" % (tile, good))
            compared += 1
        self.assertGreaterEqual(compared, 40, "most cases are compared (%d skipped)" % skipped)

    def test_the_spending_in_kind_agrees(self):
        rng = random.Random(11)
        checked = 0
        for _case in range(30):
            basket, view, cohorts = random_world(rng)
            units = random_units(rng, cohorts, basket)
            parts = parts_of(basket, view, cohorts)
            reference_own = plots_of(units)
            expected = reference_final_demand(parts, view, reference_own)
            if not is_stable(parts, view, units, cohorts, expected):
                continue
            own = plots_of(units)
            packed, _got = kernel_final_demand(parts_of(basket, view, cohorts), view, own, cohorts)
            if not packed.supported:
                continue
            self.assertAlmostEqual(own.in_kind, reference_own.in_kind, delta=TOLERANCE * max(1.0, abs(reference_own.in_kind)))
            checked += 1
        self.assertGreaterEqual(checked, 15)

    def test_a_durable_in_use_in_the_store_is_left_to_the_old_path(self):
        rng = random.Random(3)
        basket, view, cohorts = random_world(rng)
        view.held[(cohorts[0].agent_id, "gold")] = 5.0
        packed = opening_demand.OpeningDemand(parts_of(basket, view, cohorts), view, SPECS, plots_of({}))
        self.assertFalse(packed.supported)


class DurableBidsAgreeTests(unittest.TestCase):
    def test_the_bids_for_durables_that_serve_needs_are_the_ones_goods_orders_makes_at_cash_equal_to_income(self):
        rng = random.Random(21)
        compared = 0
        for _case in range(40):
            basket, view, cohorts = random_world(rng)
            parts = parts_of(basket, view, cohorts)
            packed = opening_demand.OpeningDemand(parts_of(basket, view, cohorts), view, SPECS, plots_of({}))
            if not packed.supported:
                continue
            record = types.SimpleNamespace(cohorts={cohort.agent_id: cohort for cohort in cohorts})
            expected = []
            for cohort, basket, priced, shared in sorted(parts, key=lambda part: part[0].agent_id):
                orders = households.goods_orders(cohort, view, cohort.last_year_income, cohort.last_year_income, basket, SPECS,
                                                 priced, shared_store=shared, stationary_durables=False)
                expected.extend((cohort.agent_id, bid.good, bid.floor_quantity + bid.flexible_quantity) for bid in orders.bids
                                if bid.priority != 2 and SPECS[bid.good].service_life_years > 0.0)
            got = [(cohort.agent_id, good, quantity) for cohort, good, quantity in packed.durable_bids(record)]
            self.assertEqual([(who, good) for who, good, _q in got], [(who, good) for who, good, _q in expected])
            for (_w, _g, found), (_w2, _g2, wanted) in zip(got, expected):
                self.assertAlmostEqual(found, wanted, delta=TOLERANCE * max(abs(wanted), 1.0))
            compared += 1
        self.assertGreaterEqual(compared, 20)


if __name__ == "__main__":
    unittest.main()
