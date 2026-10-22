"""Complaint 497: the labour year's shared reads give the answers of the reads they replaced. Each fast path is
called beside a copy of the plain one on random built inputs; no game."""

QUICK_TOPIC = True

import random
import unittest

from sim.economy import household_hours_year, households_hours_offered
from sim.economy.labour_supply import HourSupply
from sim.economy.types import LabourOffer
from sim.labour.market import bonded_room, formation_bonded
from sim.labour.market.bonded_worth import carriage_from, cheapest_carriage
from sim.labour.market.import_cost import ImportCosts
from sim.labour.market.records import Bid, Clearing, MarketState, Route, YearInputs, YearReport


def plain_sold(held, offer, wage):
    """`sold_hours_schedule` as it was: the leisure term through `leisure_hours_kept`."""
    whole = held._hours.get(offer.worker, 0.0)
    if whole <= 0.0 or offer.hours <= 0.0:
        return 0.0
    plot = held.plot_hours_at.get(offer.worker)
    plot_kept = max(held.plan_hours.get(offer.worker, 0.0), plot(wage) if plot else 0.0)
    share = offer.hours / whole
    free = offer.hours - min(plot_kept + held.work_hours.get(offer.worker, 0.0), whole) * share
    eligible = max(0.0, free - max(0.0, held.plot_usable.get(offer.worker, 0.0) - plot_kept) * share)
    return free - households_hours_offered.leisure_hours_kept(eligible, wage, held.anchor_wage.get(offer.trade))


class TheSoldScheduleKeepsItsValues(unittest.TestCase):

    def test_hours_sold_equal_the_plain_formula_exactly(self):
        rng = random.Random(5)
        for _round in range(60):
            workers = ["w%d" % i for i in range(4)]
            offers = [LabourOffer(rng.choice(workers), rng.choice(["a", "b", "c"]), "vale", rng.choice([0.0, rng.uniform(10, 900)]),
                                  0.1) for _ in range(6)]
            held = HourSupply(
                offers=offers, plan_hours={w: rng.uniform(0, 200) for w in workers[:2]},
                work_hours={w: rng.uniform(0, 300) for w in workers[1:]},
                plot_hours_at={w: (lambda wage, scale=rng.uniform(100, 900): scale / (1.0 + max(wage, 0.0))) for w in workers[:3]},
                plot_usable={w: rng.uniform(0, 1500) for w in workers},
                anchor_wage={"a": rng.uniform(0.1, 3.0), "b": 0.0})       # "c" has none
            for offer in offers:
                schedule = held.sold_hours_schedule(offer)
                for wage in (-1.0, 0.0, 0.01, 0.7, 3.0, 50.0):
                    self.assertEqual(schedule(wage), plain_sold(held, offer, wage))


class ThePlotScheduleIsThePlainCall(unittest.TestCase):

    def test_hours_kept_at_a_wage_equal_the_plain_function_exactly(self):
        rng = random.Random(2)
        for _round in range(200):
            per_worker, marginal, usable, workers = (rng.choice([0.0, -1.0, rng.uniform(0.1, 2000.0)]) for _ in range(4))
            workers = abs(workers) + 1.0
            schedule = household_hours_year.plot_schedule(per_worker, marginal, usable, workers)
            for wage in (-1.0, 0.0, 1e-6, 0.3, 2.0, 80.0):
                self.assertEqual(schedule(wage), households_hours_offered.plot_hours_kept(per_worker, wage, marginal, usable) * workers)


class TheGroupedSharesAreTheMarketsShares(unittest.TestCase):

    def test_shares_for_every_market_equal_share_at_each(self):
        rng = random.Random(9)
        offers = [LabourOffer("w%d" % rng.randrange(5), rng.choice(["a", "b"]), rng.choice(["vale", "hill", "dale"]),
                              rng.choice([0.0, rng.uniform(10, 900)]), 0.1) for _ in range(30)]
        held = HourSupply(offers=offers, plan_hours={}, work_hours={}, plot_hours_at={}, plot_usable={},
                          anchor_wage={"a": 1.0, "b": 2.0})
        shares = held.shares()
        self.assertEqual(sorted(shares), sorted({(offer.trade, offer.area) for offer in offers}))
        for market, share in shares.items():
            plain = held.share_at(*market)
            for wage in (0.0, 0.3, 1.0, 9.0):
                self.assertEqual(share(wage), plain(wage))


