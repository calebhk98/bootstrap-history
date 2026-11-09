"""Bonded hours on rows (stage 4): `bondage_hours.place_held`, `place` and `payable_keep` work on the rows of the offers and the bids and
walk them with kernels (`bondage_kernels.py`). Each equals the plain Python it replaced (`sim/tests/bondage_plain.py`, one record at a
time, every offer and bid scanned) to the last digit, on written-out inputs and on random offers, bids, holdings and bonds. No game."""

QUICK_TOPIC = True

import copy
import random
import unittest

import numpy

from sim.economy import bondage_hours
from sim.economy.bondage_rows import KeepRows
from sim.economy.labour_offer_rows import LabourOfferRows
from sim.economy.types import LabourBid, LabourOffer
from sim.labour.api import LabourBidTable
from sim.tests.bondage_plain import plain_payable_keep, plain_place, plain_place_held

HOURS = 2000.0
TRADES = ("smith", "miller", "labourer")
AREAS = ("work@a", "work@b")


def random_rows(rng, cohorts=25, firms=6, bids=30):
    offers = [LabourOffer("cohort%d" % index, rng.choice(TRADES), rng.choice(AREAS), rng.choice([0.0, rng.uniform(100, 9000)]),
                          rng.choice([0.0, 0.5, rng.uniform(0.1, 3.0)])) for index in range(rng.randrange(0, cohorts))]
    employers = ["firm%d" % index for index in range(firms)]
    found = [LabourBid(rng.choice(employers), rng.choice(TRADES), rng.choice(AREAS), rng.choice([0.0, rng.uniform(100, 9000)]),
                       rng.uniform(0.5, 2.0)) for _bid in range(rng.randrange(0, bids))]
    return offers, found, employers


def as_block(workers):
    """A scalar `workers(area, trade)` as the block form `place_held` takes."""
    return lambda areas, trades: numpy.array([workers(area, trade) for area, trade in zip(areas, trades)], dtype=float)


class PlaceHeld(unittest.TestCase):
    def check(self, held, workers, offers, bids, keep_rate, area_of):
        held_plain = copy.deepcopy(held)
        plain = plain_place_held(held_plain, workers, offers, bids, HOURS, keep_rate, area_of)
        placed = bondage_hours.place_held(held, as_block(workers), offers, bids, HOURS, keep_rate, area_of)
        self.assertEqual(list(placed.offers), plain.offers)
        self.assertEqual([(bid.employer, bid.trade, bid.area, bid.hours) for bid in placed.bids],
                         [(bid.employer, bid.trade, bid.area, bid.hours) for bid in plain.bids])
        self.assertEqual(placed.hired, plain.hired)
        self.assertEqual(list(placed.keep), plain.keep)
        self.assertEqual(held, held_plain)
        return bool(plain.hired)

    def test_written_out(self):
        offers = [LabourOffer("c0", "smith", "work@a", 1000.0, 1.0), LabourOffer("c1", "smith", "work@a", 3000.0, 1.0),
                  LabourOffer("c2", "miller", "work@a", 500.0, 1.0)]
        bids = [LabourBid("firm", "smith", "work@a", 800.0, 1.0), LabourBid("other", "smith", "work@a", 800.0, 1.0)]
        held = {"a": {"smith": {"firm": 0.25}}}
        placed = bondage_hours.place_held(held, as_block(lambda area, trade: 10.0), offers, bids, HOURS, {"work@a": 40.0}, lambda tile: "work@" + tile)
        self.assertEqual(placed.hired, {"firm": {"smith": 500.0}})
        self.assertEqual([offer.hours for offer in placed.offers], [875.0, 2625.0, 500.0])      # a share of 500 of the 4000 offered
        self.assertEqual([bid.hours for bid in placed.bids], [300.0, 800.0])
        self.assertEqual([(employer, cohort) for employer, cohort, _money in placed.keep], [("firm", "c0"), ("firm", "c1")])
        self.assertEqual([offer.hours for offer in offers], [1000.0, 3000.0, 500.0])             # the offers handed over are not cut

    def test_random_offers_bids_and_holdings(self):
        rng = random.Random(5)
        placing = 0
        for _round in range(120):
            offers, bids, employers = random_rows(rng)
            held = {tile: {trade: {employer: rng.uniform(0.1, 6.0) for employer in rng.sample(employers, rng.randrange(1, 4))}
                           for trade in rng.sample(TRADES, rng.randrange(1, 3))} for tile in ("a", "b", "c")[:rng.randrange(0, 4)]}
            workers = lambda area, trade: 3.0 + len(area) % 3 + len(trade) % 4
            keep_rate = {"work@a": 40.0, "work@b": 25.0}
            area_of = lambda tile: "work@" + ("a" if tile in ("a", "c") else "b")
            placing += self.check(held, workers, offers, bids, keep_rate, area_of)
        self.assertGreater(placing, 20)       # the rounds are not all empty

    def test_rows_and_records_give_the_same_answer(self):
        rng = random.Random(8)
        offers, bids, _employers = random_rows(rng)
        bid_table = LabourBidTable()
        bid_table.add_objects(bids)
        held = {"a": {"smith": {"firm0": 2.0, "firm1": 1.0}}}
        args = (as_block(lambda area, trade: 5.0), HOURS, {"work@a": 30.0}, lambda tile: "work@a")
        from_records = bondage_hours.place_held(copy.deepcopy(held), args[0], offers, bids, *args[1:])
        from_rows = bondage_hours.place_held(copy.deepcopy(held), args[0], LabourOfferRows.of_objects(offers, bid_table.trades, bid_table.areas),
                                             bid_table, *args[1:])
        self.assertEqual(list(from_rows.offers), list(from_records.offers))
        self.assertEqual(from_rows.hired, from_records.hired)
        self.assertEqual(list(from_rows.keep), list(from_records.keep))

    def test_no_holdings_leave_offers_and_bids(self):
        offers = [LabourOffer("cohort0", "smith", "work@a", 100.0, 1.0)]
        bids = [LabourBid("firm0", "smith", "work@a", 50.0, 1.0)]
        placement = bondage_hours.place_held({}, as_block(lambda area, trade: 1.0), offers, bids, HOURS, {}, lambda tile: tile)
        self.assertEqual((list(placement.offers), [(bid.employer, bid.trade, bid.area, bid.hours, bid.maximum_wage) for bid in placement.bids],
                          placement.hired, list(placement.keep)), (offers, [(bid.employer, bid.trade, bid.area, bid.hours, bid.maximum_wage) for bid in bids], {}, []))


