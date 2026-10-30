"""`seller_offers.strategic_offers` prepares the buyers' side of a market when a seller first searches against it,
not before: the offers and the unit costs it hands back equal those of the version that always prepared it, and a
market where no seller searches builds none. Producers are stubbed (their unit cost and workshop count); the
search itself is the real one."""

QUICK_TOPIC = True

import contextlib
import dataclasses
import math
import random
import unittest
from types import SimpleNamespace
from unittest import mock

from sim.economy import goods_market, seller_offers, seller_pricing
from sim.economy.ask_adjust import GOODS_ASK_ADJUSTMENT_SHARE_PER_YEAR
from sim.economy.types import Bid, Offer

GOOD, AREA = "grain", "area"


def strategic_offers_always_preparing(setup, record, view, bids, offers, last_price, costs=None):
    offers = list(offers)
    if not bids or not offers:
        return offers
    good = offers[0].good
    book = seller_offers.merged_bids(bids, good)
    buyers = goods_market.Buyers(book, last_price)
    for index in sorted(range(len(offers)), key=lambda each: (offers[each].seller, offers[each].tile)):
        offer = offers[index]
        if offer.quantity <= 0.0:
            continue
        cost = seller_offers.unit_cost(setup, record, view, offer)
        if costs is not None:
            costs[(offer.seller, offer.tile)] = cost
        if cost is None:
            continue
        value = seller_offers.unit_value(offer, cost)
        rivals = offers[:index] + offers[index + 1:]
        ask = max(offer.reservation_price, 0.0)
        if seller_offers.stands_for_many(record, offer):
            continue
        limit = cost * seller_offers.ask_band_multiple(setup, offer) if math.isfinite(cost) else math.inf
        step = GOODS_ASK_ADJUSTMENT_SHARE_PER_YEAR * (ask if ask > 0.0 else max(last_price or 0.0, 0.0))
        choice = seller_pricing.best_reservation(
            book, rivals, offer, value, last_price, ceiling=min(ask + step, max(limit, value)), floor=value,
            current=ask, buyers=buyers)
        if choice is not None:
            offers[index] = dataclasses.replace(offer, reservation_price=choice)
    return offers


def market(generator):
    bids = [Bid("buyer%d" % index, GOOD, AREA, "tile", generator.choice([0.0, 2.0]), generator.uniform(0.0, 30.0),
                generator.uniform(0.5, 3.0), generator.uniform(0.3, 2.0), generator.uniform(5.0, 400.0),
                generator.choice([0, 1]), generator.choice([4.0, 1e9]))
            for index in range(generator.randint(0, 5))]
    offers = [Offer("seller%d" % index, GOOD, AREA, "tile", generator.choice([0.0, generator.uniform(0.5, 40.0)]),
                    generator.choice([0.0, 0.7, 1.0, 1.6, 2.5]))
              for index in range(generator.randint(0, 5))]
    producers = {}
    for offer in offers:
        kind = generator.choice(["none", "crowd", "owner", "owner"])
        if kind != "none":
            producers[offer.seller] = SimpleNamespace(workshops=2 if kind == "crowd" else 1,
                                                      cost=generator.choice([0.4, 1.0, 2.0, math.inf]))
    return bids, offers, producers


def run_new(bids, offers, producers, last_price, costs):
    setup = SimpleNamespace(basket_for=lambda tile: SimpleNamespace(substitution=1.5))
    record = SimpleNamespace(producers=producers)
    return seller_offers.strategic_offers(setup, record, None, bids, offers, last_price, costs)


def stub_costs(producers):
    def cost(_setup, _record, _view, offer):
        producer = producers.get(offer.seller)
        return None if producer is None else producer.cost
    no_inputs = mock.patch.object(seller_offers, "input_share_of_cost", lambda *_arguments: 0.0)   # the copy below bands the whole cost
    stack = contextlib.ExitStack()
    stack.enter_context(mock.patch.object(seller_offers, "unit_cost", cost))
    stack.enter_context(no_inputs)
    return stack


class LazyBuyersTests(unittest.TestCase):
    def test_equals_the_version_that_always_prepared(self):
        generator = random.Random(3)
        searched = 0
        for _case in range(600):
            bids, offers, producers = market(generator)
            last_price = generator.choice([None, 1.2])
            setup = SimpleNamespace(basket_for=lambda tile: SimpleNamespace(substitution=1.5))
            record = SimpleNamespace(producers=producers)
            old_costs, new_costs = {}, {}
            with stub_costs(producers):
                old = strategic_offers_always_preparing(setup, record, None, bids, offers, last_price, old_costs)
                new = run_new(bids, offers, producers, last_price, new_costs)
            self.assertEqual(old, new)
            self.assertEqual(old_costs, new_costs)
            searched += old != offers
        self.assertGreater(searched, 20)

    def test_no_searching_seller_builds_no_buyers(self):
        offers = [Offer("crowd", GOOD, AREA, "tile", 5.0, 1.0), Offer("trader", GOOD, AREA, "tile", 5.0, 1.0)]
        bids = [Bid("buyer", GOOD, AREA, "tile", 1.0, 5.0, 1.0, 1.0, 100.0)]
        producers = {"crowd": SimpleNamespace(workshops=3, cost=1.0)}
        with stub_costs(producers), mock.patch.object(goods_market, "Buyers", side_effect=AssertionError("early")):
            self.assertEqual(run_new(bids, offers, producers, 1.0, {}), offers)


if __name__ == "__main__":
    unittest.main()
