"""SCENARIO: the opening prices of Rome, England and the Mexica put oil into household light spending only where olives
grow (Complaint 531). The data rules are in `test_lighting_inputs`."""

import unittest

from sim.engine.economy_port_setup import build_setup
from sim.tests.harness import unopened_sim
from sim.world import need_basket


def _oil_share_of_light(civilisation_id):
    """Share of a household's light spending that goes to oil lamps at the start's own opening prices."""
    setup = build_setup(unopened_sim(civ=civilisation_id))
    light = [need for need in need_basket.need_prices(setup.basket_for(setup.capital_tile), setup.opening_prices.get)
             if need.spec.need_id == "light"][0]
    oil = sum(share for good, _price, _effect, share in light.goods if "oil_lamp" in good)
    return oil, sum(share for _good, _price, _effect, share in light.goods)


class LightingSpendingTests(unittest.TestCase):
    def test_oil_takes_more_of_the_light_spending_where_olives_grow(self):
        southern_oil, southern_total = _oil_share_of_light("rome_100ad")
        northern_oil, northern_total = _oil_share_of_light("england_1300")
        self.assertGreater(southern_total, 0.0)
        self.assertGreater(northern_total, 0.0)
        self.assertGreater(southern_oil / southern_total, northern_oil / northern_total)

    def test_no_oil_is_bought_where_the_olive_tree_is_unknown(self):
        oil, total = _oil_share_of_light("mexica_1500")
        self.assertGreater(total, 0.0)
        self.assertEqual(oil, 0.0)


if __name__ == "__main__":
    unittest.main()
