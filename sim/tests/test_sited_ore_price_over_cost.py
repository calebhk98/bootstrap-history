"""Complaint 519: a sited ore that the economy trades opens within a bounded multiple of its making cost.

Raising ore takes labour and nothing else, so a price many times its cost means a miner-hour sells for many
wages and mining would draw the workers. The most one metal's catalogue deposits differ in labour per tonne of
metal is the spread of their grades (a few times), so a scarcity rent beyond an order of magnitude is not a
rent but a stuck price. Known failure: after a first step some ores of every civilisation but the Norse and the
English still open beyond it, which ores varying with the opening's spin-up; the room of their sites and the grade
of their ore no longer bind them (Complaints/519), the opening's remembered prices do. Remove the marker when it
passes."""
import random
import unittest

from sim.tests import harness  # noqa: F401  (shortens the spin-up for the suite)
from sim.engine.core import Sim
from sim.engine.data import load, load_civ
from sim.geography import api as geography

ORE_PRICE_OVER_COST_BOUND = 10.0   # an order of magnitude: above the widest grade spread among one metal's deposits
CIVILISATIONS = ("rome_100ad", "han_china_100ad", "mexica_1500", "norse_900ad", "england_1300")


def sited_traded_ore_ratios(civilisation):
    """{ore good: agent price over the engine's making cost} after one step, for the ores of resources the
    seat has found a deposit of and whose markets cleared lately."""
    _tree, _prices, nodes, _wages, _goods = load()
    game = Sim(nodes, [], random.Random(3), events=False, manual=True, civ=load_civ(civilisation))
    game.done_year = {}
    game.step()
    prices, costs = game.economy.agent_prices(), game._material_prices()
    stale = game.economy.agent.stale_goods()
    return {ore: prices[ore] / costs[ore]
            for resource, ores in geography.ore_goods().items() if game.found_deposits(resource)
            for ore in ores if prices.get(ore) and costs.get(ore) and ore not in stale}


class SitedOrePriceOverCostTests(unittest.TestCase):
    @unittest.expectedFailure
    def test_every_civilisations_sited_ores_open_within_a_bounded_multiple_of_their_cost(self):
        too_dear = {}
        for civilisation in CIVILISATIONS:
            ratios = sited_traded_ore_ratios(civilisation)
            self.assertTrue(ratios, civilisation)
            too_dear[civilisation] = {ore: round(ratio, 1) for ore, ratio in ratios.items()
                                      if ratio > ORE_PRICE_OVER_COST_BOUND}
        self.assertEqual({civilisation: dear for civilisation, dear in too_dear.items() if dear}, {})


if __name__ == "__main__":
    unittest.main()
