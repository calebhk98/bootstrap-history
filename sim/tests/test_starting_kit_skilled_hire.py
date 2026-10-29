"""Complaint 640: the smallest funded starting kit buys a skilled hire for a year. A kit's money is its labourer-years of the
civilisation's opening labourer wage (`data.kit_capital`), so the kit affords a smith when its labourer-years are at least the
smith's wage over the labourer's in the civilisation's wage schedule. The schedule is built from each civilisation file; the
kit is read as data. The wage rules are test_wage_floor_and_coin_standard."""
QUICK_TOPIC = True

import os
import unittest

from sim.content import catalog
from sim.engine import data, wage_schedule

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CIVILISATIONS = ["rome_100ad", "han_china_100ad", "england_1300", "norse_900ad", "mexica_1500", "sample_egypt_100bc_e7k2:egypt"]


def smallest_funded_kit_years():
    return min(kit["labourer_years"] for kit in data.STARTING_KITS.values() if kit["labourer_years"] > 0.0)


class StartingKitSkilledHire(unittest.TestCase):
    def test_the_smallest_funded_kit_covers_a_smiths_year_in_every_civilisation(self):
        registry = catalog.load_trade_registry(ROOT)
        for civ_name in CIVILISATIONS:
            schedule = wage_schedule.build_schedule(registry, data.load_civ(civ_name))
            smiths_year_in_labourer_years = schedule.annual_wage("smith") / schedule.annual_wage("labourer")
            self.assertGreaterEqual(smallest_funded_kit_years(), smiths_year_in_labourer_years, civ_name)

    def test_a_skilled_year_costs_more_than_a_labourers(self):
        schedule = wage_schedule.build_schedule(catalog.load_trade_registry(ROOT), data.load_civ("rome_100ad"))
        self.assertGreater(schedule.annual_wage("smith"), schedule.annual_wage("labourer"))


if __name__ == "__main__":
    unittest.main()
