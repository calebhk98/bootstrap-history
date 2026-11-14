"""The price a market remembers after a year moves in proportion to what traded and what was wanted, against a reference volume that is never zero."""

QUICK_TOPIC = True

import unittest

from sim.economy.market_memory_blend import blended_price, reference_volume

def price(old, total, cleared, wanted, target, reference, was_quote=False, quiet_years=0, demand_led=True, cost=None):
    return blended_price(old, was_quote, quiet_years, reference, total, cleared, wanted, demand_led, target, cost)


class ReferenceVolumeTests(unittest.TestCase):
    def test_a_market_with_no_usual_volume_and_no_buyers_still_has_a_reference(self):
        self.assertGreater(reference_volume(0.0, 0.0, 0.0, 0.25), 0.0)

    def test_the_reference_is_the_largest_of_the_market_scales(self):
        self.assertEqual(reference_volume(40.0, 100.0, 80.0, 0.25), 40.0)
        self.assertEqual(reference_volume(2.0, 100.0, 80.0, 0.25), 25.0)
        self.assertEqual(reference_volume(2.0, 4.0, 400.0, 0.25), 100.0)


class BlendedPriceTests(unittest.TestCase):
    def test_a_sliver_of_trade_in_a_market_with_no_usual_volume_moves_the_price_a_sliver(self):
        reference = reference_volume(0.0, 0.0, 0.0, 0.25)
        self.assertAlmostEqual(price(2603.97, 2.5e-16, 106.81, 0.0, None, reference), 2603.97, places=9)

    def test_a_sliver_bid_drifts_the_price_a_sliver_toward_the_cost(self):
        reference = reference_volume(0.0, 1e-16, 0.0, 0.25)
        self.assertAlmostEqual(price(2603.97, 0.0, None, 1e-16, 1854.82, reference), 2603.97, places=9)

    def test_a_market_with_no_bid_and_no_offer_left_keeps_its_price(self):
        self.assertAlmostEqual(price(50.0, 0.0, None, 0.0, 10.0, reference_volume(0.0, 0.0, 0.0, 0.25)), 50.0, places=12)

    def test_the_price_is_continuous_in_the_quantity_traded(self):
        reference = reference_volume(30.0, 0.0, 0.0, 0.25)
        steps = [price(100.0, total, 20.0, 0.0, 60.0, reference) for total in (0.0, 1e-12, 1e-6, 1.0, 10.0, 30.0)]
        self.assertAlmostEqual(steps[0], steps[1], places=9)
        self.assertEqual([each for each in steps], sorted(steps, reverse=True))
        self.assertEqual(steps[-1], 20.0)

    def test_the_price_is_continuous_in_the_quantity_wanted(self):
        reference = reference_volume(30.0, 0.0, 0.0, 0.25)
        steps = [price(100.0, 0.0, None, wanted, 60.0, reference) for wanted in (0.0, 1e-12, 1.0, 10.0, 30.0, 300.0)]
        self.assertEqual(steps[0], 100.0)
        self.assertAlmostEqual(steps[0], steps[1], places=9)
        self.assertEqual(steps, sorted(steps, reverse=True))
        self.assertAlmostEqual(steps[-1], 100.0 + 0.3 * (60.0 - 100.0))

    def test_a_representative_trade_is_not_pulled_toward_the_cost(self):
        reference = reference_volume(30.0, 0.0, 0.0, 0.25)
        self.assertEqual(price(100.0, 0.25 * reference, 100.0, 0.0, 60.0, reference, demand_led=False), 100.0)

    def test_the_pull_toward_the_cost_fades_as_trade_nears_a_representative_share(self):
        reference = reference_volume(30.0, 0.0, 0.0, 0.25)
        pulled = [price(100.0, share * 0.25 * reference, 100.0, 0.0, 60.0, reference, demand_led=False) for share in (0.0, 0.5, 1.0)]
        self.assertAlmostEqual(pulled[0], 100.0 + 0.3 * (60.0 - 100.0))
        self.assertAlmostEqual(pulled[1], 100.0 + 0.5 * 0.3 * (60.0 - 100.0))
        self.assertEqual(pulled[2], 100.0)

    def test_a_market_with_nothing_remembered_takes_its_target_or_its_trade(self):
        reference = reference_volume(30.0, 0.0, 0.0, 0.25)
        self.assertEqual(price(None, 0.0, None, 0.0, 60.0, reference), 60.0)
        self.assertEqual(price(None, 15.0, 20.0, 0.0, None, reference), 20.0)
        self.assertIsNone(price(None, 0.0, None, 0.0, None, reference))


if __name__ == "__main__":
    unittest.main()
