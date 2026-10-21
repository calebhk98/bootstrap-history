"""SCENARIO: England 1300's opening basket moves light spending from tallow to cleaner light as quality reach rises.
The rule is in `test_need_quality`; this reads the real needs data through a built opening."""
import unittest

from sim.engine.economy_port_setup import build_setup
from sim.tests.harness import unopened_sim
from sim.world import need_basket


class RealLightGoodsTest(unittest.TestCase):
    def test_the_real_basket_moves_light_spending_from_tallow_to_cleaner_light_as_reach_rises(self):
        setup = build_setup(unopened_sim(civ="england_1300"))
        basket = setup.basket_for(setup.capital_tile)
        base = need_basket.need_prices(basket, setup.opening_prices.get)
        light_spec = [need.spec for need in base if need.spec.need_id == "light"][0]
        tallow = {good for good, _factor in light_spec.qualities if "tallow" in good}
        self.assertTrue(tallow)

        def tallow_share(reach):
            (light,) = [need for need in need_basket.with_quality_reach(base, basket, reach)
                        if need.spec.need_id == "light"]
            return sum(share for good, _price, _effect, share in light.goods if good in tallow)

        self.assertLess(tallow_share(1.0), tallow_share(0.0))


if __name__ == "__main__":
    unittest.main()
