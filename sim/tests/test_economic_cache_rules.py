"""The memoised economic readers (Complaint 640) recompute exactly when the state they read changes, on stand-ins that carry only what
each method reads: `revenue`, `annual_material_demand` and the goods-category ratios. Whether the version counters move when the
household is edited is test_household_invalidation_containers."""
QUICK_TOPIC = True

import types
import unittest

from sim.engine.economy_goods import GoodsMixin
from sim.engine.economy_production import ProductionMixin
from sim.tests import materials_stand_in


def household(**versions):
    fields = dict(operating_version=0, done_version=0, active_version=0, workforce_version=0, institution_units_version=0,
                  wage_hours_this_year=0.0, directors_extra=0.0, bondage_years_left=0.0, freedmen=0.0, slaves=0.0,
                  reputation=0.0)
    fields.update(versions)
    return types.SimpleNamespace(**fields)


class RevenueStandIn(ProductionMixin):
    """What `revenue` reads, with the uncached sum counted."""

    def real_output_per_head(self):
        return self.state.economy.output_per_head

    def view(self, name):   # the polity module's standing
        return lambda: {"governance": 0.0, "reputation": 0.0}

    def __init__(self):
        self.pop_scale = 1.0
        self.household = household()
        self.computed = 0
        self.year = 100
        self.price_level = 1.0
        self.output_factor = 1.0
        self.state = types.SimpleNamespace(
            scenario=types.SimpleNamespace(year=100), economy=types.SimpleNamespace(output_per_head=1.0),
            holdings=types.SimpleNamespace(farm_hectares=0.0), projects=types.SimpleNamespace(),
            household=self.household, governance=types.SimpleNamespace(gov=0.0))
        self.founder_alive = True
        self.labour = types.SimpleNamespace(director_hours_committed=lambda: 0.0, wage_signature=lambda: 0)

    def state_funding(self):
        return 0.0

    def home_price_level(self):
        return self.price_level

    def _compute_revenue_uncached(self):
        self.computed += 1
        return (3.0 * self.computed, 1.0)


class RevenueMemoTest(unittest.TestCase):
    def test_a_repeated_call_on_unchanged_state_computes_once_and_returns_the_same_sum(self):
        sim = RevenueStandIn()
        first = sim.revenue()
        self.assertEqual(sim.revenue(), first)
        self.assertEqual(sim.computed, 1)

    def test_each_input_the_key_names_forces_a_recompute(self):
        changes = {
            "operating": lambda sim: setattr(sim.household, "operating_version", 1),
            "done": lambda sim: setattr(sim.household, "done_version", 1),
            "workforce": lambda sim: setattr(sim.household, "workforce_version", 1),
            "freedmen": lambda sim: setattr(sim.household, "freedmen", 10.0),
            "year": lambda sim: setattr(sim.state.scenario, "year", 101),
            "farmland": lambda sim: setattr(sim.state.holdings, "farm_hectares", 5.0),
            "price level": lambda sim: setattr(sim, "price_level", 1.5),
            "output factor": lambda sim: setattr(sim, "output_factor", 0.5),
        }
        for name, change in sorted(changes.items()):
            sim = RevenueStandIn()
            sim.revenue()
            change(sim)
            sim.revenue()
            self.assertEqual(sim.computed, 2, name)

    def test_capacity_sells_no_hours_and_leaves_the_household_as_it_was(self):
        sim = RevenueStandIn()
        sim.household.wage_hours_this_year = 40.0
        sim.revenue()
        sim.revenue_capacity()
        self.assertEqual(sim.household.wage_hours_this_year, 40.0)
        self.assertEqual(sim.computed, 2)
        sim.revenue()
        self.assertEqual(sim.computed, 3)


class MaterialDemandStandIn:
    """The materials module over a tree, a set of active projects and the version counters that say they changed."""

    def __init__(self, nodes, active):
        self.household = household()
        self.active = list(active)
        projects = types.SimpleNamespace(done=set(), active={}, active_keys_sorted=lambda: sorted(self.active))
        self.module = materials_stand_in.build(
            tree_nodes=nodes, legacy_projects=projects,
            project_versions=lambda: (self.household.active_version, self.household.done_version))

    def annual_material_demand(self):
        return self.module.annual_material_demand()


NODES = {"smelter": {"build_yrs": 2.0, "mat": {"iron_kg": 4000.0}}, "kiln": {"yrs": 1.0, "mat": {"clay_kg": 1000.0}}}


