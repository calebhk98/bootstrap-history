"""Complaint 595, the rules: each lever of a government's record changes the field its budget, revenue, works or surplus
code reads, and a request that is not the seat's to make is a refusal with a cause. Each test builds a Government record
and calls the rule: `set_lever`, then `budget.standing_lines`, `revenue.assess`, `state_works.gaps` or
`Government.build_works` on a stand-in world."""

QUICK_TOPIC = True

import unittest
from types import SimpleNamespace
from unittest import mock

from sim.agents import budget, government_levers, revenue, state_works
from sim.agents.api import ExportPolicy, Government
from sim.agents.records import ActorRecord
from sim.agents.tuning_spending import RESERVE_CEILING_YEARS_OF_NEED
from sim.refusal import Refusal

from .agents_fake_world import FakeWorld

WAGE = 10.0
GRAIN = "wheat_kg"
FORMS = [{"form": "land_tax", "basis": "harvest", "rate": 0.1},
         {"form": "poll_tax", "basis": "adult_labour_years", "rate": 0.02}]


class LeverWorld(FakeWorld):
    """A country that keeps an army, officials and a dole, and has a coast the navy can be sized to."""

    def __init__(self, money=0.0):
        super().__init__()
        self.state = Government("government:home", ActorRecord(kind="government", money=money))
        self.prices = {GRAIN: 2.0, "ship": 50.0, "iron_bar_kg": 1.0}
        self.forms = FORMS

    def government(self):
        return self.state

    def army_wanted(self):
        return 1000.0

    def threat_pressure(self):
        return 0.0

    def territory(self):
        return SimpleNamespace(frontier_km=0.0, coast_km=0.0, road_km=0.0)

    def urban_population(self):
        return 1000.0

    def state_weights(self):
        return {}

    def pay_per_person_year(self, trade):
        return WAGE

    def national_people(self, trade):
        return 1.0e6

    def subsistence_kg_per_person_year(self):
        return 200.0

    def commodity_of(self, material):
        return material

    def revenue_assessments(self):
        return []

    def soldiers_under_arms(self):
        return 0.0

    def revenue_forms(self):
        return government_levers.revenue_forms(self.forms, self.state.record)

    def country_strata(self):
        return []

    def need_floor_costs_per_person_year(self):
        return {}

    def local_staff(self, trade, people):
        return people

    def population_total(self):
        return 1.0e5

    def state_capacity(self):
        return 0.5

    def equipment_kg_per_soldier(self):
        return 0.0

    def trade_exists(self, trade):
        return True

    def fleet_goods(self, holder_id=None):
        return [{"material": "ship", "life": 10.0, "crew": {"sailor": 10.0}, "held": 0.0}]


def context(population=1.0e5):
    return government_levers.LeverContext(FORMS, {GRAIN, "salt_kg", "ship"}, population)


def lever(kind, name=None, value=None, **more):
    return dict({"lever": kind, "name": name, "value": value}, **more)


def lines_of(world):
    return {line.name: line for line in budget.standing_lines(world)}


