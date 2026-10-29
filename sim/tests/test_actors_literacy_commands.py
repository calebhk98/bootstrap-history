"""The actors' answers about reading and the commands that move it (sim/actors/literacy_views.py, literacy_rules.py): each test
calls one handler or view over written-out strata, and reads the figures it gives or leaves."""

QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

from sim.actors import literacy_rules
from sim.actors.commands import HoldEdgeGoods, SchoolLiteracy, TeachLiteracy
from sim.actors.module import Actors
from sim.agents.api import ActorsState
from sim.agents.edges import EDGE_THIEVES
from sim.tests import module_harness


def stratum(country, members, literacy, property_share=0.0):
    return SimpleNamespace(record=SimpleNamespace(country=country, members=members, literacy=literacy, exited_year=None,
                                                  plan={"property_share": property_share}))


def actors_over(strata):
    """The actors module whose cast holds `strata` (home country "rome")."""
    module = module_harness.build(Actors, world=ActorsState(home_country="rome"), module_id="actors")
    registry = SimpleNamespace(state=SimpleNamespace(home_country="rome"), of_kind=lambda kind: strata)
    module.seeded_actor_registry = lambda: registry
    return module


class CountryLiteracyViews(unittest.TestCase):
    def test_the_figure_is_the_members_weighted_share_of_the_country_asked_for(self):
        module = actors_over([stratum(None, 10.0, 0.2), stratum("rome", 30.0, 0.6), stratum("gaul", 10.0, 0.9)])
        self.assertAlmostEqual(module.country_literacy_figure(None, "literacy_general"), 0.5)
        self.assertAlmostEqual(module.country_literacy_figure("gaul", "literacy_general"), 0.9)

    def test_the_elite_figure_counts_only_the_propertied_strata(self):
        module = actors_over([stratum(None, 10.0, 0.2), stratum(None, 10.0, 0.8, property_share=0.5)])
        self.assertAlmostEqual(module.country_literacy_figure(None, "literacy_elite"), 0.8)

    def test_the_ceiling_weights_each_groups_own_limit_by_its_members(self):
        module = actors_over([stratum(None, 30.0, 0.2), stratum(None, 10.0, 0.8, property_share=0.5)])
        self.assertAlmostEqual(module.country_literacy_ceiling(None, 0.6, 1.0), 0.7)

    def test_a_preview_of_schooling_answers_the_gain_and_leaves_every_stratum_as_it_was(self):
        strata = [stratum(None, 10.0, 0.2)]
        before, after = actors_over(strata).literacy_after_schooling(None, (("literacy_general", 0.5, 0.6),))
        self.assertAlmostEqual(after["literacy_general"] - before["literacy_general"], 0.2)
        self.assertEqual(strata[0].record.literacy, 0.2)


class LiteracyCommands(unittest.TestCase):
    def test_schooling_closes_the_gap_of_each_step_in_order_and_answers_the_figures_before_and_after(self):
        strata = [stratum(None, 10.0, 0.2)]
        before, after = actors_over(strata).school_literacy(SchoolLiteracy((("literacy_general", 0.5, 0.6),)))
        self.assertAlmostEqual(before["literacy_general"], 0.2)
        self.assertAlmostEqual(after["literacy_general"], 0.4)
        self.assertAlmostEqual(strata[0].record.literacy, 0.4)

    def test_teaching_moves_the_figure_toward_the_value_but_not_past_the_ceiling(self):
        strata = [stratum(None, 10.0, 0.2)]
        actors_over(strata).teach_literacy(TeachLiteracy("literacy_general", 0.9, 0.5))
        self.assertAlmostEqual(strata[0].record.literacy, 0.5)


class HoldEdgeGoodsCommand(unittest.TestCase):
    def test_an_edge_holds_the_goods_it_is_given_added_to_what_it_had(self):
        state = ActorsState(home_country="rome")
        module = module_harness.build(Actors, world=state, module_id="actors")
        module.hold_edge_goods(HoldEdgeGoods(EDGE_THIEVES, "grain", 2.0))
        module.hold_edge_goods(HoldEdgeGoods(EDGE_THIEVES, "grain", 1.5))
        self.assertEqual(state.edge_goods, {EDGE_THIEVES: {"grain": 3.5}})


class SchoolRule(unittest.TestCase):
    def test_the_rule_answers_both_figures_before_and_after_in_the_report_order(self):
        class Country:
            def __init__(self):
                self.values = {"literacy_general": 0.1, "literacy_elite": 0.5}

            def get(self, field):
                return self.values[field]

            def school(self, field, fraction, ceiling):
                self.values[field] += fraction * (ceiling - self.values[field])
        before, after = literacy_rules.school(Country(), (("literacy_elite", 0.5, 0.9), ("literacy_general", 1.0, 0.3)))
        self.assertEqual((list(before), before["literacy_elite"], after["literacy_elite"], after["literacy_general"]),
                         (["literacy_general", "literacy_elite"], 0.5, 0.7, 0.3))


if __name__ == "__main__":
    unittest.main()
