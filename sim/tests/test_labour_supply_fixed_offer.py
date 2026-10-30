"""A household offers every hour its plot and household work do not take, at any wage (Eurace@Unibi Labour/Household_Employee_Functions.c:
an employed household supplies its whole labour, an unemployed one searches). Plain records, no game."""

QUICK_TOPIC = True

import unittest

from sim.economy.labour_supply import HourSupply
from sim.economy.types import LabourOffer


def supply():
    offers = [LabourOffer("farmers", "reaper", "vale", 1000.0, 0.1)]
    return HourSupply(offers=offers, plan_hours={"farmers": 100.0}, work_hours={"farmers": 200.0}, plot_hours_at={})


class TheOfferIsEveryFreeHour(unittest.TestCase):

    def test_hours_sold_are_the_hours_left_after_plan_and_work_at_every_wage(self):
        held = supply()
        for wage in (0.01, 1.0, 100.0):
            self.assertAlmostEqual(held.split(held.offers[0], wage)[0], 700.0)

    def test_the_settled_offer_keeps_only_the_plan_and_the_work(self):
        held = supply()
        held.settle({("reaper", "vale"): 1.0})
        self.assertAlmostEqual(held.kept["farmers"], 300.0)


if __name__ == "__main__":
    unittest.main()
