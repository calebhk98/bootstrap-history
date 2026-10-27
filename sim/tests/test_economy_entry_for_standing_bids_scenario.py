"""SMOKE (Complaint 629): the Rome game's economy setup prices the carriers its merchants wear. The entry rules for standing
bids are in test_economy_entry_for_standing_bids.py."""
import unittest


class RomeCarriersAreMakeableTests(unittest.TestCase):
    """Complaint 629: merchants wear pack saddles, river barges and merchant ships; their cordage comes from the rope
    walk, so a Rome without it priced none of the three and no merchant could bid for a replacement."""

    def test_rome_prices_the_carriers_its_merchants_wear(self):
        from sim.markets import port_setup
        from sim.tests.harness import unopened_sim
        game = unopened_sim()
        setup = port_setup.build_setup(game.economy.world)
        for carrier in ("pack_saddle", "river_barge", "merchant_ship"):
            self.assertIn(carrier, setup.opening_prices, carrier)


if __name__ == "__main__":
    unittest.main()
