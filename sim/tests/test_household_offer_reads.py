"""The household decisions' reads of the year's offers as columns equal the loops over `LabourOffer` records they replace, to the last
digit, on random offers: the hours a worker offers (`household_hours_year.plot_parameters_by_cohort`), the worth of an hour
(`households_work.hour_value` at the faced wage times the expected share), the wage faced (`household_hours_year.wage_faced_per_hour`)
and the hours offered in each market (`household_work_year.expected_shares`). No game."""

QUICK_TOPIC = True

import random
import unittest

from sim.economy import households_work, trade_wages
from sim.economy.household_hours_year import wage_faced_per_hour
from sim.economy.household_offer_reads import OfferReads
from sim.economy.labour_offer_rows import LabourOfferRows
from sim.economy.types import LabourOffer

WORKERS = ("household:a:0", "household:a:1", "household:b:0", "seat:x")
TRADES = ("smith", "miller", "labourer")
AREAS = ("work@a", "work@b")


def random_offers(rng):
    return [LabourOffer(rng.choice(WORKERS), rng.choice(TRADES), rng.choice(AREAS),
                        rng.choice([0.0, rng.uniform(1.0, 5000.0), rng.uniform(1.0, 1e5) * 10.0 ** rng.randint(-6, 6)]),
                        rng.uniform(0.01, 3.0)) for _each in range(rng.randint(0, 25))]


def random_wages(rng):
    return {(trade, area): rng.choice([None, rng.uniform(0.01, 4.0)]) for trade in TRADES for area in AREAS}


class OfferColumnsEqualOfferRecords(unittest.TestCase):
    def test_hours_of_a_worker_are_the_sum_of_its_offers_hours(self):
        rng = random.Random(1)
        for _case in range(400):
            offers = random_offers(rng)
            rows = LabourOfferRows.of_objects(offers)
            found = OfferReads(rows).hours_of_workers().tolist()
            for worker, number in rows.workers.number_of.items():
                self.assertEqual(found[number], sum([offer.hours for offer in offers if offer.worker == worker]), offers)

    def test_worth_of_an_hour_is_hour_value_at_the_faced_wage_times_the_share(self):
        rng = random.Random(2)
        for _case in range(400):
            offers, wages = random_offers(rng), random_wages(rng)
            shares = {market: rng.uniform(0.0, 1.0) for market in wages}
            rows = LabourOfferRows.of_objects(offers)
            reads = OfferReads(rows)
            share = reads.market_values(lambda trade, area: shares[(trade, area)])
            found = reads.hour_value_of_workers(reads.faced_wage(lambda trade, area: wages[(trade, area)]), share).tolist()
            for worker, number in rows.workers.number_of.items():
                expected = households_work.hour_value(
                    [(offer.hours, trade_wages.faced_wage(wages[(offer.trade, offer.area)], offer.reservation_wage) * shares[(offer.trade, offer.area)])
                     for offer in offers if offer.worker == worker])
                self.assertEqual(found[number], expected, offers)

    def test_wage_faced_is_the_hours_weighted_faced_wage(self):
        rng = random.Random(3)
        for _case in range(400):
            offers, wages = random_offers(rng), random_wages(rng)
            rows = LabourOfferRows.of_objects(offers)
            reads = OfferReads(rows)
            found = reads.hour_value_of_workers(reads.faced_wage(lambda trade, area: wages[(trade, area)])).tolist()
            view = type("View", (), {"wage": staticmethod(lambda trade, area: wages[(trade, area)])})
            for worker, number in rows.workers.number_of.items():
                self.assertEqual(found[number], wage_faced_per_hour(view, [offer for offer in offers if offer.worker == worker]), offers)

    def test_hours_by_market_add_in_the_order_the_offers_came(self):
        rng = random.Random(4)
        for _case in range(400):
            offers = random_offers(rng)
            expected = {}
            for offer in offers:
                expected[(offer.trade, offer.area)] = expected.get((offer.trade, offer.area), 0.0) + offer.hours
            found = OfferReads(LabourOfferRows.of_objects(offers)).hours_by_market()
            self.assertEqual(found, expected)
            self.assertEqual(list(found), list(expected))

    def test_a_worker_with_no_offer_is_not_found(self):
        reads = OfferReads(LabourOfferRows.of_objects([LabourOffer("a", "smith", "work@a", 5.0, 1.0)]))
        self.assertIsNone(reads.worker_number("b"))
        self.assertEqual(reads.worker_number("a"), 0)


if __name__ == "__main__":
    unittest.main()
