"""Numba port item 7, bonded hours: `bondage_hours.place_held` indexes the bids by holder, trade and area and the offers by
trade and area once, where the old function scanned every bid and every offer for every holder. It equals the old function,
copied here, on random offers, bids and holdings (exact: the sums run over the same offers in the same order). No game."""

QUICK_TOPIC = True

import copy
import dataclasses
import random
import unittest

from sim.economy import bondage_hours
from sim.economy.types import LabourBid, LabourOffer

HOURS = 2000.0
TRADES = ("smith", "miller", "labourer")
AREAS = ("work@a", "work@b")


def old_place_held(held, workers, offers, bids, hours_per_worker, keep_per_worker_year, area_of):
    new_offers, new_bids = list(offers), list(bids)
    hired, keep = {}, []
    for tile in sorted(held):
        area = area_of(tile)
        for trade in sorted(held[tile]):
            available = workers(area, trade)
            for employer in sorted(held[tile][trade]):
                people = min(held[tile][trade][employer], available)
                held[tile][trade][employer] = people
                available -= people
                want = people * hours_per_worker
                for slot, bid in enumerate(new_bids):
                    if want <= 1e-12:
                        break
                    if bid.employer != employer or bid.trade != trade or bid.area != area or bid.hours <= 0.0:
                        continue
                    offered = sum(offer.hours for offer in new_offers if offer.trade == trade and offer.area == area)
                    taken = min(want, bid.hours, offered)
                    if taken <= 1e-12:
                        continue
                    cut = taken / offered
                    for index, offer in enumerate(new_offers):
                        if offer.trade == trade and offer.area == area and offer.hours > 0.0:
                            keep.append((employer, offer.worker, offer.hours * cut / hours_per_worker * keep_per_worker_year.get(area, 0.0)))
                            new_offers[index] = dataclasses.replace(offer, hours=offer.hours * (1.0 - cut))
                    new_bids[slot] = dataclasses.replace(bid, hours=bid.hours - taken)
                    rows = hired.setdefault(employer, {})
                    rows[trade] = rows.get(trade, 0.0) + taken
                    want -= taken
    return bondage_hours.HeldPlacement(new_offers, new_bids, hired, keep)


class PlaceHeldIsTheOldScan(unittest.TestCase):

    def test_random_offers_bids_and_holdings(self):
        rng = random.Random(5)
        for _round in range(60):
            offers = [LabourOffer("cohort%d" % index, rng.choice(TRADES), rng.choice(AREAS), rng.choice([0.0, rng.uniform(100, 9000)]), 1.0)
                      for index in range(rng.randrange(0, 25))]
            employers = ["firm%d" % index for index in range(6)]
            bids = [LabourBid(rng.choice(employers), rng.choice(TRADES), rng.choice(AREAS), rng.choice([0.0, rng.uniform(100, 9000)]), 1.0)
                    for _bid in range(rng.randrange(0, 30))]
            held = {tile: {trade: {employer: rng.uniform(0.1, 6.0) for employer in rng.sample(employers, rng.randrange(1, 4))}
                           for trade in rng.sample(TRADES, rng.randrange(1, 3))} for tile in ("a", "b", "c")[:rng.randrange(0, 4)]}
            workers = lambda area, trade: 3.0 + len(area) % 3 + len(trade) % 4
            keep_rate = {"work@a": 40.0, "work@b": 25.0}
            area_of = lambda tile: "work@" + ("a" if tile in ("a", "c") else "b")
            held_old = copy.deepcopy(held)
            old = old_place_held(held_old, workers, offers, bids, HOURS, keep_rate, area_of)
            new = bondage_hours.place_held(held, workers, offers, bids, HOURS, keep_rate, area_of)
            self.assertEqual(new, old)
            self.assertEqual(held, held_old)

    def test_no_holdings_leave_offers_and_bids(self):
        offers = [LabourOffer("cohort0", "smith", "work@a", 100.0, 1.0)]
        bids = [LabourBid("firm0", "smith", "work@a", 50.0, 1.0)]
        placement = bondage_hours.place_held({}, lambda area, trade: 1.0, offers, bids, HOURS, {}, lambda tile: tile)
        self.assertEqual((placement.offers, placement.bids, placement.hired, placement.keep), (offers, bids, {}, []))


if __name__ == "__main__":
    unittest.main()
