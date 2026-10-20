"""Complaint 621: hours a state takes from the working people (a corvee, conscripts) are hours the households do not offer
to the labour market, so they sell fewer hours and ask a dearer hour for the rest."""

QUICK_TOPIC = True

import types
import unittest

from sim.economy import households, year_labour
from sim.economy.protocols import YearInputs
from sim.labour.api import MarketState
from sim.labour.market.aptitude import split_evenly

HOURS = 2000.0
WORKERS = 60.0


class View:
    year = 1

    def area_of(self, trade, tile):
        return "work@" + tile


def offers_with(levy):
    cohort = households.Cohort("household:t:0", "t", 0, 100.0, WORKERS, 0.3)
    record = types.SimpleNamespace(cohorts={cohort.agent_id: cohort},
                                   workforce=MarketState(workers={"work@t": {"plough": split_evenly(WORKERS)}}))
    setup = types.SimpleNamespace(trades={}, working_hours_per_year=HOURS)
    if levy is None:
        return year_labour.labour_offers(setup, record, View(), {"t": 200.0})
    return year_labour.labour_offers(setup, record, View(), {"t": 200.0}, levy_hours_per_worker=levy)


class LabourLevyTests(unittest.TestCase):
    def test_without_a_levy_the_workers_offer_the_whole_year(self):
        self.assertAlmostEqual(offers_with(None)[0].hours, WORKERS * HOURS)

    def test_a_levy_removes_its_hours_from_every_worker(self):
        free = offers_with(None)[0]
        taxed = offers_with(300.0)[0]
        self.assertAlmostEqual(free.hours - taxed.hours, WORKERS * 300.0)

    def test_the_hours_left_are_asked_at_a_dearer_wage(self):
        self.assertGreater(offers_with(500.0)[0].reservation_wage, offers_with(None)[0].reservation_wage)

    def test_a_levy_of_the_whole_year_leaves_nothing_to_offer(self):
        self.assertEqual(offers_with(HOURS * 2.0), [])

    def test_the_engine_hands_the_levy_to_the_economy_each_year(self):
        inputs = YearInputs(year=1, population_by_tile={}, working_age_share=0.5, yield_factor_by_producer={}, engine_orders={},
                            labour_levy_hours_per_worker=40.0)
        self.assertEqual(inputs.labour_levy_hours_per_worker, 40.0)


if __name__ == "__main__":
    unittest.main()
