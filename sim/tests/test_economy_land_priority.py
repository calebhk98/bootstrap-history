"""Scarce land on a tile goes to the uses that pay most for it, households' own plots included (Complaints 961, 538):
the order of claims is a pure function, and the land market grants by rent bid against the plot's own return."""

QUICK_TOPIC = True

import unittest

from sim.economy import land_priority, titles_plots
from sim.economy.land_market import LandDemand, clear_land


def demand(agent, hectares, value=100.0, cost=40.0, tile="t"):
    return LandDemand(agent, tile, hectares, value, cost)


class AllocateByBidTests(unittest.TestCase):
    def test_the_higher_bid_is_served_first(self):
        got = land_priority.allocate_by_bid(10.0, [("low", 2.0, 8.0), ("high", 5.0, 8.0)])
        self.assertAlmostEqual(got["high"], 8.0)
        self.assertAlmostEqual(got["low"], 2.0)

    def test_equal_bids_share_what_is_left_in_proportion_to_hectares_asked(self):
        got = land_priority.allocate_by_bid(6.0, [("a", 3.0, 8.0), ("b", 3.0, 4.0)])
        self.assertAlmostEqual(got["a"], 4.0)
        self.assertAlmostEqual(got["b"], 2.0)

    def test_nothing_is_granted_beyond_what_was_asked(self):
        got = land_priority.allocate_by_bid(100.0, [("a", 3.0, 8.0), ("b", 1.0, 4.0)])
        self.assertEqual(got, {"a": 8.0, "b": 4.0})

    def test_no_land_grants_nothing(self):
        self.assertEqual(land_priority.allocate_by_bid(0.0, [("a", 3.0, 8.0)]), {"a": 0.0})


class ClearLandByBidTests(unittest.TestCase):
    def test_a_producer_that_outbids_the_plots_takes_the_land_they_would_have_held(self):
        result = clear_land({"t": 100.0}, [demand("firm", 100.0, value=100.0, cost=40.0)], {"t": 100.0}, {"t": 20.0})
        self.assertAlmostEqual(result.granted_hectares["firm"], 100.0)
        self.assertAlmostEqual(result.ceded_by_tile["t"], 100.0)

    def test_a_producer_that_bids_less_than_the_plots_return_gets_only_what_they_leave(self):
        result = clear_land({"t": 100.0}, [demand("firm", 100.0, value=100.0, cost=90.0)], {"t": 60.0}, {"t": 50.0})
        self.assertAlmostEqual(result.granted_hectares["firm"], 40.0)
        self.assertNotIn("t", result.ceded_by_tile)

    def test_among_producers_the_higher_bid_gets_the_scarce_land(self):
        result = clear_land({"t": 10.0}, [demand("grain", 10.0, value=50.0, cost=40.0), demand("wood", 10.0, value=90.0, cost=40.0)])
        self.assertAlmostEqual(result.granted_hectares["wood"], 10.0)
        self.assertAlmostEqual(result.granted_hectares["grain"], 0.0)

    def test_the_plots_keep_their_land_when_they_return_more_than_every_producer_bids(self):
        result = clear_land({"t": 100.0}, [demand("firm", 50.0, value=60.0, cost=40.0)], {"t": 100.0}, {"t": 30.0})
        self.assertAlmostEqual(result.granted_hectares["firm"], 0.0)

    def test_without_a_valuation_of_the_plots_they_come_first_as_before(self):
        result = clear_land({"t": 100.0}, [demand("firm", 100.0)], {"t": 100.0})
        self.assertAlmostEqual(result.granted_hectares["firm"], 0.0)


class HectaresHeldTests(unittest.TestCase):
    def test_hectares_ceded_to_producers_are_not_held_by_households(self):
        held = titles_plots.allocate_on_tile({"a": 60.0, "b": 40.0}, 100.0, 30.0)
        self.assertAlmostEqual(held["a"], 42.0)
        self.assertAlmostEqual(held["b"], 28.0)

    def test_nothing_ceded_leaves_the_claims_as_they_were(self):
        held = titles_plots.allocate_on_tile({"a": 60.0, "b": 40.0}, 100.0, 0.0)
        self.assertEqual(held, {"a": 60.0, "b": 40.0})


if __name__ == "__main__":
    unittest.main()
