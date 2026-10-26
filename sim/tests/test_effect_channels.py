"""The effect channels a work declares in its `mechanics` (Complaint 190's benefactions use them). Each method is called once on a
stand-in `self` whose attributes are written out and whose collaborators are plain lambdas: the mechanics rules `effect_size`,
`grouped_values`, `sum_in_order`, `factor_product`, and the module's `effect_holds`; the readers `standing_floor`, `goods_reach_factor`, `_schooling_flow`; and
`institution_unit_cost`. No game is built. What the benefactions branch declares is test_complaint_190_benefactions."""
import unittest
from types import SimpleNamespace

from sim.engine.core import Sim
from sim.mechanics import rules
from sim.mechanics.module import Mechanics
from sim.tests import module_harness

QUICK_TOPIC = True


class EffectValue(unittest.TestCase):

    def value(self, spec, units=4.0, money_per_hour=2.0):
        return rules.effect_size(spec, lambda: units, lambda: money_per_hour)

    def test_a_flat_effect_is_its_flat_value(self):
        self.assertEqual(self.value({"flat": 1.5}), 1.5)

    def test_a_per_unit_effect_scales_with_the_units(self):
        self.assertEqual(self.value({"per_unit": 3.0}, units=4.0), 12.0)

    def test_a_per_sqrt_unit_effect_scales_with_the_square_root_of_the_units(self):
        self.assertEqual(self.value({"per_sqrt_unit": 3.0}, units=4.0), 6.0)

    def test_a_labour_hour_effect_is_scaled_by_the_money_a_labour_hour_is_worth(self):
        self.assertEqual(self.value({"flat": 1.5, "labour_hours": True}, money_per_hour=2.0), 3.0)


class EffectValues(unittest.TestCase):

    def values(self, terms, holds):
        return rules.grouped_values(terms, lambda node_id, spec: node_id in holds, lambda node_id, spec: spec["flat"])

    def test_a_work_that_does_not_hold_contributes_nothing(self):
        self.assertEqual(self.values([("a", {"flat": 1.0})], holds=()), [])

    def test_a_work_that_holds_contributes_its_value(self):
        self.assertEqual(self.values([("a", {"flat": 1.0})], holds=("a",)), [("a", 1.0)])

    def test_a_group_counts_once_for_its_first_holder_in_declared_order(self):
        terms = [("a", {"flat": 1.0, "group": "patron"}), ("b", {"flat": 2.0, "group": "patron"})]
        self.assertEqual(self.values(terms, holds=("a", "b")), [("a", 1.0)])

    def test_a_group_whose_first_member_does_not_hold_is_counted_by_the_next(self):
        terms = [("a", {"flat": 1.0, "group": "patron"}), ("b", {"flat": 2.0, "group": "patron"})]
        self.assertEqual(self.values(terms, holds=("b",)), [("b", 2.0)])


class EffectHolds(unittest.TestCase):

    def holds(self, spec, running, built):
        module = module_harness.build(Mechanics, views={"running": lambda node_id: running,
                                                        "techniques_held": {"x"} if built else set()})
        return module.effect_holds("x", spec)

    def test_an_ordinary_effect_needs_the_work_running(self):
        self.assertFalse(self.holds({}, running=False, built=True))
        self.assertTrue(self.holds({}, running=True, built=True))

    def test_a_has_gated_effect_needs_the_work_only_built(self):
        self.assertTrue(self.holds({"gate": "has"}, running=False, built=True))


class EffectSumAndFactor(unittest.TestCase):

    def test_the_sum_starts_from_the_base_and_adds_each_value(self):
        self.assertEqual(rules.sum_in_order([("a", 0.5), ("b", 0.25)], 10.0), 10.75)

    def test_the_sum_of_nothing_is_the_base(self):
        self.assertEqual(rules.sum_in_order([], 3.0), 3.0)

    def test_factors_multiply(self):
        terms = [("a", {"factor": 1.5}), ("b", {"factor": 1.6})]
        self.assertAlmostEqual(rules.factor_product(terms, lambda node_id, spec: True, None, 1.0, None), 2.4)

    def test_a_factor_of_a_work_that_does_not_hold_is_left_out(self):
        terms = [("a", {"factor": 1.5}), ("b", {"factor": 1.6})]
        self.assertAlmostEqual(rules.factor_product(terms, lambda node_id, spec: node_id == "b", None, 1.0, None), 1.6)


