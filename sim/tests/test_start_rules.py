"""The start gate's plain rules (sim/projects/start_rules.py, phase_rules.py, record_rules.py): each test calls one function
with the figures written out."""
QUICK_TOPIC = True

import unittest

from sim.projects.api import phase_rules, record_rules, start_rules


def arrears(insolvent_years=3, capital=-100.0, surplus=0.0, cost=500.0, revenue=100.0, grace=3):
    calls = []

    def watched(name, value):
        return lambda: calls.append(name) or value
    blocked = start_rules.arrears_blocks(
        insolvent_years, grace, capital, watched("surplus", surplus), watched("cost", cost), watched("revenue", revenue),
        watched("cheap_floor", 50.0), 2.0, watched("hard_floor", 200.0), 2.0)
    return blocked, calls


class ArrearsBlocks(unittest.TestCase):
    def test_a_household_short_of_the_grace_years_is_never_blocked_and_nothing_is_worked_out(self):
        self.assertEqual(arrears(insolvent_years=2, capital=-1e9), (False, []))

    def test_a_project_the_surplus_pays_for_is_allowed_however_deep_the_debt(self):
        blocked, calls = arrears(surplus=400.0, cost=500.0, capital=-1e9)
        self.assertFalse(blocked)
        self.assertEqual(calls, ["surplus", "cost", "cheap_floor"])

    def test_a_dear_project_is_blocked_once_the_debt_passes_the_revenue_multiple_or_the_floor(self):
        self.assertTrue(arrears(capital=-250.0)[0])
        self.assertFalse(arrears(capital=-150.0)[0])

    def test_the_cheap_floor_lets_a_household_with_no_surplus_start_something_small(self):
        self.assertFalse(arrears(surplus=0.0, cost=50.0, capital=-1e9)[0])


class CreditFrozenText(unittest.TestCase):
    def test_a_freeze_that_outlasts_the_run_says_so(self):
        self.assertIn("past the horizon", start_rules.credit_frozen_text(1700, 1500))   # presentation: the clause

    def test_a_freeze_that_lifts_inside_the_run_does_not(self):
        self.assertEqual(start_rules.horizon_note(1400, 1500), "")


class ApprovalStance(unittest.TestCase):
    def stance(self, score, wary="patron", opposed="senate", running=(), protection=0.0):
        return start_rules.approval_stance(score, wary, opposed, lambda patron: patron in running, protection, -0.4, -1.2, 0.45)

    def test_a_state_that_is_not_wary_lets_it_be(self):
        self.assertIsNone(self.stance(0.0))

    def test_a_wary_state_wants_a_local_patron_running(self):
        self.assertEqual(self.stance(-0.5), "wary")
        self.assertIsNone(self.stance(-0.5, running=("patron",)))

    def test_an_opposing_state_wants_the_top_patron_or_protection_above_the_override(self):
        self.assertEqual(self.stance(-2.0, running=("patron",)), "opposed")
        self.assertIsNone(self.stance(-2.0, running=("patron", "senate")))
        self.assertIsNone(self.stance(-2.0, running=("patron",), protection=0.5))

    def test_a_gate_with_no_patron_asks_for_nothing(self):
        self.assertIsNone(self.stance(-5.0, wary=None, opposed=None))


class SubstitutionOutcome(unittest.TestCase):
    GROUPS = [{"group": "fuel"}, {"group": "vessel"}]

    def test_each_groups_best_option_multiplies_into_the_quality(self):
        quality, ok, failed = start_rules.substitution_outcome(self.GROUPS, lambda group: {"fuel": 0.5, "vessel": 0.8}[group["group"]])
        self.assertEqual((quality, ok, failed), (0.4, True, None))

    def test_a_group_with_no_option_fails_the_gate_and_is_named(self):
        quality, ok, failed = start_rules.substitution_outcome(self.GROUPS, lambda group: 0.0 if group["group"] == "vessel" else 0.5)
        self.assertEqual((quality, ok, failed["group"]), (0.0, False, "vessel"))

    def test_the_gap_names_the_group_in_words_and_the_four_best_options(self):
        group = {"group": "pressure_vessel", "options": {"iron": 0.9, "bronze": 0.5, "wood": 0.1, "clay": 0.3, "horn": 0.2}}
        name, options = start_rules.substitution_gap(group)
        self.assertEqual((name, options), ("a pressure vessel", ["iron", "bronze", "clay", "horn"]))


class BountyPossible(unittest.TestCase):
    CRAFTS = ("glass_optics", "metallurgy")

    def possible(self, category, prerequisites_done=True, cost_factor=1.0):
        return start_rules.bounty_possible(category, self.CRAFTS, prerequisites_done, lambda: cost_factor, 0.95)

    def test_a_craft_category_with_its_prerequisites_known_can_be_bought(self):
        self.assertTrue(self.possible("metallurgy"))
        self.assertFalse(self.possible("metallurgy", prerequisites_done=False))

    def test_another_category_only_when_the_society_is_measurably_good_at_it(self):
        self.assertFalse(self.possible("shipbuilding"))
        self.assertTrue(self.possible("shipbuilding", cost_factor=0.9))

    def test_the_cost_factor_is_not_asked_for_a_craft_category(self):
        asked = []
        start_rules.bounty_possible("metallurgy", self.CRAFTS, True, lambda: asked.append(1) or 1.0, 0.95)
        self.assertEqual(asked, [])


