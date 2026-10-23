"""Each civilisation's data names its money regime, only a struck coin carries a mint charge, and Mexica's cacao money is a
good in the production catalogue. Data checks, no game."""
QUICK_TOPIC = True
import json
import os
import unittest

from sim.tests.money_regimes_play import REGIME_OF
from sim.tests.harness import ROOT, S


class MoneyRegimeDataTests(unittest.TestCase):
    def test_every_civilisations_data_names_its_regime(self):
        for civ_id, regime in sorted(REGIME_OF.items()):
            self.assertEqual(S.load_civ(civ_id)["coin_standard"].get("regime"), regime, civ_id)

    def test_englands_mint_keeps_a_charge(self):
        self.assertGreater(S.load_civ("england_1300")["coin_standard"]["mint_charge_share"], 0.0)

    def test_only_a_struck_coin_carries_a_mint_charge(self):
        for civ_id, regime in sorted(REGIME_OF.items()):
            if regime != "struck_coin":
                self.assertNotIn("mint_charge_share", S.load_civ(civ_id)["coin_standard"], civ_id)

    def test_mexicas_money_is_cacao_a_good_in_the_production_catalogue(self):
        with open(os.path.join(ROOT, "data", "production", "94_agri_organics_gaps.json"), encoding="utf-8") as handle:
            production = json.load(handle)["materials"]
        material = S.load_civ("mexica_1500")["coin_standard"]["material"]
        self.assertIn(material, production)
        self.assertIn("cacao_kg", production["cacao_kg"]["outputs"])


if __name__ == "__main__":
    unittest.main()
