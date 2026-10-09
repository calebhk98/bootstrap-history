"""Every money figure reaches the player in the civilisation's own coin
through one conversion: labour hours -> civilisation money."""
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
    """One shared, never-mutated game per civilisation (or per coin-scaled Rome)."""
    if name not in _PLAIN_GAMES:
        if name == "heavier_rome":
            _PLAIN_GAMES[name] = build(civ_with_coin_scale("rome_100ad", COIN_SCALE))
        else:
            _PLAIN_GAMES[name] = build(data.load_civ(name))
    return _PLAIN_GAMES[name]


def civ_with_coin_scale(name, scale):
    civ = copy.deepcopy(data.load_civ(name))
    civ["coin_standard"]["kg_per_unit"] *= scale
    return civ


def reference_concern(sim):
    """A revenue-earning node picked by a rule, not by name: the cheapest to
    build among those that earn more than they cost to keep."""
    candidates = sorted(
        (node["_total_cost"], node_id) for node_id, node in sim.nodes.items()
        if node["rev"] > node["up"] > 0 and node["_total_cost"] > 0)
    return candidates[0][1]


def labourer_annual_wage(sim):
    return sim.labour.wage_schedule().annual_wage("labourer")


def takings_per_wage(sim, node_id):
    """One concern's yearly takings in labourer-years, with the civilisation's
    price level and output factor divided out."""
    factors = sim.price_index * sim.state.economy.output_factor
    return sim.concern_takings(node_id, 1.0) / factors / labourer_annual_wage(sim)


def open_concern(sim, node_id):
    sim.done.add(node_id)
    sim.operating.add(node_id)
    sim._done_changed()


class RevenueIsInTheCivilisationsCoin(unittest.TestCase):

    def test_node_revenue_in_labour_hours_is_the_same_in_every_civilisation(self):
        sims = {name: plain(name) for name in ALL_CIVS}
        node_id = reference_concern(sims["rome_100ad"])
        hours = {name: sim.nodes[node_id]["rev"] / sim.labour.wage_schedule().money_per_labour_hour
                 for name, sim in sims.items()}
        for name, value in hours.items():
            self.assertAlmostEqual(value, hours["rome_100ad"],
                                   delta=hours["rome_100ad"] * 1e-9, msg=name)

    def test_revenue_to_wage_ratio_stays_near_romes_in_every_civilisation(self):
        rome = plain("rome_100ad")
        node_id = reference_concern(rome)
        rome_ratio = takings_per_wage(rome, node_id)
        for name in ALL_CIVS:
            ratio = takings_per_wage(plain(name), node_id)
            self.assertGreater(ratio, rome_ratio / 3.0, name)
            self.assertLess(ratio, rome_ratio * 3.0, name)


class MaterialPricesAreInHours(unittest.TestCase):

    def test_material_price_over_hourly_wage_ignores_the_coin_standard(self):
        rome = plain("rome_100ad")
        heavier = plain("heavier_rome")
        prices, heavier_prices = rome._material_prices(), heavier._material_prices()
        checked = 0
        for material in sorted(prices):
            expected = prices[material] / rome.labour.wage_per_hour("labourer")
            self.assertAlmostEqual(
                heavier_prices[material] / heavier.labour.wage_per_hour("labourer"),
                expected, delta=1e-6 * max(expected, 1e-9), msg=material)
            checked += 1
        self.assertGreater(checked, 100)

    def test_material_hours_do_not_depend_on_the_coin(self):
        # Hours differ between civilisations (land rent, wage ratios); within
        # one civilisation the coin is only the unit.
        name = "rome_100ad"
        rate = data.starting_schedule(name).money_per_labour_hour
        light = data.calculated_goods_prices([], name, rate)
        heavy = data.calculated_goods_prices([], name, rate * COIN_SCALE)
        self.assertGreater(len(light), 100)
        for material, price in light.items():
            self.assertAlmostEqual(heavy[material] / (rate * COIN_SCALE), price / rate,
                                   delta=price / rate * 1e-9 + 1e-12, msg=material)


class EconomyWorksWithAnyCoin(unittest.TestCase):

    def test_han_can_afford_and_earn_from_a_basic_concern(self):
        han = plain("han_china_100ad")
        rome = plain("rome_100ad")
        node_id = reference_concern(han)

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
            sim = build(data.load_civ(name))
            open_concern(sim, reference_concern(sim))
            years = sim.revenue() / labourer_annual_wage(sim)
            self.assertGreater(years, 0.01, name)
            self.assertLess(years, 5000.0, name)


class CoinMassRescalesEveryFigure(unittest.TestCase):

    def test_every_money_figure_scales_with_the_coin(self):
        base = build(data.load_civ("rome_100ad"))
        heavier = build(civ_with_coin_scale("rome_100ad", COIN_SCALE))
        node_id = reference_concern(base)
        for sim in (base, heavier):
            open_concern(sim, node_id)
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


if __name__ == "__main__":
    unittest.main()
