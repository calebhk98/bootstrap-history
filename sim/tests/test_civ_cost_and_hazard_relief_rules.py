"""What a society finds harder to build, what money a quoted cost means, what built defences take off a hazard, and how a
value weight moves, called with figures built here (Complaint 640; from the first playtests)."""
QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

from sim.diffusion.civ_cost import civ_cost_factor, multiplier_for
from sim.engine.core import Sim
from sim.hazards import constants
from sim.tests import hazards_host
from sim.tests import projects_host
from sim.polity.value_weight import VALUE_WEIGHT_CEILING, VALUE_WEIGHT_FLOOR, shifted
from sim.labour.labour_population import PopulationMixin

MULTIPLIERS = {"ships": 0.5, "infrastructure": 2.0, "commerce": 1.5, "chemical": 3.0}
REMEDIES = {"infrastructure": {"node": "public_works_office", "residual": 1.2}}


class CivCostTests(unittest.TestCase):
    def factor(self, category, traits, done=(), multipliers=MULTIPLIERS, remedies=REMEDIES):
        return civ_cost_factor(multipliers, remedies, set(done), category, traits)

    def test_a_society_with_no_table_builds_at_the_base_cost(self):
        self.assertEqual(civ_cost_factor(None, None, set(), "ships", ["commerce"]), 1.0)
        self.assertEqual(civ_cost_factor({}, {}, set(), "ships", []), 1.0)

    def test_a_category_in_the_table_sets_the_factor(self):
        self.assertEqual(self.factor("ships", []), 0.5)

    def test_traits_colour_a_known_craft_at_a_damped_exponent_not_at_full_weight(self):
        with_trait = self.factor("ships", ["infrastructure", "commerce"])
        self.assertAlmostEqual(with_trait, 0.5 * 2.0 ** 0.25 * 1.5 ** 0.25)
        self.assertLess(with_trait, 0.5 * 2.0 * 1.5)

    def test_a_craft_the_society_is_best_at_stays_cheaper_than_the_base_despite_dear_traits(self):
        self.assertLess(self.factor("ships", ["infrastructure", "commerce"]), 1.0)

    def test_without_a_craft_in_the_table_traits_apply_at_full_weight(self):
        self.assertAlmostEqual(self.factor("tools", ["infrastructure", "commerce"]), 2.0 * 1.5)

    def test_a_trait_not_in_the_table_is_ignored(self):
        self.assertEqual(self.factor("ships", ["inexplicable"]), 0.5)
        self.assertEqual(self.factor("tools", ["inexplicable"]), 1.0)

    def test_a_remedy_lifts_the_handicap_to_its_residual_once_its_node_is_done(self):
        before = self.factor("tools", ["infrastructure"])
        after = self.factor("tools", ["infrastructure"], done=["public_works_office"])
        self.assertEqual(before, 2.0)
        self.assertEqual(after, 1.2)
        self.assertLess(after, before)

    def test_a_remedy_whose_node_is_not_done_changes_nothing(self):
        self.assertEqual(self.factor("tools", ["infrastructure"], done=["something_else"]), 2.0)

    def test_a_remedy_with_no_residual_removes_the_handicap(self):
        self.assertEqual(multiplier_for("infrastructure", MULTIPLIERS, {"infrastructure": {"node": "x"}}, {"x"}), 1.0)

    def test_a_remedy_applies_to_the_category_too(self):
        remedies = {"chemical": {"node": "lab", "residual": 1.0}}
        self.assertEqual(self.factor("chemical", [], remedies=remedies), 3.0)
        self.assertEqual(self.factor("chemical", [], done=["lab"], remedies=remedies), 1.0)


class MoneyFactorTests(unittest.TestCase):
    def test_a_quoted_cost_means_the_price_level_and_not_the_coins_silver(self):
        money_real = [1.0]
        module = projects_host.build(price_index=1.7, money_real=lambda: money_real[0])
        before = module.cost_money_factor()
        money_real[0] = 0.005
        self.assertEqual(module.cost_money_factor(), before)
        self.assertEqual(before, 1.7)


def rows_of(counters):
    """The mechanics module's rows ({kind: [(order, node, share, label)]}) of a table of counters."""
    return {kind: [(index, node, share, label) for index, (node, share, label) in enumerate(entries)]
            for kind, entries in counters.items()}


class Defended:
    """The hazards module over a table of counters, which of them stand (running) or are shut (built, not running), the
    own mines and what the country has adopted."""

    def __init__(self, running=(), closed=(), counters=None, gold=0.0, silver=0.0, adopted=None):
        counters = counters if counters is not None else {
            "staff_loss": [("sanitation", 0.4, "sanitation"), ("quarantine", 0.5, "quarantine")],
            "sack_chance": [("walls", 0.5, "walls"), ("cannon", 0.4, "cannon"), ("garrison", 0.5, "garrison")]}
        standing, adopted = set(running), adopted or {}
        self.module = hazards_host.build(
            hazard_counter_rows=rows_of(counters), techniques_held=standing | set(closed), running=lambda node: node in standing,
            tree=lambda node: {"name": node}, civ_diffusion=lambda node: adopted.get(node, 0.0),
            mine_capacity={"gold": gold, "silver": silver})

    def hazard_relief(self, kind, beyond_national=False):
        return self.module.hazard_relief(kind, beyond_national)


