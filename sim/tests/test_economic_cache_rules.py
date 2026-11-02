"""The memoised economic readers (Complaint 640) recompute exactly when the state they read changes, on stand-ins that carry only what
each method reads: `revenue`, `annual_material_demand`. Whether the version counters move when the
household is edited is test_household_invalidation_containers."""
QUICK_TOPIC = True

import types
import unittest

from sim.tests import materials_stand_in, production_host
from sim.workforce.api import SetWageHoursSold


def household(**versions):
    fields = dict(operating_version=0, done_version=0, active_version=0, workforce_version=0, institution_units_version=0,
                  wage_hours_this_year=0.0, directors_extra=0.0, bondage_years_left=0.0, freedmen=0.0, slaves=0.0, employees={},
                  reputation=0.0)
    fields.update(versions)
    return types.SimpleNamespace(**fields)


class RevenueStandIn:
    """The views `revenue` reads, under a production module whose uncached sum is counted."""

    def __init__(self):
        self.household = household()
        self.computed = 0
        self.year = 100
        self.price_level = 1.0
        self.output_factor = 1.0
        self.farm_hectares = 0.0
        self.module = production_host.build(
            staff=lambda: {key: getattr(self.household, key) for key in ("directors_extra", "freedmen", "slaves", "employees")},
            staff_version=lambda: self.household.workforce_version,
            hour_commitments=lambda: {"wage_hours": self.household.wage_hours_this_year},
            year=lambda: self.year, output_factor=lambda: self.output_factor, home_price_level=lambda: self.price_level,
            farm_holdings=lambda: {"hectares": self.farm_hectares},
            techniques_version=lambda: self.household.done_version, operating_version=lambda: self.household.operating_version,
            institution_units_version=lambda: self.household.institution_units_version,
            answers={SetWageHoursSold: lambda command: setattr(self.household, "wage_hours_this_year", command.hours)})
        self.module._compute_revenue_uncached = self._compute_revenue_uncached

    def revenue(self):
        return self.module.revenue()

    def revenue_capacity(self):
        return self.module.revenue_capacity()

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
            "institution units": lambda sim: setattr(sim.household, "institution_units_version", 1),
            "operating": lambda sim: setattr(sim.household, "operating_version", 1),
            "done": lambda sim: setattr(sim.household, "done_version", 1),
            "workforce": lambda sim: setattr(sim.household, "workforce_version", 1),
            "freedmen": lambda sim: setattr(sim.household, "freedmen", 10.0),
            "year": lambda sim: setattr(sim, "year", 101),
            "farmland": lambda sim: setattr(sim, "farm_hectares", 5.0),
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
            tree_nodes=nodes, projects_record=projects,
            active_projects_version=lambda: self.household.active_version, techniques_version=lambda: self.household.done_version)

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


if __name__ == "__main__":
    unittest.main()
