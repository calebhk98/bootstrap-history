"""Numba port, labour clearing: the head of every market's year (`clearing_kernel.market_heads`: fetched hands, the
reservation wage, the ceiling, the wage before the hiring rounds and where it heads) agrees with the plain functions
kept in `clearing._plain_head`, on random built markets with routes, bids and hours schedules; no game.

The kernel sums left to right where the plain code used Python's compensated `sum`, so figures agree to a relative
tolerance. The searches (fetched hands, the supply target) are bisections on a rising total: a case where the plain search
itself lands on a different side of a step under a one-ulp nudge of its input is no test of the kernel and is skipped;
most cases must be compared."""

QUICK_TOPIC = True

import math
import random
import unittest

from sim.economy import household_hours_year
from sim.economy.labour_supply import HourSupply
from sim.economy.types import LabourOffer
from sim.labour.market import clearing, clearing_arrays, trades
from sim.labour.market.import_cost import ImportCosts
from sim.labour.market.records import EmployerHoursBid, MarketState, Route, YearInputs, copy_state

TOLERANCE = 1e-9
AREAS = ["a%d" % i for i in range(6)]
TRADE_DATA = {"dig": {"family": "earth", "training_years": 0, "fallback": True},
              "smith": {"family": "metal", "training_years": 4, "difficulty": 0.5, "fatality_risk_per_year": 0.002},
              "mason": {"family": "earth", "training_years": 2, "difficulty": 0.2},
              "seer": {"family": "mind", "training_years": 7, "difficulty": 1.0, "fatality_risk_per_year": 0.0}}
SPECS = trades.trade_specs(TRADE_DATA)


def random_case(rng, scheduled):
    workers = {area: {trade: [rng.choice([0.0, rng.uniform(1.0, 400.0)]) for _band in range(5)]
                      for trade in SPECS if rng.random() < 0.8} for area in AREAS}
    state = MarketState(workers=workers)
    for area in AREAS:
        for trade in SPECS:
            if rng.random() < 0.7:
                state.wages.setdefault(area, {})[trade] = rng.uniform(0.3, 3.0)
            if rng.random() < 0.4:
                state.asks.setdefault(area, {})[trade] = rng.uniform(0.8, 1.5)
    bids = [EmployerHoursBid("e%d" % rng.randint(0, 5), rng.choice(list(SPECS)), rng.choice(AREAS), rng.uniform(100.0, 40000.0),
                             rng.uniform(0.4, 6.0)) for _ in range(rng.randint(5, 40))]
    routes = {area: [Route(other, rng.uniform(0.0, 800.0)) for other in AREAS if other != area and rng.random() < 0.5]
              for area in AREAS}
    inputs = YearInputs(trades=SPECS, bids=bids, subsistence_per_worker_year={area: rng.uniform(150.0, 600.0) for area in AREAS[:-1]},
                        hours_per_worker_year=300.0, discount_rate=0.03, career_years=30.0, routes=routes,
                        ask_floor_per_worker_year={area: rng.uniform(50.0, 300.0) for area in AREAS[:3]},
                        value_of_life_years_of_income=rng.uniform(0.0, 20.0))
    if scheduled:
        offers = []
        for index in range(rng.randint(10, 60)):
            offers.append(LabourOffer("w%d" % index, rng.choice(list(SPECS)), rng.choice(AREAS), rng.uniform(50.0, 900.0), 0.1))
        names = ["w%d" % index for index in range(len(offers))]
        plots = {name: household_hours_year.plot_schedule(rng.uniform(100, 2000), rng.uniform(0.0, 3.0), rng.uniform(0, 1500),
                                                          rng.uniform(1, 30)) for name in names[::2]}
        supply = HourSupply(offers=offers, plan_hours={name: rng.uniform(0, 100) for name in names[::3]},
                            work_hours={name: rng.uniform(0, 100) for name in names[1::3]}, plot_hours_at=plots)
        inputs.hours_sold_at = supply.schedules()
    return state, inputs


def markets_of(state, inputs):
    found = {(bid.trade, bid.area) for bid in inputs.bids}
    found.update((trade, area) for area, by_trade in state.workers.items() for trade, bands in by_trade.items() if sum(bands) > 0.0)
    return sorted(found)


def plain_heads(state, inputs, markets, bids_by_market):
    costs = ImportCosts(state, inputs)
    return [clearing._plain_head(state, inputs, trade, area, bids_by_market.get((trade, area), []), costs)
            for trade, area in markets]


