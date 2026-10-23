"""The starting wage in metal is alike across civilisations: a coin metal costs the same hours wherever it is made, so an hour of work
is paid alike in metal (Complaint 507, stage 2). Reads the civilisation records and their starting schedules; no game."""
import unittest

from sim.engine import data
from sim.labour.api import wage_provider

QUICK_TOPIC = True

CIVILISATIONS = ("rome_100ad", "england_1300", "norse_900ad")
GRAMS_SPREAD = 1.15       # the dearest civilisation's hour in grams of coin metal over the cheapest's (heuristic; no measuring command)


class OpeningWageAnchorTests(unittest.TestCase):
    def test_a_coin_metal_costs_the_same_hours_wherever_it_is_made_so_an_hour_is_paid_alike_in_metal(self):
        grams = {}
        for civ_id in CIVILISATIONS:
            standard = wage_provider.coin_standard(data.load_civ(civ_id))
            grams[civ_id] = data.starting_schedule(civ_id).money_per_labour_hour * standard["kg_per_unit"] * 1000.0
        self.assertLess(max(grams.values()) / min(grams.values()), GRAMS_SPREAD, grams)


if __name__ == "__main__":
    unittest.main()
