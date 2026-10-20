"""Complaints/579: each departure and each closure is an event with a kind, its cause and what it stops. The lines are
built by `staff_lost_line` (sim/labour/staff_events.py) and `unstaffed_closure_line` (sim/engine/staffing_events.py)
from plain facts; how the protocol treats the kinds is sim/ui/proto/event_kinds.py. (That a played year logs them and
a multi-year step stops on them: test_scenarios_batch3.)"""
QUICK_TOPIC = True

import unittest

from sim.engine.staffing_events import unstaffed_closure_line
from sim.labour.staff_events import people_text, staff_lost_line
from sim.refusal import cause_of, facts_of
from sim.ui.proto.event_kinds import EVENT_KINDS, is_failure, stops_a_step


class DepartureTests(unittest.TestCase):
    def departure(self, cause="better offers", counts=None, stops=("hall",), earnings=120.04):
        return staff_lost_line(cause, counts or {"artisan": 6}, list(stops), earnings)

    def test_a_departure_that_closes_a_concern_has_its_own_kind(self):
        self.assertEqual(cause_of(self.departure()), "staff_lost_stops_concerns")

    def test_its_kind_is_listed_in_event_kinds(self):
        self.assertIn("staff_lost_stops_concerns", EVENT_KINDS)
        self.assertIn("staff_lost", EVENT_KINDS)

    def test_it_carries_its_cause(self):
        self.assertEqual(facts_of(self.departure())["reason"], "better_offers")
        self.assertEqual(facts_of(self.departure(cause="death"))["reason"], "death")

    def test_it_names_the_people_and_what_it_stops(self):
        facts = facts_of(self.departure())
        self.assertEqual(facts["trades"], {"artisan": 6})
        self.assertEqual(facts["stops"], ["hall"])
        self.assertEqual(facts["stops_earnings_per_year"], 120.0)

    def test_it_is_a_warning_that_stops_a_step(self):
        self.assertTrue(stops_a_step(self.departure()))
        self.assertTrue(is_failure(self.departure()))

    def test_a_departure_that_stops_nothing_is_a_plain_staff_lost_with_no_stops(self):
        quiet = self.departure(stops=())
        self.assertEqual(cause_of(quiet), "staff_lost")
        self.assertEqual(facts_of(quiet)["stops"], [])
        self.assertFalse(stops_a_step(quiet))

    def test_nobody_leaving_logs_nothing(self):
        self.assertIsNone(staff_lost_line("death", {"artisan": 0}, [], 0.0))
        self.assertIsNone(staff_lost_line("death", {}, [], 0.0))

    def test_only_trades_with_losses_are_counted(self):
        self.assertEqual(facts_of(staff_lost_line("death", {"artisan": 2, "smith": 0}, [], 0.0))["trades"],
                         {"artisan": 2})

    def test_stops_are_sorted(self):
        self.assertEqual(facts_of(self.departure(stops=("zeta", "alpha")))["stops"], ["alpha", "zeta"])

    def test_the_text_names_the_people_and_at_most_four_closures(self):
        # presentation: the sentence a player reads
        text = str(self.departure(counts={"artisan": 6, "smith": 1}, stops=list("abcdef")))
        self.assertIn("you lose 6 artisans, 1 smith to better offers", text)
        self.assertIn("a, b, c, d will close", text)

    def test_people_are_counted_in_whole_numbers_near_whole_and_tenths_otherwise(self):
        # presentation: how a headcount reads
        self.assertEqual(people_text({"smith": 1.02}), "1 smith")
        self.assertEqual(people_text({"smith": 2.5}), "2.5 smiths")


class ClosureTests(unittest.TestCase):
    def closure(self, closed=("hall",), earnings=88.0):
        return unstaffed_closure_line(list(closed), {"artisan": 1.5}, "1.5 craftsmen", 3, "Hire or train.", earnings)

    def test_the_closure_names_the_concerns_its_cause_and_the_shortfall(self):
        facts = facts_of(self.closure(("zeta", "alpha")))
        self.assertEqual(cause_of(self.closure()), "concerns_closed_unstaffed")
        self.assertEqual(facts["concerns"], ["alpha", "zeta"])
        self.assertEqual(facts["closed_because"], "short_staffed")
        self.assertEqual(facts["short"], {"artisan": 1.5})

    def test_it_says_what_it_stops_earning(self):
        self.assertEqual(facts_of(self.closure())["stops_earnings_per_year"], 88.0)

    def test_its_kind_is_listed_as_a_failure(self):
        self.assertIn("concerns_closed_unstaffed", EVENT_KINDS)
        self.assertTrue(is_failure(self.closure()))

    def test_the_text_names_at_most_four_closures_and_says_others(self):
        # presentation: the sentence a player reads
        text = str(self.closure(closed=list("abcdef")))
        self.assertIn("a, b, c, d and others closed", text)
        self.assertIn("6 concerns", text)

    def test_one_concern_reads_in_the_singular(self):
        # presentation: the sentence a player reads
        self.assertIn("1 concern (short of 1.5 craftsmen)", str(self.closure()))


if __name__ == "__main__":
    unittest.main()