class AnnualMaterialDemandTest(unittest.TestCase):
    def test_demand_is_each_active_projects_materials_spread_over_its_years_in_tonnes(self):
        demand = MaterialDemandStandIn(NODES, ["smelter"]).annual_material_demand()
        self.assertAlmostEqual(demand["iron_kg"], 2.0)
        self.assertNotIn("clay_kg", demand)

    def test_changing_the_active_set_changes_the_demand(self):
        sim = MaterialDemandStandIn(NODES, ["smelter"])
        sim.annual_material_demand()
        sim.active.append("kiln")
        sim.household.active_version += 1
        self.assertAlmostEqual(sim.annual_material_demand()["clay_kg"], 1.0)

    def test_finishing_a_project_changes_the_demand_through_the_done_version(self):
        sim = MaterialDemandStandIn(NODES, ["smelter", "kiln"])
        sim.annual_material_demand()
        sim.active.remove("kiln")
        sim.household.done_version += 1
        self.assertNotIn("clay_kg", sim.annual_material_demand())

    def test_progress_that_leaves_the_same_projects_active_keeps_the_figure(self):
        sim = MaterialDemandStandIn(NODES, ["smelter"])
        first = sim.annual_material_demand()
        sim.household.active_version += 1
        self.assertEqual(sim.annual_material_demand(), first)

    def test_the_caller_gets_a_copy_it_may_edit(self):
        sim = MaterialDemandStandIn(NODES, ["smelter"])
        sim.annual_material_demand()["fake_kg"] = 999.0
        self.assertNotIn("fake_kg", sim.annual_material_demand())
        sim.household.active_version += 1
        sim.annual_material_demand()["fake_kg"] = 999.0
        self.assertNotIn("fake_kg", sim.annual_material_demand())


class GoodsStandIn(GoodsMixin):
    GOODS_TAU_POP_SCALE_EXPONENT = 0.0

    def real_output_per_head(self):
        return self.state.economy.output_per_head

    def __init__(self, concerns):
        self.concerns = concerns
        self.calls = 0
        self.pop_scale = 1.0
        self.market_version = 0
        self.household = household()
        self.state = types.SimpleNamespace(scenario=types.SimpleNamespace(year=100), projects=types.SimpleNamespace(),
                                           economy=types.SimpleNamespace(output_per_head=1.0),
                                           holdings=types.SimpleNamespace(farm_hectares=0.0))

    def actor_market_version(self):
        return self.market_version

    def _goods_category_state(self, cat):
        self.calls += 1
        return (self.concerns, 0.0, {"tau": 10.0, "eta": 1.0, "floor": 0.1}) if self.concerns else None

    def goods_reach_factor(self):
        return 1.0

    def income_factor(self):
        return 1.0


class GoodsCategoryRatiosTest(unittest.TestCase):
    def test_a_repeated_question_is_answered_from_the_first_computation(self):
        sim = GoodsStandIn(1)
        first = sim._goods_category_ratios("textiles")
        self.assertEqual(sim._goods_category_ratios("textiles"), first)
        self.assertEqual(sim.calls, 1)

    def test_a_change_of_operating_set_or_actor_market_recomputes(self):
        sim = GoodsStandIn(1)
        sim._goods_category_ratios("textiles")
        sim.household.operating_version += 1
        sim._goods_category_ratios("textiles")
        sim.market_version += 1
        sim._goods_category_ratios("textiles")
        self.assertEqual(sim.calls, 3)

    def test_nothing_operating_in_the_category_gives_no_ratios_and_a_neutral_factor(self):
        sim = GoodsStandIn(0)
        self.assertIsNone(sim._goods_category_ratios("textiles"))
        self.assertEqual(sim.goods_category_factor("textiles"), 1.0)

    def test_a_second_concern_in_the_category_lowers_each_sellers_factor(self):
        single = GoodsStandIn(1).goods_category_factor("textiles")
        double = GoodsStandIn(2).goods_category_factor("textiles")
        self.assertLess(double, single)

    def test_the_factor_is_remembered_until_the_operating_set_changes(self):
        sim = GoodsStandIn(1)
        first = sim.goods_category_factor("textiles")
        sim.concerns = 2
        self.assertEqual(sim.goods_category_factor("textiles"), first)
        sim.household.operating_version += 1
        self.assertLess(sim.goods_category_factor("textiles"), first)


if __name__ == "__main__":
    unittest.main()