class ImportCostsKeepTheirValues(unittest.TestCase):

    class Plain(ImportCosts):
        """`_fills` as it was: the spare hours of the sources worked out at every call."""

        def _fills(self, area, trade, sources, wanted, wage):
            own = self.hours_at(area, trade, wage)
            remaining = [max(0.0, self.everyone(other, trade) - self.wanted.get((other, trade), 0.0)) for other in sources]
            slack = 1e-9 * (1.0 + abs(wanted))
            to_come = sum(remaining)
            if own + to_come < wanted - slack:
                return False
            fetched = 0.0
            for other, cap in zip(sources, remaining):
                to_come -= cap
                fetched += max(0.0, self.hours_at(other, trade, wage) - self.wanted.get((other, trade), 0.0))
                if own + fetched >= wanted:
                    return True
                if own + fetched + to_come < wanted - slack:
                    return False
            return own + fetched >= wanted

    def test_the_wage_of_fetched_hands_is_the_plain_search(self):
        rng = random.Random(11)
        for _round in range(40):
            areas = ["a%d" % i for i in range(5)]
            routes = {area: [Route(other, rng.uniform(0, 200)) for other in areas if other != area and rng.random() < 0.7]
                      for area in areas}
            state = MarketState(workers={area: {"digger": [rng.uniform(0, 40), rng.uniform(0, 40)]} for area in areas})
            state.wages = {area: {"digger": rng.uniform(0.5, 3.0)} for area in areas if rng.random() < 0.9}
            bids = [Bid("e%d" % i, "digger", rng.choice(areas), rng.uniform(100, 6000), rng.uniform(1, 8)) for i in range(7)]
            shares = {("digger", area): (lambda wage, base=rng.uniform(0.3, 1.0): min(1.0, base * (0.5 + wage / 6.0)))
                      for area in areas if rng.random() < 0.6}
            inputs = YearInputs(trades={}, bids=bids, subsistence_per_worker_year={area: 100.0 for area in areas},
                                hours_per_worker_year=100.0, discount_rate=0.03, career_years=30.0, routes=routes,
                                hours_share_at=shares)
            fast, plain = ImportCosts(state, inputs), self.Plain(state, inputs)
            for area in areas:
                self.assertEqual(fast.wage(area, "digger"), plain.wage(area, "digger"))


class BondedPurchaseReadsKeepTheirValues(unittest.TestCase):

    def test_buyers_read_from_the_grouped_bids_are_those_read_from_all_of_them(self):
        rng = random.Random(3)
        for _round in range(40):
            bids = [Bid("e%d" % rng.randrange(6), rng.choice(["x", "y"]), rng.choice(["p", "q"]), rng.choice([0.0, rng.uniform(1, 500)]),
                        2.0) for _ in range(20)]
            hired = {"e%d" % i: rng.uniform(0, 300) for i in range(6) if rng.random() < 0.5}
            clearing = Clearing(trade="x", area="p", wage=1.0, hours_offered=0.0, hours_wanted=0.0, hours_hired=0.0,
                                hired_by_employer=hired, paid_by_employer={}, average_wage=1.0, target_wage=rng.uniform(0, 2))
            room = {"e%d" % i: rng.uniform(-5, 50) for i in range(6) if rng.random() < 0.5}
            hours = {}
            for bid in bids:
                if bid.area == "p" and bid.trade == "x" and bid.hours > 0.0:
                    hours[bid.employer] = hours.get(bid.employer, 0.0) + bid.hours
            expected = []
            for employer in sorted(hours):
                vacant = max(0.0, hours[employer] - hired.get(employer, 0.0))
                line = vacant * max(0.0, clearing.heading_wage)
                free = max(0.0, room.get(employer, 0.0))
                if vacant > 0.0 and line + free > 0.0:
                    expected.append(bonded_room.Buyer(employer, vacant, line, free))
            self.assertEqual(bonded_room.buyers_in(bonded_room.hours_by_market(bids), clearing, room), expected)

    def test_purchases_sharing_a_memo_equal_purchases_each_with_their_own(self):
        routes = {"p": [Route("q", 40.0)], "q": [Route("r", 25.0), Route("p", 40.0)], "r": [Route("p", 90.0)]}
        bids = [Bid("forge", "fitter", area, 50000.0, 3.0) for area in ("p", "q", "r")]
        inputs = YearInputs(trades={}, bids=bids, subsistence_per_worker_year={}, hours_per_worker_year=2000.0,
                            discount_rate=0.05, career_years=40.0, routes=routes, bondage_allowed=frozenset({"p", "q", "r"}),
                            bonded_for_sale={area: {"fitter": 30.0} for area in ("p", "q", "r")},
                            ask_floor_per_worker_year={area: 100.0 for area in ("p", "q", "r")}, outlay_room={"forge": 1.0e9})
        index = {(area, "fitter"): Clearing(trade="fitter", area=area, wage=1.0, hours_offered=0.0, hours_wanted=50000.0,
                                            hours_hired=0.0, hired_by_employer={}, paid_by_employer={}, average_wage=1.0,
                                            target_wage=3.0) for area in ("p", "q", "r")}

        def run(shared):
            pool = {area: {"fitter": 30.0} for area in ("p", "q", "r")}
            report, room, memo = YearReport(), dict(inputs.outlay_room), {}
            for area in ("p", "q", "r", "p"):
                formation_bonded.buy(MarketState(), inputs, index, area, "fitter", 12.0, pool, report, room,
                                     memo if shared else {})
            return [(lot.origin, lot.people, lot.price) for lot in report.bonded_lots], room

        self.assertTrue(run(True)[0])
        self.assertEqual(run(True), run(False))
        self.assertEqual(cheapest_carriage(routes, "p", "r"), 65.0)

    def test_one_search_from_an_origin_gives_the_carriage_to_every_destination(self):
        rng = random.Random(21)
        for _round in range(30):
            areas = ["a%d" % i for i in range(9)]
            routes = {area: [Route(other, rng.choice([0.0, rng.uniform(-5, 80)])) for other in areas if rng.random() < 0.3]
                      for area in areas if rng.random() < 0.9}
            for origin in areas:
                tree = carriage_from(routes, origin)
                for destination in areas:
                    self.assertEqual(tree.get(destination), cheapest_carriage(routes, origin, destination))


if __name__ == "__main__":
    unittest.main()
