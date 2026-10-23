"""Complaint 331: what an entrant expects. `SimWorld.entry_gross` is the concern's takings at full ramp times the output
market's factor, then, in a goods category, the factor the category's price gives with the entrants added; elsewhere the
takings shared among the rivals and the entrants. An expanded incumbent counts as more rivals (test_firm_expansion). The
sim is a stand-in holding only what the rule reads."""
QUICK_TOPIC = True

import unittest

from sim.engine.agents_port import SimWorld

GOODS = "cloth"
SERVICE = "teaching"
TAKINGS = 1000.0
MARKET_FACTOR = 0.8


class StandInSim:
    GOODS_CATEGORIES = (GOODS,)
    nodes = {"weaver": {"cat": GOODS}, "school": {"cat": SERVICE}}

    def __init__(self, supply_falls_per_entrant):
        self.supply_falls_per_entrant = supply_falls_per_entrant
        self.asked_entrants = []

    def concern_takings(self, node_id, ramp):
        assert ramp == 1.0
        return TAKINGS

    def node_output_market_factor(self, node):
        return MARKET_FACTOR

    def goods_category_factor_with_entrants(self, category, entrants):
        self.asked_entrants.append((category, entrants))
        return 1.0 / (1.0 + self.supply_falls_per_entrant * entrants)


class EntryGrossTests(unittest.TestCase):
    def test_a_goods_concern_expects_its_takings_times_the_categorys_factor_with_the_entrants(self):
        sim = StandInSim(supply_falls_per_entrant=0.5)
        gross = SimWorld(sim).entry_gross("weaver", rivals=3.0, entrants=2)
        self.assertAlmostEqual(gross, TAKINGS * MARKET_FACTOR / 2.0)
        self.assertEqual(sim.asked_entrants, [(GOODS, 2)])

    def test_more_entrants_in_a_goods_category_mean_less_expected(self):
        sim = StandInSim(supply_falls_per_entrant=0.5)
        world = SimWorld(sim)
        self.assertLess(world.entry_gross("weaver", 0.0, 3), world.entry_gross("weaver", 0.0, 1))

    def test_a_goods_concern_does_not_divide_by_rivals_the_price_already_carries(self):
        sim = StandInSim(supply_falls_per_entrant=0.5)
        world = SimWorld(sim)
        self.assertEqual(world.entry_gross("weaver", 0.0, 1), world.entry_gross("weaver", 9.0, 1))

    def test_a_service_shares_its_takings_among_rivals_and_entrants(self):
        world = SimWorld(StandInSim(0.5))
        self.assertAlmostEqual(world.entry_gross("school", rivals=3.0, entrants=1), TAKINGS * MARKET_FACTOR / 4.0)

    def test_a_service_expects_less_the_more_rivals_there_are(self):
        world = SimWorld(StandInSim(0.5))
        self.assertLess(world.entry_gross("school", 6.0, 1), world.entry_gross("school", 1.0, 1))


if __name__ == "__main__":
    unittest.main()