class HazardReliefTests(unittest.TestCase):
    def test_with_nothing_built_a_hazard_is_not_blunted(self):
        self.assertEqual(Defended().hazard_relief("staff_loss"), (1.0, []))

    def test_medicine_blunts_a_plague(self):
        relief, why = Defended({"sanitation"}).hazard_relief("staff_loss")
        self.assertAlmostEqual(relief, 0.6)
        self.assertEqual(why, ["sanitation"])

    def test_each_defence_removes_a_share_of_what_is_left_so_five_partial_answers_are_strong(self):
        relief, _ = Defended({"sanitation", "quarantine"}).hazard_relief("staff_loss")
        self.assertAlmostEqual(relief, 0.6 * 0.5)

    def test_a_defence_shut_down_blunts_by_the_part_that_lingers(self):
        relief, why = Defended(closed={"sanitation"}).hazard_relief("staff_loss")
        self.assertAlmostEqual(relief, 1.0 - 0.4 * constants.KNOWLEDGE_RESIDUE_AFTER_CLOSURE)
        self.assertIn("lapsed", why[0])      # a part-standing defence is told as closed

    def test_your_own_gold_mine_blunts_a_debasement(self):
        self.assertAlmostEqual(Defended(gold=1.0).hazard_relief("real_erosion")[0], 1.0 - constants.HAZARD_EROSION_OWN_GOLD)
        self.assertEqual(Defended(gold=0.0).hazard_relief("real_erosion")[0], 1.0)

    def test_a_trace_of_gold_does_not_count_as_a_mine(self):
        self.assertEqual(Defended(gold=0.0004).hazard_relief("real_erosion")[0], 1.0)

    def test_your_own_silver_mine_blunts_it_less_than_gold(self):
        gold = Defended(gold=1.0).hazard_relief("real_erosion")[0]
        silver = Defended(silver=1.0).hazard_relief("real_erosion")[0]
        self.assertLess(gold, silver)
        self.assertLess(silver, 1.0)

    def test_every_military_counter_standing_blunts_a_sacking_but_never_zeroes_it(self):
        everything = Defended({"walls", "cannon", "garrison"})
        relief, why = everything.hazard_relief("sack_chance")
        self.assertGreater(relief, 0.0)
        self.assertLess(relief, Defended().hazard_relief("sack_chance")[0])
        self.assertEqual(len(why), 3)

    def test_what_the_country_has_adopted_does_not_count_twice_for_the_household(self):
        alone = Defended({"sanitation"}).hazard_relief("staff_loss", beyond_national=True)[0]
        adopted = Defended({"sanitation"}, adopted={"sanitation": 0.5}).hazard_relief("staff_loss", beyond_national=True)[0]
        self.assertGreater(adopted, alone)
        self.assertAlmostEqual(adopted, 1.0 - 0.4 * 0.5)

    def test_a_kind_with_no_counters_is_not_blunted(self):
        self.assertEqual(Defended(counters={}).hazard_relief("output_factor")[0], 1.0)


class TradeAvailabilityTests(unittest.TestCase):
    """A trade the society lacks is absent, not dear: only teaching or a school brings it."""

    def population(self, absent=("machinist",), created=(), schools=None):
        world = SimpleNamespace(
            trades_absent=set(absent),
            workforce=SimpleNamespace(trades_created=set(created), trade_schools=schools or {}))
        return SimpleNamespace(_world=world)

    def available(self, trade, **kwargs):
        return PopulationMixin.trade_available(self.population(**kwargs), trade)

    def test_a_trade_the_society_has_is_available(self):
        self.assertTrue(self.available("mason"))

    def test_a_trade_the_society_lacks_is_not(self):
        self.assertFalse(self.available("machinist"))

    def test_teaching_a_trade_into_existence_makes_it_available_but_not_the_others(self):
        self.assertTrue(self.available("machinist", created=["machinist"]))
        self.assertFalse(self.available("chemist", absent=("machinist", "chemist"), created=["machinist"]))

    def test_a_trade_school_makes_the_trade_available(self):
        self.assertTrue(self.available("machinist", schools={"machinist": 1.0}))
        self.assertFalse(self.available("machinist", schools={"machinist": 0.0}))


class ValueWeightTests(unittest.TestCase):
    def test_a_weight_moves_by_the_delta(self):
        self.assertAlmostEqual(shifted(0.5, -0.2, -1.0, 1.5), 0.3)

    def test_a_weight_stops_at_the_floor_and_the_ceiling(self):
        self.assertEqual(shifted(-0.9, -0.5, -1.0, 1.5), -1.0)
        self.assertEqual(shifted(1.4, 0.5, -1.0, 1.5), 1.5)

    def test_the_engines_bounds_are_a_floor_below_a_ceiling(self):
        self.assertLess(VALUE_WEIGHT_FLOOR, VALUE_WEIGHT_CEILING)


if __name__ == "__main__":
    unittest.main()
