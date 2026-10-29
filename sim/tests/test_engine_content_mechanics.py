"""CLAUDE.md 4.7: the engine reads node `mechanics`, never node ids. A node of an id no engine code has seen gets an effect by
declaring the mechanic, and a node that does not declare it gets nothing. Each rule is called on a stand-in `self` holding a
few hand-written nodes; no game. The scan for node ids in the engine's source is `test_engine_content_ids`."""
QUICK_TOPIC = True

import types
import unittest

from sim.seats.api import SeatsSeat
from sim.seats.module import Seats
from sim.knowledge import rules as knowledge_rules
from sim.mechanics.module import Mechanics
from sim.tests import module_harness

MODDED = "mod_x:hall"


def node(mechanics):
    return {"mechanics": mechanics}


def mechanics_over(nodes, running=(), held=()):
    """The mechanics module over hand-written nodes, with `running` and the techniques held read from two sets."""
    return module_harness.build(Mechanics, views={
        "tree_nodes": nodes, "running": lambda node_id: node_id in set(running), "techniques_held": set(held),
        "institution_units": lambda node_id: 1.0, "money_per_labour_hour": 1.0})


class EffectSumTests(unittest.TestCase):
    def test_a_node_of_any_id_declaring_an_effect_adds_its_flat_value(self):
        module = mechanics_over({MODDED: node({"standing": {"flat": 7.0}})}, running=[MODDED])
        self.assertAlmostEqual(module.effect_sum("standing", 10.0), 17.0)

    def test_the_credit_line_channel_is_read_the_same_way(self):
        module = mechanics_over({MODDED: node({"credit_line": {"flat": 1234.0}})}, running=[MODDED])
        self.assertAlmostEqual(module.effect_sum("credit_line", 100.0), 1334.0)

    def test_a_node_whose_data_no_longer_declares_the_effect_adds_nothing(self):
        module = mechanics_over({"patron_imperial": node({})}, running=["patron_imperial"])
        self.assertEqual(module.effect_sum("standing", 10.0), 10.0)

    def test_a_node_that_is_not_running_adds_nothing(self):
        module = mechanics_over({MODDED: node({"standing": {"flat": 7.0}})})
        self.assertEqual(module.effect_sum("standing", 10.0), 10.0)


class RunningWithMechanicTests(unittest.TestCase):
    def test_it_lists_the_running_nodes_declaring_the_mechanic(self):
        nodes = {"a": node({"founder_life_extension": True}), "b": node({"founder_life_extension": True}), "c": node({})}
        module = mechanics_over(nodes, running=["a", "c"])
        self.assertEqual([node_id for node_id, _parameters in module.running_mechanics("founder_life_extension")], ["a"])


class FounderLifeExtensionTests(unittest.TestCase):
    def mortality(self, running_mechanics):
        slot = SeatsSeat(founder_alive=True, life_left=10)
        module = module_harness.build(Seats, seat=slot, views={
            "dissolution_terms": {"life_extension_years": 3, "years_before_forgetting": 3, "forget_fraction_divisor": 4, "years_until_end": 12},
            "running_mechanics": running_mechanics, "legacy_projects": types.SimpleNamespace(operating=set()),
            "patronage": {"founder_age": 50, "deputies": 0.0, "deputy_hours": 0.0, "deputies_carry_the_work": True}})
        module.founder_mortality()
        return slot.life_left

    def test_a_running_node_declaring_the_mechanic_extends_the_founders_life(self):
        asked = []
        left = self.mortality(lambda name: asked.append(name) or [MODDED])
        self.assertEqual(asked, ["founder_life_extension"])
        self.assertEqual(left, 10 - 1 + 3)

    def test_with_no_such_node_running_the_founder_ages_a_year(self):
        self.assertEqual(self.mortality(lambda name: []), 9)


class CorpusTests(unittest.TestCase):
    CORPUS = {"rank": 9, "dispersed": True, "loss_chance": 0.01, "fraction_lost": 0.02, "diffusion_pace": 2.0}
    LOWER = {"rank": 1, "dispersed": False, "loss_chance": 0.5, "fraction_lost": 0.6, "diffusion_pace": 1.0}

    def module(self, held=()):
        return mechanics_over({MODDED: node({"corpus": self.CORPUS}), "plain_library": node({"corpus": self.LOWER})}, held=held)

    def test_the_best_corpus_node_is_the_highest_ranked_declaring_one(self):
        self.assertEqual(self.module().corpus_nodes()[0], MODDED)

    def test_the_hedge_tiers_follow_the_declared_ranks_strongest_first(self):
        self.assertEqual(self.module().corpus_hedge_tiers(), [(MODDED, 0.01, 0.02), ("plain_library", 0.5, 0.6)])

    def test_the_hedge_a_sacking_faces_is_the_strongest_held_tier(self):
        tiers = [(MODDED, 0.01, 0.02), ("plain_library", 0.5, 0.6)]
        self.assertEqual(knowledge_rules.corpus_hedge(tiers, {MODDED, "plain_library"}, 0.9, 0.8), (0.01, 0.02, MODDED))

    def test_with_no_corpus_held_the_unhedged_figures_apply_and_no_hedge_is_named(self):
        self.assertEqual(knowledge_rules.corpus_hedge([(MODDED, 0.01, 0.02)], set(), 0.9, 0.8), (0.9, 0.8, None))


class CapabilityInstitutionTests(unittest.TestCase):
    def setUp(self):
        self.module = mechanics_over({MODDED: node({"capability": {"scalable": "population", "lost_benefit": "Guild pay"}}),
                                "fixed": node({"capability": {}}), "other": node({})})

    def test_every_node_declaring_capability_is_a_capability_institution(self):
        self.assertEqual(self.module.capability_sets()[0], frozenset({MODDED, "fixed"}))

    def test_only_those_declaring_a_scalable_unit_are_scalable(self):
        self.assertEqual(self.module.capability_sets()[1], frozenset({MODDED}))

    def test_the_lost_benefit_text_is_the_declared_one(self):
        self.assertEqual(self.module.capability_sets()[2], {MODDED: "Guild pay"})


class DiseaseBurdenTests(unittest.TestCase):
    def test_the_disease_technologies_are_exactly_the_nodes_declaring_the_burden(self):
        module = mechanics_over({"germ": node({"disease_burden": {}}), "well": node({"disease_burden": {}}), "plain": node({})})
        self.assertEqual(tuple(module.mechanic("disease_burden")), ("germ", "well"))


if __name__ == "__main__":
    unittest.main()
