"""A standing bid's demand is its fixed floor whatever the entry price, and the founder's draws become fixed-quantity bids at the
economy's price. Called on a bid and a fixture economy built here, no year is run."""
QUICK_TOPIC = True
import unittest

from sim.economy import entry_trial
from sim.economy.economy import Economy
from sim.economy.types import Bid
from sim.tests.test_economy_entry_for_standing_bids import GADGET, UNITS_WANTED, gadget_setup


class StandingBidTests(unittest.TestCase):
    def test_the_bids_demand_is_its_floor_whatever_the_entry_price(self):
        bid = Bid("buyer", GADGET, "area", "tile", UNITS_WANTED, 0.0, 400.0, 1.0, 1e9)
        self.assertAlmostEqual(entry_trial.demand_at([bid], 100.0, 100.0), UNITS_WANTED)

    def test_the_founders_draws_become_fixed_quantity_bids_at_the_economys_price(self):
        from sim.engine import economy_port_actors
        setup = gadget_setup()
        economy = Economy(setup)
        flows = {"bought": {GADGET: {"seat:one": 2.0, "firm:other": 9.0}}, "drawn": {GADGET: 1.0}}
        bids = economy_port_actors.standing_bids(economy, flows, {"seat:one"}, setup.capital_tile, lambda good: 0.5,
                                                 lambda commodity: [commodity])
        self.assertEqual(len(bids), 1)
        self.assertAlmostEqual(bids[0].floor_quantity, (2.0 + 1.0) / 0.5)
        self.assertEqual(bids[0].good, GADGET)
        self.assertGreater(bids[0].budget, 0.0)


if __name__ == "__main__":
    unittest.main()