class PlaceBonds(unittest.TestCase):
    def test_random_offers_bids_and_bonds(self):
        rng = random.Random(11)
        placing = 0
        for _round in range(400):
            offers, bids, employers = random_rows(rng)
            owner = {employer: rng.choice(["creditor0", "creditor1", employer]) for employer in employers}
            workers = sorted({offer.worker for offer in offers} | {"cohort99"})       # a cohort with no offers may be bonded too
            bonds = {worker: {"creditor": rng.choice(["creditor0", "creditor1", "nobody"]), "debt": rng.choice([0.0, rng.uniform(1, 9000)])}
                     for worker in rng.sample(workers, rng.randrange(0, min(8, len(workers)) + 1))}
            share = rng.choice([0.25, 0.75, 1.0])
            plain = plain_place(bonds, offers, bids, owner.get, share)
            placed = bondage_hours.place(bonds, offers, bids, owner.get, share)
            self.assertEqual(list(placed.offers), plain.offers)
            self.assertEqual([(bid.employer, bid.trade, bid.area, bid.hours) for bid in placed.bids],
                             [(bid.employer, bid.trade, bid.area, bid.hours) for bid in plain.bids])
            self.assertEqual((placed.hired, placed.hours_placed, placed.value_placed, placed.cash_share),
                             (plain.hired, plain.hours_placed, plain.value_placed, plain.cash_share))
            placing += bool(plain.hired)
        self.assertGreater(placing, 20)       # the rounds are not all empty

    def test_a_cohort_with_no_offers_has_no_cash_share(self):
        placed = bondage_hours.place({"nobody": {"creditor": "c", "debt": 5.0}}, [LabourOffer("other", "smith", "a", 10.0, 1.0)], [],
                                     lambda employer: employer, 0.75)
        self.assertEqual((placed.hired, placed.hours_placed, placed.cash_share), ({}, {}, {}))


class PayableKeep(unittest.TestCase):
    def test_random_rows(self):
        rng = random.Random(3)
        for _round in range(200):
            holders = ["works%d" % index for index in range(4)]
            rows = [(rng.choice(holders), "cohort%d" % index, rng.choice([0.0, rng.uniform(0.0, 9.0)])) for index in range(rng.randrange(0, 20))]
            balance = {holder: rng.choice([-1e-13, 0.0, rng.uniform(0.0, 30.0)]) for holder in holders}
            self.assertEqual(list(bondage_hours.payable_keep(rows, balance.get)), plain_payable_keep(rows, balance.get))

    def test_rows_in_the_form_of_arrays(self):
        rows = KeepRows(["works", "works"], ["cohort:a", "cohort:b"], numpy.array([6.0, 6.0]))
        paid = bondage_hours.payable_keep(rows, {"works": 10.0}.get)
        self.assertEqual(list(paid), [("works", "cohort:a", 6.0), ("works", "cohort:b", 4.0)])


if __name__ == "__main__":
    unittest.main()
