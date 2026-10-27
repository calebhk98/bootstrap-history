"""The knowledge module: its commands change what a seat holds, lost and heard of, and its views answer from them. The
module is built with plain values for the state it shares with the engine; no game."""
QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

from sim.knowledge import rules
from sim.knowledge.api import (ForgetTechnique, KnowledgeSeat, LearnTechnique, RevealFrom, RevealNodes)
from sim.production.api import RefreshDoneCaches
from sim.knowledge.module import DONE, REVEALED, Knowledge
from sim.tests import module_harness

NODES = {
    "fire": {"pre": [], "cat": "x"}, "bronze": {"pre": ["fire"], "cat": "x"}, "iron": {"pre": ["bronze"], "cat": "x"},
    "alloy": {"pre": [], "req_any": [{"options": {"bronze": 1.0, "iron": 1.0}}], "cat": "x"},
}


def projects(done=(), granted=(), active=(), revealed=(), done_year=None):
    return SimpleNamespace(done=set(done), granted=set(granted), active=dict.fromkeys(active, {}), revealed=set(revealed),
                           done_year=done_year)


def knowledge_over(state, fog=False, start_check=None, **views):
    return module_harness.build(
        Knowledge, seat=KnowledgeSeat(), answers={RefreshDoneCaches: None},
        views=dict({"legacy_projects": state, "legacy_tree": NODES, "legacy_fog": fog,
                    "start_check": start_check or (lambda node_id, ignore_trade, memo, why: (False, None))}, **views))


class LearnTests(unittest.TestCase):
    def test_a_learned_technique_is_held_dated_and_the_caches_are_told(self):
        state = projects()
        module = knowledge_over(state)
        module.learn_technique(LearnTechnique("fire", year=120))
        self.assertEqual(state.done, {"fire"})
        self.assertEqual(state.done_year, {"fire": 120})
        self.assertEqual(state.granted, set())
        self.assertEqual([type(command) for command in module_harness.sent(module)], [RefreshDoneCaches])

    def test_a_granted_technique_is_held_and_marked_as_its_countrys_own_with_no_year(self):
        state = projects()
        knowledge_over(state).learn_technique(LearnTechnique("fire", granted=True))
        self.assertEqual((state.done, state.granted, state.done_year), ({"fire"}, {"fire"}, None))

    def test_the_done_channel_moves_when_something_is_learned(self):
        module = knowledge_over(projects())
        before = module.clock.counter(module.module_id, DONE, True)
        module.learn_technique(LearnTechnique("fire"))
        self.assertGreater(module.clock.counter(module.module_id, DONE, True), before)


class ForgetTests(unittest.TestCase):
    def test_a_dated_loss_is_recorded_for_the_rebuild(self):
        state = projects(done={"fire", "bronze"})
        module = knowledge_over(state)
        module.forget_technique(ForgetTechnique(("bronze",), year=150))
        self.assertEqual(state.done, {"fire"})
        self.assertEqual(module.techniques_forgotten(), {"bronze": 150})

    def test_an_undated_loss_is_not_a_sacking_and_is_not_recorded(self):
        state = projects(done={"fire", "bronze"})
        module = knowledge_over(state)
        module.forget_technique(ForgetTechnique(("bronze", "fire")))
        self.assertEqual(state.done, set())
        self.assertEqual(module.techniques_forgotten(), {})
        self.assertEqual(len(module_harness.sent(module)), 1)


class RevealTests(unittest.TestCase):
    def test_finishing_a_node_reveals_what_it_leads_towards_under_fog(self):
        state = projects()
        knowledge_over(state, fog=True).reveal_from(RevealFrom("bronze"))
        self.assertEqual(state.revealed, {"bronze", "iron", "alloy"})

    def test_without_fog_nothing_is_revealed(self):
        state = projects()
        knowledge_over(state, fog=False).reveal_from(RevealFrom("bronze"))
        self.assertEqual(state.revealed, set())

    def test_hearing_of_nodes_only_adds(self):
        state = projects(revealed={"fire"})
        knowledge_over(state).reveal_nodes(RevealNodes(("iron",)))
        self.assertEqual(state.revealed, {"fire", "iron"})
        self.assertIsNotNone(REVEALED)


