"""Scenarios (Complaint 640): the smallest funded starting kit of each civilisation affords a skilled hire for a year in a
built game. The wage rules are in test_wage_floor_and_coin_standard."""
import unittest

from sim.engine import data

CIVILISATIONS = ["rome_100ad", "han_china_100ad", "england_1300", "norse_900ad", "mexica_1500"]


class OpeningCapitalScenarios(unittest.TestCase):

    def _sim(self, civ_name, kit):
        import random
        from sim.tests import harness
        from sim.engine.core import Sim
        # unopened: the claim is the opening purse against the opening wage quote, neither of which needs the agent economy
        return harness.build_unopened(lambda: Sim(
            harness.NODES, harness.ORDER, random.Random(1), events=False, manual=True,
            civ=data.load_civ(civ_name), cfg={"start_kit": kit}))

    def test_the_smallest_funded_kit_affords_a_skilled_hire_for_a_year(self):
        # Capital grows with the kit, so the smallest funded kit is the binding case.
        smallest_kit = min((kit for kit, kit_data in data.STARTING_KITS.items()
                            if kit_data["labourer_years"] > 0.0),
                           key=lambda kit: data.STARTING_KITS[kit]["labourer_years"])
        for civ_name in CIVILISATIONS + ["sample_egypt_100bc_e7k2:egypt"]:
            engine = self._sim(civ_name, smallest_kit)
            self.assertGreaterEqual(
                engine.household.capital, engine.labour.market.quote_annual("smith"), (civ_name, smallest_kit))


if __name__ == "__main__":
    unittest.main()
