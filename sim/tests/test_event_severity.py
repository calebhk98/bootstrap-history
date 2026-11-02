"""Complaint 79: the event stream carries eight severity tiers, worst first."""
import unittest

from .harness import *  # noqa: F401,F403
from sim.refusal import LogLine
from sim.ui.proto import event_severity
from sim.ui.proto.refusal_cause import event_codes
from sim.ui.proto.render_screen_step import render_step


QUICK_TOPIC = True

SACKED = LogLine("site_sacked", "The city was sacked by raiders")
EXHAUSTED = LogLine("credit_exhausted", "CREDIT EXHAUSTED: loans refused")
FAILED = LogLine("project_failed", "a technique failed", severity="minor")
PLAGUE = LogLine("hazard_hit", "plague killed a tenth of the people")
COMPLETED = LogLine("project_completed", "completed: arithmetic")
QUIET = "trade fair held in town"


class EventTiers(unittest.TestCase):

    def test_eight_tiers_from_run_ending_to_informational(self):
        self.assertEqual(len(event_severity.TIER_NAMES), 8)
        self.assertEqual(event_severity.TIER_NAMES[0], "run_ending")
        self.assertEqual(event_severity.TIER_NAMES[-1], "informational")

    def test_catastrophe_outranks_setback_outranks_information(self):
        tier = event_severity.event_tier
        self.assertLess(tier(SACKED), tier(FAILED))
        self.assertLess(tier(EXHAUSTED), tier(FAILED))
        self.assertLess(tier(FAILED), tier(QUIET))
        self.assertLess(tier(PLAGUE), tier(EXHAUSTED))

    def test_completion_is_its_own_tier_above_information(self):
        tier = event_severity.event_tier
        self.assertLess(tier(COMPLETED), tier(QUIET))

    def test_tagging_adds_the_severity_name_and_keeps_the_event(self):
        events = [{"year": 5, "message": "trade fair held in town"}]
        tagged = event_severity.tag_events(events)
        self.assertEqual(tagged[0]["severity"], "informational")
        self.assertEqual(tagged[0]["message"], events[0]["message"])
        self.assertNotIn("severity", events[0])

    def test_ordering_puts_the_worst_first_and_keeps_year_order_within_a_tier(self):
        events = event_severity.tag_events([
            {"year": 1, "message": QUIET},
            {"year": 2, "message": SACKED, "event_kind": "site_sacked"},
            {"year": 3, "message": "trade fair held again"}])
        ordered = event_severity.order_events(events)
        self.assertEqual([event["year"] for event in ordered], [2, 1, 3])


class StepScreenStyling(unittest.TestCase):

    def test_screen_lists_the_worst_event_first_and_marks_it(self):
        out = {"ok": True, "completed": [], "lost": [],
               "events": event_severity.tag_events([
                   {"year": 1, "message": QUIET},
                   {"year": 2, "message": SACKED, "event_kind": "site_sacked"}])}
        text = render_step(out)
        sacked = next(line for line in text.splitlines() if "sacked by raiders" in line)
        fair = next(line for line in text.splitlines() if "trade fair" in line)
        self.assertLess(text.index(sacked), text.index(fair))
        self.assertIn("***", sacked)
        self.assertNotIn("***", fair)


class DisasterGroups(unittest.TestCase):

    def test_a_group_takes_the_highest_tier_of_its_members_whatever_its_name(self):
        from sim.ui.proto.event_groups import group_disaster_events
        members = [LogLine("people_freed", "freed some people"), SACKED, LogLine("people_bought", "bought some people")]
        events = [{"year": 5, "message": message, **event_codes(message)} for message in members]
        grouped = group_disaster_events(events, "A quiet name", members)
        self.assertEqual(len(grouped), 1)
        tagged = event_severity.tag_events(grouped)
        self.assertEqual(tagged[0]["severity"], "regime_war_or_sack")
        self.assertEqual(event_severity.order_events(tagged + [{"year": 6, "message": QUIET}])[0]["year"], 5)


if __name__ == "__main__":
    unittest.main()