class VisibilityTests(unittest.TestCase):
    def test_without_fog_everything_is_visible_and_nothing_is_asked(self):
        asked = []
        module = knowledge_over(projects(), fog=False, start_check=lambda *arguments: asked.append(arguments))
        self.assertTrue(module.visibility("iron", None))
        self.assertEqual(asked, [])

    def test_held_in_hand_and_heard_of_nodes_are_visible_under_fog_without_asking_the_start_test(self):
        asked = []
        module = knowledge_over(projects(done={"fire"}, active={"bronze"}, revealed={"iron"}), fog=True,
                                start_check=lambda *arguments: asked.append(arguments))
        self.assertTrue(all(module.visibility(node_id, None) for node_id in ("fire", "bronze", "iron")))
        self.assertEqual(asked, [])

    def test_an_unheard_node_is_visible_only_when_it_can_be_started(self):
        module = knowledge_over(projects(), fog=True, start_check=lambda node_id, ignore_trade, memo, why: (node_id == "fire", None))
        self.assertTrue(module.visibility("fire", None))
        self.assertFalse(module.visibility("iron", None))

    def test_the_shared_memo_stops_a_second_descent_into_the_same_node(self):
        calls = []

        def start_check(node_id, ignore_trade, memo, why):
            calls.append(node_id)
            return False, None
        module = knowledge_over(projects(), fog=True, start_check=start_check)
        memo = {}
        module.visibility("iron", memo)
        module.visibility("iron", memo)
        self.assertEqual(calls, ["iron"])

    def test_the_player_may_be_told_only_about_visible_nodes_of_the_tree(self):
        module = knowledge_over(projects(revealed={"iron"}), fog=True)
        self.assertTrue(module.visible_to_player("iron"))
        self.assertFalse(module.visible_to_player("alloy"))
        self.assertFalse(module.visible_to_player("not_in_the_tree"))

    def test_a_fogged_text_loses_the_ids_the_player_has_not_heard_of(self):
        module = knowledge_over(projects(revealed={"iron"}), fog=True)
        scrubbed = module.fog_scrub("iron then alloy")
        self.assertTrue(scrubbed.startswith("iron then "))
        self.assertNotIn("alloy", scrubbed)
        self.assertIsNone(module.fog_scrub(None))


class ViewTests(unittest.TestCase):
    def test_the_tree_is_read_by_id_and_whole(self):
        module = knowledge_over(projects())
        self.assertIs(module.tree("fire"), NODES["fire"])
        self.assertIsNone(module.tree("missing"))
        self.assertIs(module.tree_nodes(), NODES)

    def test_a_seat_with_no_record_has_an_empty_done_year(self):
        self.assertEqual(knowledge_over(projects(done_year=None)).done_year(), {})

    def test_the_earliest_year_over_the_seats_that_hold_the_node(self):
        seats = {"a": SimpleNamespace(projects=projects(done={"fire"}, done_year={"fire": 130})),
                 "b": SimpleNamespace(projects=projects(done={"fire"}, done_year={"fire": 110})),
                 "c": SimpleNamespace(projects=projects(done=set(), done_year={"fire": 50}))}
        module = knowledge_over(projects(), legacy_seats=seats)
        self.assertEqual(module.earliest_done_year("fire", 200), 110)
        self.assertEqual(module.earliest_done_year("iron", 200), 200)

    def test_the_corpus_hedge_is_the_first_tier_held_else_the_unhedged_figures(self):
        module = knowledge_over(projects(done={"written"}), corpus_hedge_tiers=[("dispersed", 0.2, 0.08), ("written", 0.5, 0.22)])
        self.assertEqual(module.corpus_hedge(), (0.5, 0.22, "written"))
        bare = knowledge_over(projects(), corpus_hedge_tiers=[("dispersed", 0.2, 0.08)])
        chance, fraction, hedge = bare.corpus_hedge()
        self.assertIsNone(hedge)
        self.assertGreater(chance, 0.5)
        self.assertGreater(fraction, 0.22)


class RuleTests(unittest.TestCase):
    def test_the_finished_nodes_come_in_the_trees_order(self):
        self.assertEqual(rules.in_tree_order(["fire", "bronze", "iron"], {"iron", "fire"}), ["fire", "iron"])

    def test_reveal_targets_name_the_node_and_everything_that_leans_on_it(self):
        self.assertEqual(sorted(rules.reveal_targets(NODES, "bronze")), ["alloy", "bronze", "iron"])

    def test_never_abandon_protects_a_flagged_category_always_and_the_goals_road_unless_a_running_work_leans_on_it(self):
        self.assertTrue(rules.never_abandon(True, True, False))
        self.assertFalse(rules.never_abandon(False, True, True))
        self.assertTrue(rules.never_abandon(False, False, True))
        self.assertFalse(rules.never_abandon(False, False, False))


if __name__ == "__main__":
    unittest.main()