def standing_game(extra, scandal=0.0):
    asked = []

    def effect_sum(channel, start=0.0):
        asked.append(channel)
        return start + extra
    return SimpleNamespace(effect_sum=effect_sum, asked=asked,
                           state=SimpleNamespace(projects=SimpleNamespace(done=set(), granted=set()),
                                                 household=SimpleNamespace(scandal=scandal)))


class StandingFloor(unittest.TestCase):

    def test_it_asks_the_standing_channel(self):
        game = standing_game(1.0)
        Sim.standing_floor(game)
        self.assertEqual(game.asked, ["standing"])

    def test_it_rises_by_what_the_channel_adds(self):
        self.assertAlmostEqual(Sim.standing_floor(standing_game(1.0)) - Sim.standing_floor(standing_game(0.0)), 1.0)

    def test_scandal_lowers_it(self):
        self.assertLess(Sim.standing_floor(standing_game(0.0, scandal=3.0)), Sim.standing_floor(standing_game(0.0)))


class GoodsReach(unittest.TestCase):

    def reach(self, factor, ceiling=3.0):
        asked = []
        game = SimpleNamespace(effect_factor=lambda channel, start=1.0: asked.append(channel) or factor, REACH_CEILING=ceiling)
        return Sim.goods_reach_factor(game), asked

    def test_it_asks_the_reach_channel_and_returns_the_factor(self):
        self.assertEqual(self.reach(1.5), (1.5, ["reach"]))

    def test_it_is_capped_at_the_ceiling(self):
        self.assertEqual(self.reach(5.0, ceiling=3.0)[0], 3.0)


def school_game(running, values, reaches=None):
    return SimpleNamespace(running=lambda node_id: running, _effect_terms=lambda channel: [("school", {"required": True})],
                           effect_values=lambda channel: values, mechanic=lambda node_id, name: {"reaches": reaches})


class SchoolingFlow(unittest.TestCase):

    def test_it_is_nothing_when_the_required_school_is_shut(self):
        self.assertEqual(Sim._schooling_flow(school_game(False, [("school", 0.5)])), 0.0)

    def test_it_is_the_open_schools_flow(self):
        self.assertEqual(Sim._schooling_flow(school_game(True, [("school", 0.5)])), 0.5)

    def test_it_is_nothing_with_no_school(self):
        self.assertEqual(Sim._schooling_flow(school_game(True, [])), 0.0)

    def test_a_school_that_names_fields_teaches_only_those(self):
        game = school_game(True, [("school", 0.5)], reaches=["general"])
        self.assertEqual(Sim._schooling_flow(game, "general"), 0.5)
        self.assertEqual(Sim._schooling_flow(game, "scientific"), 0.0)


class InstitutionUnitCost(unittest.TestCase):

    def cost(self, have_units, add_units, convexity=0.5, capex=1000.0):
        game = SimpleNamespace(venture_capex=lambda node_id: capex, INSTITUTION_EXPANSION_CONVEXITY=convexity)
        return Sim.institution_unit_cost(game, "college", have_units, add_units)

    def test_the_first_unit_costs_exactly_what_founding_costs(self):
        self.assertEqual(self.cost(0.0, 1.0), 1000.0)

    def test_a_second_unit_costs_more_than_the_first(self):
        self.assertGreater(self.cost(1.0, 1.0), self.cost(0.0, 1.0))

    def test_each_further_unit_costs_more_than_the_one_before(self):
        costs = [self.cost(units, 1.0) for units in range(5)]
        self.assertEqual(costs, sorted(costs))
        self.assertEqual(len(set(costs)), 5)

    def test_with_no_convexity_every_unit_costs_the_same(self):
        self.assertEqual(self.cost(3.0, 1.0, convexity=0.0), 1000.0)

    def test_adding_nothing_costs_nothing(self):
        self.assertEqual(self.cost(2.0, 0.0), 0.0)


if __name__ == "__main__":
    unittest.main()