class TradeWait(unittest.TestCase):
    ROWS = [("x", 105, "smith", 2), ("x", 103, "smith", 0), ("x", 120, "engineer", 1)]

    def test_hands_that_exist_now_wait_nothing(self):
        self.assertEqual(start_rules.trade_wait_years(2.0, 100, self.ROWS, "smith"), 0.0)

    def test_none_now_waits_for_the_soonest_trainees_who_count(self):
        self.assertEqual(start_rules.trade_wait_years(0.0, 100, self.ROWS, "smith"), 5.0)

    def test_nobody_on_the_way_is_none(self):
        self.assertIsNone(start_rules.trade_wait_years(0.0, 100, self.ROWS, "mason"))

    def test_a_wait_outlasts_the_project_when_it_reaches_the_stall_gate_or_never_ends(self):
        stall = start_rules.STALL_YEARS_BEFORE_ABANDONMENT
        self.assertTrue(start_rules.trade_wait_outlasts(None, stall))
        self.assertTrue(start_rules.trade_wait_outlasts(stall - 1, stall))
        self.assertFalse(start_rules.trade_wait_outlasts(stall - 2, stall))


class MaxActiveProjects(unittest.TestCase):
    def test_each_kind_of_capacity_adds_slots_by_its_own_rate(self):
        self.assertEqual(phase_rules.max_active_projects(2, 4000.0, 2000.0, 24.0, 12.0, 50.0, 25.0), 8)

    def test_a_fraction_of_a_slot_is_not_a_slot(self):
        self.assertEqual(phase_rules.max_active_projects(2, 1000.0, 2000.0, 3.0, 12.0, 5.0, 25.0), 2)


class MoneyIsThin(unittest.TestCase):
    def test_a_surplus_under_the_floor_or_a_quarter_of_fixed_costs_is_thin(self):
        self.assertTrue(phase_rules.money_is_thin(1000.0, 800.0))
        self.assertFalse(phase_rules.money_is_thin(5000.0, 800.0))
        self.assertTrue(phase_rules.money_is_thin(5000.0, 4500.0))


class CandidatesInOrder(unittest.TestCase):
    NODES = {"a": {"rev": 0, "up": 0}, "b": {"rev": 30, "up": 10}, "c": {"rev": 100, "up": 0}}
    COSTS = {"a": 5.0, "b": 100.0, "c": 100.0}

    def order(self, thin):
        return phase_rules.candidates_in_order(["a", "b", "c"], self.NODES.__getitem__, self.COSTS.__getitem__, thin)

    def test_with_enough_money_the_goal_order_stands(self):
        self.assertEqual(self.order(False), ["a", "b", "c"])

    def test_with_thin_money_what_pays_best_for_its_cost_comes_first_then_the_rest_in_goal_order(self):
        self.assertEqual(self.order(True), ["c", "b", "a"])


class NonBountiedCount(unittest.TestCase):
    def test_a_bounty_never_counts_against_the_cap(self):
        self.assertEqual(phase_rules.non_bountied_count(["a", "b", "c"], {"b"}), 2)
        self.assertEqual(phase_rules.non_bountied_count(["a"], set()), 1)


class NewRecord(unittest.TestCase):
    NODE = {"ph": 100.0, "lab": {"smith": 40.0}}

    def test_a_plain_record_starts_with_all_the_hours_and_labour_left(self):
        record = record_rules.new_record(self.NODE, 1.0, None, 0.0, 70.0, True, 70.0, None)
        self.assertEqual(record, {"ph_left": 100.0, "yrs": 0.0, "spent": 0.0, "cost_left": 70.0, "status": "ACTIVE",
                                  "bill": 70.0, "lab_left": {"smith": 40.0}})

    def test_a_rebuild_scales_the_hours_and_labour_and_is_marked(self):
        record = record_rules.new_record(self.NODE, 0.5, None, 0.0, 70.0, True, None, {"forest": 2.0})
        self.assertEqual((record["ph_left"], record["lab_left"], record["rebuild_factor"], record["own_output_claim"]),
                         (50.0, {"smith": 20.0}, 0.5, {"forest": 2.0}))
        self.assertNotIn("bill", record)

    def test_a_bounty_has_no_poster_hours_and_no_labour(self):
        record = record_rules.new_record(self.NODE, 1.0, 0.0, 300.0, 0.0, False, None, None)
        self.assertEqual((record["ph_left"], record["spent"], record["cost_left"]), (0.0, 300.0, 0.0))
        self.assertNotIn("lab_left", record)


class CreditKept(unittest.TestCase):
    def test_money_spent_stands_to_the_projects_credit(self):
        self.assertEqual(record_rules.credit_kept(300.0, 50.0), (300.0, 350.0))

    def test_next_to_nothing_paid_keeps_nothing(self):
        self.assertEqual(record_rules.credit_kept(0.2, 0.0), (0.2, None))
        self.assertEqual(record_rules.credit_kept(-5.0, 0.0), (0.0, None))


class UnheldStockVerdict(unittest.TestCase):
    def test_nothing_short_gives_no_verdict(self):
        self.assertIsNone(start_rules.unheld_stock_verdict([], True))

    def test_a_stock_short_refuses_and_names_it(self):
        refused, text = start_rules.unheld_stock_verdict([("silkworm eggs", 0.02)], True)
        self.assertFalse(refused)
        self.assertIn("silkworm eggs", text)

    def test_asked_for_no_sentence_the_refusal_has_none(self):
        self.assertEqual(start_rules.unheld_stock_verdict([("silkworm eggs", 0.02)], False), (False, None))


if __name__ == "__main__":
    unittest.main()
