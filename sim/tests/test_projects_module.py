"""The projects module's start test and its blocker list, called on the module built with the views they read: the first
check with an opinion wins, a terminal blocker ends the list, the money refusal comes last, a mod's check is asked after the
shipped ones, and the module records what its start phase measured for the phases after it."""
QUICK_TOPIC = True

import unittest

from sim.projects.api import START_CHECKS, NoteActiveChanged, constants as projects_constants
from sim.tests import projects_host

PLAIN = {"cat": "technique", "pre": [], "lab": {}, "sch": 0, "art": 0, "mat": [], "ph": 10.0}


def module(node=PLAIN, **views):
    return projects_host.build(tree=lambda node_id: node if node_id == "a" else None, **views)


class FailureResetShare(unittest.TestCase):
    def test_the_view_answers_the_declared_share(self):
        self.assertEqual(module().failure_reset_share(), projects_constants.FAILURE_RESET_SHARE)


class ActiveProjectsVersion(unittest.TestCase):
    def test_a_note_that_the_projects_in_hand_changed_moves_the_version(self):
        projects = module()
        before = projects.active_projects_version()
        projects.apply_note_active_changed(NoteActiveChanged())
        self.assertNotEqual(projects.active_projects_version(), before)

    def test_a_load_moves_the_version(self):
        projects = module()
        before = projects.active_projects_version()
        projects.clock.bump_everything()
        self.assertNotEqual(projects.active_projects_version(), before)


class StartCheck(unittest.TestCase):
    def test_a_node_nothing_forbids_may_begin(self):
        self.assertEqual(module().start_check("a"), (True, None))

    def test_a_node_not_in_the_tree_cannot(self):
        self.assertEqual(module().start_check("zzz"), (False, "no such node"))
        self.assertEqual(module().start_check("zzz", False, None, False), (False, None))

    def test_the_first_check_with_an_opinion_decides(self):
        both = module(techniques_held={"a"}, legacy_projects=projects_host.projects_state(active={"a": {}}))
        self.assertEqual(both.start_check("a"), (False, "already done"))
        active = module(legacy_projects=projects_host.projects_state(active={"a": {}}))
        self.assertEqual(active.start_check("a"), (False, "already active"))

    def test_asking_for_no_sentence_gives_the_same_verdict_without_one(self):
        done = module(techniques_held={"a"})
        self.assertEqual(done.start_check("a", False, None, False), (False, None))

    def test_a_check_another_owner_answers_is_asked_in_its_place_in_the_order(self):
        asked = []

        def gate(node_id, node, ignore_trade, memo, why):
            asked.append(node_id)
            return False, "no seller"
        self.assertEqual(module(start_gate_material_seller=gate).start_check("a"), (False, "no seller"))
        self.assertEqual(asked, ["a"])
        self.assertEqual(module(techniques_held={"a"}, start_gate_material_seller=gate).start_check("a"), (False, "already done"))
        self.assertEqual(asked, ["a"])

    def test_a_node_short_of_living_stock_is_refused_naming_it(self):
        refused, text = module(stock_status=lambda node_id: {"missing": [("silkworm eggs", 0.02)]}).start_check("a")
        self.assertFalse(refused)
        self.assertIn("silkworm eggs", text)

    def test_a_mods_check_is_asked_after_the_shipped_ones(self):
        mod = lambda node_id, node, ignore_trade, memo, why: (False, "the mod forbids it")
        self.assertEqual(module(extra_start_checks=mod).start_check("a"), (False, "the mod forbids it"))
        self.assertEqual(module(extra_start_checks=mod, techniques_held={"a"}).start_check("a"), (False, "already done"))


