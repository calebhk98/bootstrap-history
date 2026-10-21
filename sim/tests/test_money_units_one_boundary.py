"""Every money figure reaches the player in the civilisation's own coin through one conversion: labour hours ->
civilisation money. Called on the civilisations' derived tree and wage schedule; the same in running games is in
test_money_units_one_boundary_scenario."""
import copy
import unittest

from sim.engine import data, node_revenue
from sim.engine.wage_schedule import build_schedule

BASE_CIVS = ["rome_100ad", "han_china_100ad"]
MOD_CIV = "sample_egypt_100bc_e7k2:egypt"
ALL_CIVS = BASE_CIVS + [MOD_CIV]
COIN_SCALE = 2.5


def civ_with_coin_scale(name, scale):
    civ = copy.deepcopy(data.load_civ(name))
    civ["coin_standard"]["kg_per_unit"] *= scale
    return civ


def derived(civ):
    """(the tree derived for the civilisation, its wage schedule)."""
    _tree, _document, nodes, _wages, _goods = data.load(civilization_id=civ["id"])
    schedule = build_schedule(data.TRADE_REGISTRY, civ)
    return node_revenue.for_civilisation(nodes, civ, schedule), schedule


def reference_concern(*trees):
    """A revenue-earning node picked by a rule, not by name: the cheapest to build (in the first tree) among those
    that take more than they cost to keep in every tree given."""
    first = trees[0]
    for _cost, node_id in sorted((node["_total_cost"], node_id) for node_id, node in first.items()
                                 if node["rev_hours"] > node["up_hours"] > 0 and node.get("_total_cost", 0) > 0):
        if all(tree[node_id]["rev_hours"] > tree[node_id]["up_hours"] > 0 for tree in trees):
            return node_id
    raise AssertionError("no revenue-earning node pays its keep in every tree")


def labourer_years_of_revenue(tree, schedule, node_id):
    """One concern's yearly takings in labourer-years, both in hours of labour."""
    return tree[node_id]["rev_hours"] / (schedule.annual_wage("labourer") / schedule.money_per_labour_hour)


class RevenueIsInTheCivilisationsCoin(unittest.TestCase):

    def test_node_revenue_in_labour_hours_ignores_the_coin(self):
        # A node's revenue is its output at the civilisation's own prices, so civilisations differ in hours (land
        # rent, wage ratios); the same civilisation with a heavier coin does not.
        rome, rome_schedule = derived(data.load_civ("rome_100ad"))
        heavier, heavier_schedule = derived(civ_with_coin_scale("rome_100ad", COIN_SCALE))
        node_id = reference_concern(rome, heavier)
        self.assertAlmostEqual(heavier[node_id]["rev_hours"], rome[node_id]["rev_hours"],
                               delta=rome[node_id]["rev_hours"] * 1e-9)
        self.assertAlmostEqual(heavier_schedule.money_per_labour_hour, rome_schedule.money_per_labour_hour / COIN_SCALE,
                               delta=rome_schedule.money_per_labour_hour * 1e-9)
        for name, value in (("rome", rome[node_id]["rev_hours"]), ("heavier rome", heavier[node_id]["rev_hours"])):
            self.assertGreater(value, 0.0, name)

    def test_civilisations_differ_in_hours_of_revenue(self):
        trees = {name: derived(data.load_civ(name))[0] for name in ALL_CIVS}
        node_id = reference_concern(*trees.values())
        self.assertEqual(len({round(tree[node_id]["rev_hours"], 6) for tree in trees.values()}), len(ALL_CIVS))

    def test_revenue_to_wage_ratio_stays_near_romes_in_every_civilisation(self):
        built = {name: derived(data.load_civ(name)) for name in ALL_CIVS}
        node_id = reference_concern(*[tree for tree, _schedule in built.values()])
        rome_ratio = labourer_years_of_revenue(*built["rome_100ad"], node_id)
        for name, (tree, schedule) in built.items():
            ratio = labourer_years_of_revenue(tree, schedule, node_id)
            self.assertGreater(ratio, rome_ratio / 3.0, name)
            self.assertLess(ratio, rome_ratio * 3.0, name)


class MaterialPricesAreInHours(unittest.TestCase):

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


if __name__ == "__main__":
    unittest.main()
