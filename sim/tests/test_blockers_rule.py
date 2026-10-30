"""Complaint 640: the blocker list rule (`collect_blockers`, `classify_plain_check`) on built checks, no game."""

QUICK_TOPIC = True

import unittest

from sim.projects.api import blocker_rules

classify_plain_check, collect_blockers = blocker_rules.classify_plain_check, blocker_rules.collect_blockers


def make_checks(*kinds):
    made = []
    for index, kind in enumerate(kinds):
        def check():
            pass
        check.__name__ = "check_%d" % index
        check.kind = kind
        made.append(check)
    return made


def collect(verdicts, money=None):
    ran = []

    def run_check(check):
        ran.append(check)
        return verdicts[check]

    def classify(check, text):
        return [{"kind": check.kind, "cause": check.__name__, "ids": [], "text": text}]
    return collect_blockers(list(verdicts), run_check, classify, lambda: money), ran


class CollectBlockers(unittest.TestCase):
    def test_passing_and_silent_checks_add_nothing(self):
        first, second = make_checks("knowledge", "supply")
        result, _ran = collect({first: (True, "fine"), second: None})
        self.assertEqual(result, [])

    def test_refusals_come_in_gate_order(self):
        first, second = make_checks("knowledge", "supply")
        result, _ran = collect({first: (False, "a"), second: (False, "b")})
        self.assertEqual([entry["kind"] for entry in result], ["knowledge", "supply"])

    def test_a_terminal_kind_ends_the_list_and_skips_later_checks_and_money(self):
        first, second, third = make_checks("knowledge", "done", "supply")
        result, ran = collect({first: (False, "a"), second: (False, "b"), third: (False, "c")}, money="dear")
        self.assertEqual([entry["kind"] for entry in result], ["knowledge", "done"])
        self.assertEqual(ran, [first, second])

    def test_money_comes_last_when_stated(self):
        first, = make_checks("supply")
        result, _ran = collect({first: (False, "a")}, money="dear")
        self.assertEqual([entry["kind"] for entry in result], ["supply", "money"])
        self.assertEqual(result[-1]["cause"], "money_refusal")

    def test_no_money_refusal_adds_no_entry(self):
        first, = make_checks("supply")
        result, _ran = collect({first: (False, "a")}, money=None)
        self.assertEqual(len(result), 1)


class ClassifyPlainCheck(unittest.TestCase):
    def test_cause_is_the_one_the_check_is_named_by(self):
        entry = classify_plain_check("absent_trades", "specialists", "t", [], None, False)
        self.assertEqual((entry["kind"], entry["cause"]), ("specialists", "absent_trades"))

    def test_supply_carries_its_options_and_other_kinds_do_not(self):
        self.assertEqual(classify_plain_check("x", "supply", "t", ["a"], None, False)["ids"], ["a"])
        self.assertEqual(classify_plain_check("x", "money", "t", ["a"], None, False)["ids"], [])

    def test_done_on_a_shut_venture_is_closed_with_the_shut_text(self):
        entry = classify_plain_check("already_done", "done", "done", [], "shut", False)
        self.assertEqual((entry["kind"], entry["cause"], entry["text"]), ("closed", "built_but_shut", "shut"))

    def test_done_on_a_running_work_stays_done(self):
        entry = classify_plain_check("already_done", "done", "done", [], None, False)
        self.assertEqual((entry["kind"], entry["cause"]), ("done", "already_done"))

    def test_mothballed_is_closed_with_its_own_cause(self):
        entry = classify_plain_check("already_done", "done", "done", [], "shut", True)
        self.assertEqual((entry["kind"], entry["cause"]), ("closed", "mothballed"))


class SupplyBlockerIds(unittest.TestCase):
    """Complaint 682: only the substitution check names the options of the node's own failed group."""
    gap = ("a vessel", ["bronze_boiler", "hidden_boiler"])

    def ids(self, cause, gap):
        return blocker_rules.supply_blocker_ids(cause, gap, lambda option: option != "hidden_boiler")

    def test_substitution_names_its_visible_options(self):
        self.assertEqual(self.ids("substitution", self.gap), ["bronze_boiler"])

    def test_substitution_with_no_gap_names_none(self):
        self.assertEqual(self.ids("substitution", None), [])

    def test_held_herd_names_no_substitution_option(self):
        self.assertEqual(self.ids("needs_held_herd", self.gap), [])

    def test_own_material_causes_name_no_substitution_option(self):
        self.assertEqual(self.ids("unheld_stock", self.gap), [])
        self.assertEqual(self.ids("materials_have_a_seller", self.gap), [])


if __name__ == "__main__":
    unittest.main()