class StartBlockers(unittest.TestCase):
    def causes(self, found):
        return [(entry["kind"], entry["cause"]) for entry in found]

    def test_nothing_in_the_way_is_an_empty_list(self):
        self.assertEqual(module().start_blockers("a"), [])

    def test_an_unknown_node_is_unavailable(self):
        self.assertEqual(self.causes(module().start_blockers("zzz")), [("unavailable", "no_such_node")])

    def test_a_terminal_blocker_ends_the_list_before_the_money_is_asked(self):
        done = module(techniques_held={"a"}, material_upfront_refusal=lambda node_id: "no money for the materials")
        self.assertEqual(self.causes(done.start_blockers("a")), [("done", "already_done")])

    def test_the_money_refusal_comes_last(self):
        dear = module(material_upfront_refusal=lambda node_id: "no money for the materials")
        self.assertEqual(self.causes(dear.start_blockers("a")), [("money", "money_refusal")])

    def test_a_built_work_that_is_shut_is_closed_and_one_mothballed_says_so(self):
        shut = module(techniques_held={"a"}, is_venture=lambda node_id: True, running=lambda node_id: False)
        self.assertEqual(self.causes(shut.start_blockers("a")), [("closed", "built_but_shut")])
        mothballed = module(techniques_held={"a"}, closures={"a"}, is_venture=lambda node_id: True,
                            running=lambda node_id: False)
        self.assertEqual(self.causes(mothballed.start_blockers("a")), [("closed", "mothballed")])

    def test_a_mods_refusal_is_a_blocker_of_no_single_kind(self):
        found = module(extra_start_checks=lambda *call: (False, "the mod forbids it")).start_blockers("a")
        self.assertEqual(self.causes(found), [("idle", "extension")])

    def test_the_refusal_is_the_first_blockers_text(self):
        self.assertEqual(module(techniques_held={"a"}).start_refusal("a"), "already done")
        self.assertIsNone(module().start_refusal("a"))

    def test_a_missing_power_capability_is_a_power_blocker_beside_the_plain_ones(self):
        node = dict(PLAIN, pre=["plain", "grid"])
        tree = {"a": node, "plain": PLAIN, "grid": dict(PLAIN, mechanics={"power_tier": 1})}
        found = projects_host.build(tree=tree.get, generation=50.0).start_blockers("a")
        self.assertEqual(self.causes(found), [("knowledge", "missing_prereqs"), ("power", "power_gate")])
        self.assertEqual([entry["ids"] for entry in found], [["plain"], ["grid"]])


class TheChecks(unittest.TestCase):
    def test_every_check_the_table_names_exists_in_the_module(self):
        built = projects_host.build()
        own = [check.cause for check in START_CHECKS if not check.source]
        self.assertTrue(all(callable(getattr(built, "_check_" + cause)) for cause in own))
        self.assertTrue(all(check.source in projects_host.defaults() for check in START_CHECKS if check.source))

    def test_the_order_ends_with_the_social_approval(self):
        self.assertEqual(START_CHECKS[-1].cause, "social_approval")


class StartPhaseHours(unittest.TestCase):
    def test_the_phase_leaves_the_hours_it_measured_for_the_phases_after_it(self):
        phase = projects_host.start_phase_module(
            hours_available={"scholar_hands": 0.0, "craft_hands": 0.0, "director_pool": 900.0, "director_committed": 200.0,
                             "hired_cap": 40.0})
        phase.start_projects_phase("founder")
        self.assertEqual(phase.start_hours(), (700.0, 40.0))

    def test_hours_already_committed_beyond_the_pool_leave_none_free(self):
        phase = projects_host.start_phase_module(
            hours_available={"scholar_hands": 0.0, "craft_hands": 0.0, "director_pool": 100.0, "director_committed": 200.0,
                             "hired_cap": 0.0})
        phase.start_projects_phase("founder")
        self.assertEqual(phase.start_hours(), (0.0, 0.0))

    def test_a_frozen_credit_starts_nothing_but_still_measures_the_hours(self):
        phase = projects_host.start_phase_module(debt_status={"credit_frozen_until": 105, "insolvent_years": 0}, year=100)
        phase.start_projects_phase("founder")
        self.assertEqual(phase.started, [])
        self.assertEqual(len(phase.start_hours()), 2)


if __name__ == "__main__":
    unittest.main()