class LeverRules(unittest.TestCase):
    def test_a_lever_answers_the_change_it_made(self):
        record = ActorRecord(kind="government")
        change = government_levers.set_lever(record, lever("army", None, 500), context())
        self.assertEqual((change["lever"], change["before"], change["after"]), ("army", None, 500.0))
        again = government_levers.set_lever(record, lever("army", None, 700), context())
        self.assertEqual((again["before"], again["after"]), (500.0, 700.0))
        cleared = government_levers.set_lever(record, lever("army"), context())
        self.assertEqual((cleared["before"], cleared["after"], record.levers), (700.0, None, {}))

    def test_the_army_lever_is_the_force_the_budget_keeps(self):
        world = LeverWorld()
        self.assertEqual(lines_of(world)["army"].labour["soldier"], 1000.0)
        government_levers.set_lever(world.state.record, lever("army", None, 400), context())
        self.assertEqual(lines_of(world)["army"].labour["soldier"], 400.0)
        self.assertEqual(budget.army_wanted(world), 400.0)

    def test_an_army_of_none_drops_the_line(self):
        world = LeverWorld()
        government_levers.set_lever(world.state.record, lever("army", None, 0), context())
        self.assertNotIn("army", lines_of(world))

    def test_a_budget_share_keeps_that_share_of_the_line(self):
        world = LeverWorld()
        full = lines_of(world)["dole"]
        government_levers.set_lever(world.state.record, lever("budget", "dole", 0.25), context())
        cut = lines_of(world)["dole"]
        self.assertAlmostEqual(cut.money, 0.25 * full.money)
        self.assertAlmostEqual(sum(cut.materials.values()), 0.25 * sum(full.materials.values()))
        self.assertAlmostEqual(lines_of(world)["administration"].money, budget.administration_line(world)[0].money)

    def test_the_navy_lever_sizes_the_fleet(self):
        world = LeverWorld()
        self.assertNotIn("navy", lines_of(world))
        government_levers.set_lever(world.state.record, lever("navy", None, 4), context())
        self.assertEqual(lines_of(world)["navy"].labour["sailor"], 40.0)

    def test_a_works_lever_is_the_stock_the_state_wants(self):
        world = LeverWorld()
        self.assertEqual(state_works.gaps(world), [])
        government_levers.set_lever(world.state.record, lever("works", "water_works", 5000), context())
        world.state.record.works_stock = {"fortifications": 0.0, "water_works": 1000.0, "capital_buildings": 0.0}
        gaps = {work.name: gap for work, gap in state_works.gaps(world)}
        self.assertEqual(gaps, {"water_works": 4000.0})

    def test_a_subsidy_and_a_mandate_are_lines_the_budget_pays(self):
        world = LeverWorld()
        government_levers.set_lever(world.state.record, lever("subsidy", GRAIN, 300), context())
        government_levers.set_lever(world.state.record, lever("mandate", GRAIN, 5), context())
        lines = lines_of(world)
        self.assertEqual(lines["subsidy " + GRAIN].transfer, 300.0)
        self.assertEqual(lines["mandate " + GRAIN].materials, {GRAIN: 5.0})
        self.assertEqual(lines["mandate " + GRAIN].material_cost, 10.0)

    def test_a_monopoly_lever_is_the_set_the_export_policy_holds_back(self):
        record = ActorRecord(kind="government")
        government_levers.set_lever(record, lever("monopoly", "salt_kg", True), context())
        self.assertEqual(record.state_monopolies, {"salt_kg"})
        government = Government("government:home", record, ExportPolicy())
        self.assertEqual(government.exports_allowed(["salt_kg", GRAIN]), [GRAIN])
        government_levers.set_lever(record, lever("monopoly", "salt_kg", False), context())
        self.assertEqual(record.state_monopolies, set())

    def test_a_declared_forms_rate_is_the_rate_revenue_is_assessed_at(self):
        world = LeverWorld()
        world.harvest_tonnes = lambda: 100.0
        before = revenue.assess(world)[0]
        government_levers.set_lever(world.state.record, lever("revenue", "land_tax", 0.2), context())
        after = revenue.assess(world)[0]
        self.assertEqual((before.rate, after.rate), (0.1, 0.2))
        self.assertAlmostEqual(after.money, 2.0 * before.money)

    def test_a_started_form_joins_the_declared_ones(self):
        record = ActorRecord(kind="government")
        change = government_levers.set_lever(record, lever("revenue", "salt_tax", 0.05, basis="exports_value"), context())
        self.assertTrue(change["new_form"])
        forms = government_levers.revenue_forms(FORMS, record)
        self.assertEqual([form["form"] for form in forms], ["land_tax", "poll_tax", "salt_tax"])
        self.assertEqual(forms[2]["basis"], "exports_value")

    def test_clearing_a_rate_restores_the_files_figure(self):
        record = ActorRecord(kind="government")
        government_levers.set_lever(record, lever("revenue", "land_tax", 0.5), context())
        government_levers.set_lever(record, lever("revenue", "land_tax"), context())
        self.assertEqual(government_levers.revenue_forms(FORMS, record), FORMS)

    def test_a_reserve_lever_is_the_reserve_held_before_a_surplus_is_spent(self):
        need = 100.0
        years = RESERVE_CEILING_YEARS_OF_NEED + 3.0
        world = LeverWorld(money=years * need)
        government_levers.set_lever(world.state.record, lever("reserve", None, years + 1.0), context())
        with mock.patch.object(Government, "restock_granary", return_value=0.0), \
                mock.patch.object(state_works, "gaps", return_value=[(state_works.WORKS[-1], 10.0)]), \
                mock.patch.object(state_works, "held", return_value={"capital_buildings": 0.0}):
            world.state.build_works([budget.Line("army", "requisition", {}, need)], world)
        self.assertEqual(world.state.record.outlays, {})
        self.assertEqual(government_levers.reserve_years(world.state.record, 0.0), years + 1.0)


class LeverRefusals(unittest.TestCase):
    def refused(self, request, cause, context_=None):
        record = ActorRecord(kind="government")
        result = government_levers.set_lever(record, request, context_ or context())
        self.assertIsInstance(result, Refusal)
        self.assertEqual(result.cause, cause)
        self.assertEqual((record.levers, record.state_monopolies), ({}, set()))   # nothing was changed
        return result

    def test_an_unknown_lever_lists_the_levers(self):
        result = self.refused(lever("tithe", None, 1), "unknown_lever")
        self.assertEqual(result.choices, list(government_levers.LEVER_KINDS))

    def test_an_unknown_name_lists_the_names(self):
        self.assertIn("dole", self.refused(lever("budget", "moat", 0.5), "unknown_name").choices)
        self.assertIn("water_works", self.refused(lever("works", "moat", 5), "unknown_name").choices)
        self.assertIn(GRAIN, self.refused(lever("subsidy", "gold_dust", 5), "unknown_name").choices)
        self.assertEqual(self.refused(lever("revenue", "salt_tax", 0.1), "unknown_name").choices, ["land_tax", "poll_tax"])

    def test_a_base_the_economy_does_not_model_is_refused(self):
        self.assertIn("harvest", self.refused(lever("revenue", "salt_tax", 0.1, basis="moonlight"), "unknown_basis").choices)

    def test_a_value_out_of_range_is_refused_with_its_limits(self):
        for request in (lever("revenue", "land_tax", 1.5), lever("revenue", "land_tax", -0.1), lever("budget", "dole", 2),
                        lever("army", None, 1.0e9), lever("navy", None, -1), lever("works", "water_works", -5),
                        lever("reserve", None, -1), lever("subsidy", GRAIN, -1), lever("mandate", GRAIN, -1)):
            result = self.refused(request, "value_out_of_range")
            self.assertLessEqual(result.facts["low"], result.facts["high"])

    def test_a_value_that_is_not_a_number_is_refused(self):
        for value in ("many", True, float("nan"), [1]):
            self.refused(lever("army", None, value), "value_not_number")

    def test_a_monopoly_takes_true_or_false(self):
        self.refused(lever("monopoly", "salt_kg", 1), "value_not_boolean")
        self.refused(lever("monopoly", "gold_dust", True), "unknown_name")

    def test_clearing_a_rate_never_set_is_refused(self):
        self.refused(lever("revenue", "land_tax"), "nothing_to_clear")


if __name__ == "__main__":
    unittest.main()