def kernel_heads(state, inputs, markets, bids_by_market):
    costs = ImportCosts(state, inputs)
    found = clearing_arrays.run_heads(clearing_arrays.pack_heads(state, inputs, markets, bids_by_market, costs,
                                                                clearing.WAGE_SHARE_CLOSED_PER_YEAR))
    return [tuple(clearing._kernel_head(tuple(row[1:]))) if row[0] else None for row in found.tolist()]


def grouped(inputs):
    by_market = {}
    for bid in inputs.bids:
        if bid.hours > 0.0 and bid.trade in inputs.trades:
            by_market.setdefault((bid.trade, bid.area), []).append(bid)
    return by_market


def same(left, right):
    if left is None or right is None:
        return left is right
    return abs(left - right) <= TOLERANCE * max(1.0, abs(left), abs(right)) or (math.isinf(left) and left == right)


def nudged(state, inputs):
    """The case with every wage and every worker count one ulp higher."""
    again = MarketState(workers={a: {t: [math.nextafter(c, math.inf) for c in b] for t, b in by.items()} for a, by in state.workers.items()},
                        wages={a: {t: math.nextafter(w, math.inf) for t, w in by.items()} for a, by in state.wages.items()},
                        asks=state.asks)
    return again


class MarketHeadsAgreeWithThePlainFunctions(unittest.TestCase):

    def compare(self, scheduled, seed):
        rng = random.Random(seed)
        compared = skipped = 0
        for _case in range(30):
            state, inputs = random_case(rng, scheduled)
            markets = markets_of(state, inputs)
            by_market = grouped(inputs)
            plain = plain_heads(state, inputs, markets, by_market)
            again = plain_heads(nudged(state, inputs), inputs, markets, by_market)
            fast = kernel_heads(state, inputs, markets, by_market)
            for market, want, other, got in zip(markets, plain, again, fast):
                if (want is None) != (got is None):
                    self.fail("outside option disagrees for %s" % (market,))
                if want is None:
                    continue
                if not all(same(a, b) for a, b in zip(want, other) if a is not None and b is not None):
                    skipped += 1       # the plain search itself moves under a one-ulp nudge
                    continue
                compared += 1
                for name, left, right in zip("wage target goal offered reservation base lowest ceiling held".split(), want, got):
                    self.assertTrue(same(left, right), "%s of %s: plain %r, kernel %r" % (name, market, left, right))
        self.assertGreater(compared, 10 * skipped)
        self.assertGreater(compared, 300)

    def test_every_worker_sells_a_whole_year(self):
        self.compare(False, 1)

    def test_hours_sold_follow_a_schedule(self):
        self.compare(True, 2)

    def test_every_market_cleared_through_the_kernel_equals_the_plain_path(self):
        """`clear_all` with the heads from the kernel and with the heads from the plain functions give the same clearings."""
        rng = random.Random(9)
        compared = 0
        for _case in range(12):
            state, inputs = random_case(rng, _case % 2 == 1)
            fast = clearing.clear_all(copy_state(state), inputs)
            real = clearing_arrays.kernel_applies
            clearing_arrays.kernel_applies = lambda _inputs: False
            try:
                plain = clearing.clear_all(copy_state(state), inputs)
            finally:
                clearing_arrays.kernel_applies = real
            self.assertEqual([(each.trade, each.area) for each in fast], [(each.trade, each.area) for each in plain])
            for got, want in zip(fast, plain):
                for name in ("wage", "hours_offered", "hours_wanted", "hours_hired", "target_wage", "hours_held"):
                    self.assertTrue(same(getattr(got, name), getattr(want, name)) or abs(getattr(got, name) - getattr(want, name)) <= 1e-6 * max(1.0, abs(getattr(want, name))),
                                    "%s of %s: kernel %r, plain %r" % (name, (want.trade, want.area), getattr(got, name), getattr(want, name)))
                compared += 1
        self.assertGreater(compared, 100)

    def test_a_replaced_fetch_search_is_called_through_the_plain_path(self):
        state, inputs = random_case(random.Random(3), True)
        self.assertTrue(clearing_arrays.kernel_applies(inputs))
        inputs.fetch_wage = lambda *arguments: None
        self.assertFalse(clearing_arrays.kernel_applies(inputs))

    def test_a_schedule_that_is_not_packed_is_called_through_the_plain_path(self):
        state, inputs = random_case(random.Random(4), True)
        inputs.hours_sold_at[("dig", "a0")] = lambda wage: 5.0
        self.assertFalse(clearing_arrays.kernel_applies(inputs))


if __name__ == "__main__":
    unittest.main()
