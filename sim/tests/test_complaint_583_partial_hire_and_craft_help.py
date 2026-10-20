"""Complaints/583: a partial hire says how many were hired and why; the craft help reads the supervision trade data.
The rules are plain functions (sim/labour/hire_outcome.py, sim/ui/proto/hire_reply.py), called on built numbers.
(That `hire` and `ventures` call them: test_scenarios_batch3_hire.)"""
QUICK_TOPIC = True

import unittest

from sim.engine.data import TRADE_FAMILY
from sim.labour.hire_outcome import FOUND_FEWER, craft_trades_report, hire_result, unfound_note
from sim.refusal import cause_of, facts_of
from sim.ui.proto.hire_reply import hire_reply

ASKED, FOUND = 4, 1


def reply(hired=FOUND, asked=ASKED, outcome="taken on"):
    return hire_reply(hired, asked, "artisan", 7.0, 1234.56, 99.94, 321.09, 5000.04, outcome)


class PartialHireReplyTests(unittest.TestCase):
    def partial(self):
        _ok, outcome = hire_result("text", unfound_note(FOUND, ASKED), FOUND, ASKED)
        return reply(outcome=outcome)

    def test_a_short_hire_is_still_ok(self):
        self.assertIs(self.partial()["ok"], True)

    def test_hired_is_the_number_found_and_asked_the_number_requested(self):
        self.assertEqual((self.partial()["hired"], self.partial()["asked"]), (FOUND, ASKED))

    def test_the_shortfall_carries_a_cause(self):
        self.assertEqual(self.partial()["cause"], "search_found_fewer")

    def test_the_trade_is_named_in_its_own_field(self):
        self.assertEqual(self.partial()["trade"], "artisan")

    def test_a_full_hire_carries_no_shortfall_cause(self):
        self.assertNotIn("cause", reply(hired=ASKED, asked=ASKED))

    def test_a_cause_the_outcome_names_wins_over_the_default(self):
        outcome = hire_result("t", " x", FOUND, ASKED)[1]
        self.assertEqual(reply(outcome=outcome)["cause"], FOUND_FEWER)

    def test_figures_are_rounded_for_reading(self):
        full = reply(hired=ASKED)
        self.assertEqual((full["you_now_employ"], full["annual_wage_bill"], full["paid_now"],
                          full["from_next_year_per_year"], full["capital"]), (7.0, 1234.6, 99.9, 321.1, 5000.0))


class HireResultTests(unittest.TestCase):
    def test_a_full_hire_returns_its_text(self):
        self.assertEqual(hire_result("2 smiths taken on", unfound_note(2, 2), 2, 2), (True, "2 smiths taken on"))

    def test_a_short_hire_returns_a_refusal_with_how_many_of_how_many(self):
        ok, outcome = hire_result("text", unfound_note(FOUND, ASKED), FOUND, ASKED)
        self.assertTrue(ok)
        self.assertEqual(cause_of(outcome), "search_found_fewer")
        self.assertEqual((facts_of(outcome)["asked"], facts_of(outcome)["hired"]), (4.0, 1.0))

    def test_the_note_says_found_of_asked_only_when_short(self):
        # presentation: the sentence a player reads
        self.assertIn("Found 1 of the 4 asked for", unfound_note(1, 4))
        self.assertEqual(unfound_note(4, 4), "")
        self.assertEqual(unfound_note(4.0 - 1e-9, 4), "")


class CraftTradesReportTests(unittest.TestCase):
    def test_the_report_splits_the_trades_by_the_test_it_is_given(self):
        report = craft_trades_report(["smith", "labourer", "mason", "scribe"], lambda trade: trade in ("smith", "mason"))
        self.assertEqual(report, {"craft": ["mason", "smith"], "not_craft": ["labourer", "scribe"]})

    def test_every_trade_is_in_exactly_one_list(self):
        trades = ["a", "b", "c", "d", "e"]
        report = craft_trades_report(trades, lambda trade: trade in "bd")
        self.assertEqual(sorted(report["craft"] + report["not_craft"]), trades)
        self.assertFalse(set(report["craft"]) & set(report["not_craft"]))

    def test_the_craft_trades_the_help_names_are_those_the_family_table_calls_craft(self):
        from sim.engine.data import trade_family
        report = craft_trades_report(TRADE_FAMILY, lambda trade: trade_family(trade) == "craft")
        self.assertEqual(sorted(report["craft"]), sorted(trade for trade, family in TRADE_FAMILY.items() if family == "craft"))
        self.assertTrue(report["craft"])

    def test_the_labourer_does_not_supervise_as_craft(self):
        from sim.engine.data import trade_family
        self.assertNotEqual(trade_family("labourer"), "craft")


if __name__ == "__main__":
    unittest.main()
