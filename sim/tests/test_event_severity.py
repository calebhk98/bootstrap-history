"""Complaint 81: the event stream carries eight severity tiers, worst first."""
import unittest

from .harness import *  # noqa: F401,F403
from sim.engine.proto import event_severity
from sim.engine.proto.render_screens_big import render_step


class EventTiers(unittest.TestCase):

    def test_eight_tiers_from_run_ending_to_informational(self):
        self.assertEqual(len(event_severity.TIER_NAMES), 8)
        self.assertEqual(event_severity.TIER_NAMES[0], "run_ending")
        self.assertEqual(event_severity.TIER_NAMES[-1], "informational")

    def test_catastrophe_outranks_setback_outranks_information(self):
        tier = event_severity.event_tier
        self.assertLess(tier("The city was sacked by raiders"), tier("a technique failed"))
        self.assertLess(tier("CREDIT EXHAUSTED: loans refused"), tier("a technique failed"))
        self.assertLess(tier("a technique failed"), tier("trade fair held in town"))
        self.assertLess(tier("plague killed a tenth of the people"), tier("CREDIT EXHAUSTED: loans refused"))

    def test_completion_is_its_own_tier_above_information(self):
        tier = event_severity.event_tier
        self.assertLess(tier("completed: arithmetic"), tier("trade fair held in town"))

    def test_tagging_adds_the_severity_name_and_keeps_the_event(self):
        events = [{"year": 5, "message": "trade fair held in town"}]
        tagged = event_severity.tag_events(events)
        self.assertEqual(tagged[0]["severity"], "informational")
        self.assertEqual(tagged[0]["message"], events[0]["message"])
        self.assertNotIn("severity", events[0])

    def test_ordering_puts_the_worst_first_and_keeps_year_order_within_a_tier(self):
        events = event_severity.tag_events([
            {"year": 1, "message": "trade fair held in town"},
            {"year": 2, "message": "The city was sacked by raiders"},
            {"year": 3, "message": "trade fair held again"}])
        ordered = event_severity.order_events(events)
        self.assertEqual([event["year"] for event in ordered], [2, 1, 3])


class StepScreenStyling(unittest.TestCase):

    def test_screen_lists_the_worst_event_first_and_marks_it(self):
        out = {"ok": True, "completed": [], "lost": [],
               "events": event_severity.tag_events([
                   {"year": 1, "message": "trade fair held in town"},
                   {"year": 2, "message": "The city was sacked by raiders"}])}
        text = render_step(out)
        sacked = next(line for line in text.splitlines() if "sacked by raiders" in line)
        fair = next(line for line in text.splitlines() if "trade fair" in line)
        self.assertLess(text.index(sacked), text.index(fair))
        self.assertIn("***", sacked)
        self.assertNotIn("***", fair)


class StepReplyCarriesSeverity(unittest.TestCase):

    def test_every_step_event_has_a_severity_name(self):
        from sim.engine.protocol import _agent_dispatch
        household = sim(civ="rome_100ad", capital=1e5)
        household.end_year = household.cfg["start_year"] + 50
        reply = _agent_dispatch(household, NODES, {"cmd": "step", "years": 3})
        self.assertTrue(reply["events"])
        for event in reply["events"]:
            self.assertIn(event["severity"], event_severity.TIER_NAMES)


if __name__ == "__main__":
    unittest.main()
