"""Complaint 331: what an entrant expects. `ActorWorld.entry_gross` is the concern's takings at full ramp times the output
market's factor (the economy's cleared price over the long-run one), shared among the rivals and the entrants. An expanded incumbent counts as more rivals (test_firm_expansion). The
sim is a stand-in holding only what the rule reads."""
QUICK_TOPIC = True

import unittest

from sim.actors.world import ActorWorld

from .world_stand_in import fake_needs

GOODS = "cloth"
SERVICE = "teaching"
TAKINGS = 1000.0
MARKET_FACTOR = 0.8


class StandInSim:
    """The module the world is handed: the views the entry rule reads."""

    def __init__(self, market_rate=None):
        self.needs = fake_needs(
            goods_categories=lambda: (GOODS,), tree_nodes={"weaver": {"cat": GOODS}, "school": {"cat": SERVICE}},
            concern_takings=self.concern_takings, node_output_market_factor=lambda node: MARKET_FACTOR, market_rate=market_rate)

    def concern_takings(self, node_id, ramp):
        assert ramp == 1.0
        return TAKINGS


class EntryGrossTests(unittest.TestCase):
    def test_a_concern_shares_its_takings_among_rivals_and_entrants(self):
        world = ActorWorld(StandInSim().needs)
        self.assertAlmostEqual(world.concerns.entry_gross("weaver", rivals=3.0, entrants=2), TAKINGS * MARKET_FACTOR / 5.0)
        self.assertAlmostEqual(world.concerns.entry_gross("school", rivals=3.0, entrants=1), TAKINGS * MARKET_FACTOR / 4.0)

    def test_a_concern_expects_less_the_more_rivals_there_are(self):
        world = ActorWorld(StandInSim().needs)
        self.assertLess(world.concerns.entry_gross("weaver", 6.0, 1), world.concerns.entry_gross("weaver", 1.0, 1))


class EntrantsRateTests(unittest.TestCase):
    def test_the_entrants_cost_of_capital_is_the_capital_markets_rate(self):
        game = StandInSim(market_rate=0.0731)
        self.assertEqual(ActorWorld(game.needs).credit.market_rate(), 0.0731)


if __name__ == "__main__":
    unittest.main()
