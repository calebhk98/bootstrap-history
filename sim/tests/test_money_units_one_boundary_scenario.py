"""Scenario: in running games every money figure reaches the player in the civilisation's own coin through one
conversion: labour hours -> civilisation money. The derivations in hours (revenue ignores the coin, the revenue to wage
ratio, material prices in hours) are called directly in test_money_units_one_boundary."""
import contextlib
import copy
import random
import unittest

from sim.engine import data
from sim.engine.core import Sim

BASE_CIVS = ["rome_100ad", "han_china_100ad"]
MOD_CIV = "sample_egypt_100bc_e7k2:egypt"
ALL_CIVS = BASE_CIVS + [MOD_CIV]
COIN_SCALE = 2.5


def _harness():
    from sim.tests import harness
    return harness


def build(civ):
    harness = _harness()
    sim = Sim(harness.NODES, harness.ORDER, random.Random(1), events=False,
              manual=True, civ=civ)
    sim.goal, sim.done_year = harness.GOAL, {}
    return sim


_PLAIN_GAMES = {}


def plain(name):
    """One shared, never-mutated game per civilisation (or per coin-scaled Rome). The coin-scaled Rome shares
    Rome's cached spin-up (the economy counts money in its own unit); the mod civilisation, which no suite start
    warms, is built with its economy unopened and answered by the engine's own figures."""
    if name not in _PLAIN_GAMES:
        if name == "heavier_rome":
            _PLAIN_GAMES[name] = build(civ_with_coin_scale("rome_100ad", COIN_SCALE))
        elif name == MOD_CIV:
            _PLAIN_GAMES[name] = _harness().build_unopened(lambda: build(data.load_civ(name)))
        else:
            _PLAIN_GAMES[name] = build(data.load_civ(name))
    return _PLAIN_GAMES[name]


def civ_with_coin_scale(name, scale):
    civ = copy.deepcopy(data.load_civ(name))
    civ["coin_standard"]["kg_per_unit"] *= scale
    return civ


def reference_concern(*games):
    """A revenue-earning node picked by a rule, not by name: the cheapest to build (in the first game) among those
    that take more than they cost to keep in every game given."""
    first = games[0]
    candidates = sorted(
        (node["_total_cost"], node_id) for node_id, node in first.nodes.items()
        if node["rev"] > node["up"] > 0 and node["_total_cost"] > 0)
    for _cost, node_id in candidates:
        if all(game.concern_takings(node_id, 1.0) > game.nodes[node_id]["up"] * game.price_index for game in games):
            return node_id
    raise AssertionError("no revenue-earning node pays its keep in every game")


def labourer_annual_wage(sim):
    return sim.labour.wage_schedule().annual_wage("labourer")


def takings_per_wage(sim, node_id):
    """One concern's yearly takings in labourer-years, with the civilisation's
    price level and output factor divided out."""
    factors = sim.price_index * sim.state.economy.output_factor
    return sim.concern_takings(node_id, 1.0) / factors / labourer_annual_wage(sim)


@contextlib.contextmanager
def opened_concern(sim, node_id):
    """`node_id` known and running on a shared game for the duration of the block; the game's sets are put back after."""
    done_before, operating_before = set(sim.done), set(sim.operating)
    sim.done.add(node_id)
    sim.operating.add(node_id)
    sim._done_changed()
    try:
        yield
    finally:
        sim.done.intersection_update(done_before)
        sim.operating.intersection_update(operating_before)
        sim._done_changed()


class EconomyWorksWithAnyCoin(unittest.TestCase):

    def test_han_can_afford_and_earn_from_a_basic_concern(self):
        han = plain("han_china_100ad")
        rome = plain("rome_100ad")
        node_id = reference_concern(han, rome)

        def payback(sim):
            net = sim.concern_takings(node_id, 1.0) - sim.nodes[node_id]["up"] * sim.price_index
            return sim.project_cost(node_id) / net

        self.assertLess(han.project_cost(node_id), han.capital * 20,
                        "concern is out of reach of the opening purse")
        self.assertGreater(payback(han), 0)
        # earning from it: Han's concern pays back no slower than a few times Rome's; paying back faster
        # is an outcome of Han's prices and wages, not a unit error
        self.assertLess(payback(han), payback(rome) * 3.0)

    def test_purse_and_annual_wage_are_of_one_scale_in_every_civilisation(self):
        rome = plain("rome_100ad")
        rome_years = rome.capital / labourer_annual_wage(rome)
        for name in ALL_CIVS:
            sim = plain(name)
            years = sim.capital / labourer_annual_wage(sim)
            self.assertAlmostEqual(years / sim.price_index, rome_years,
                                   delta=rome_years * 1e-6, msg=name)

    def test_running_revenue_is_a_sane_multiple_of_a_labourers_wage_everywhere(self):
        for name in ALL_CIVS:
            sim = plain(name)
            with opened_concern(sim, reference_concern(sim)):
                years = sim.revenue() / labourer_annual_wage(sim)
            self.assertGreater(years, 0.01, name)
            self.assertLess(years, 5000.0, name)


class CoinMassRescalesEveryFigure(unittest.TestCase):

    def test_every_money_figure_scales_with_the_coin(self):
        base = plain("rome_100ad")
        heavier = plain("heavier_rome")
        node_id = reference_concern(base, heavier)
        with opened_concern(base, node_id), opened_concern(heavier, node_id):
            figures = {
                "purse": lambda sim: sim.capital,
                "labourer wage": labourer_annual_wage,
                "project cost": lambda sim: sim.project_cost(node_id),
                "takings": lambda sim: sim.concern_takings(node_id, 1.0),
                "revenue": lambda sim: sim.revenue(),
                "wheat": lambda sim: sim._material_prices()["wheat_kg"],
                "forest per hectare": lambda sim: sim.FOREST_COST_PER_HA,
                "slave base price": lambda sim: sim.labour.SLAVE_BASE_PRICE,
                "node upkeep": lambda sim: sim.nodes[node_id]["up"],
                "node capital": lambda sim: sim.nodes[node_id]["cap"],
            }
            for label, figure in figures.items():
                self.assertAlmostEqual(figure(heavier) / figure(base), 1.0 / COIN_SCALE,
                                       delta=1e-6, msg=label)
            prices, heavier_prices = base._material_prices(), heavier._material_prices()
            self.assertGreater(len(prices), 100)
            for material in sorted(prices):
                expected = prices[material] / base.labour.wage_per_hour("labourer")
                self.assertAlmostEqual(heavier_prices[material] / heavier.labour.wage_per_hour("labourer"),
                                       expected, delta=1e-6 * max(expected, 1e-9), msg=material)


if __name__ == "__main__":
    unittest.main()
