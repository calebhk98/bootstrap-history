"""The hours a market's households sell at a wage: the schedule asked many times at once equals the offer-by-offer
split the settlement reads. Plain records, no game."""

QUICK_TOPIC = True

import unittest

from sim.economy.labour_supply import HourSupply
from sim.economy.types import LabourOffer


def supply():
    offers = [LabourOffer("farmers", "reaper", "vale", 1000.0, 0.1), LabourOffer("farmers", "reaper", "hill", 400.0, 0.1),
              LabourOffer("idle", "reaper", "vale", 0.0, 0.1), LabourOffer("potters", "reaper", "vale", 600.0, 0.1)]
    return HourSupply(offers=offers, plan_hours={"farmers": 100.0}, work_hours={"farmers": 200.0, "potters": 50.0},
                      plot_hours_at={"farmers": lambda wage: 900.0 / (1.0 + wage)})


class TheScheduleEqualsTheSplit(unittest.TestCase):

    def test_hours_sold_at_a_wage_are_the_splits_sold_hours_for_every_offer(self):
        held = supply()
        for offer in held.offers:
            schedule = held.sold_hours_schedule(offer)
            for wage in (0.0, 0.05, 0.5, 1.0, 5.0, 100.0):
                self.assertAlmostEqual(schedule(wage), held.split(offer, wage)[0], places=9)

    def test_a_markets_share_is_its_offers_sold_hours_over_its_hours(self):
        held = supply()
        share = held.share_at("reaper", "vale")
        for wage in (0.05, 1.0, 20.0):
            sold = sum(held.split(offer, wage)[0] for offer in held.offers if offer.area == "vale")
            self.assertAlmostEqual(share(wage), sold / 1600.0, places=9)


if __name__ == "__main__":
    unittest.main()
