"""Complaints/96: schooling message always says 'a generation' even for new schools.

When a school is first opened, the first literacy advancement message appears
soon after, but the log message says "a generation of schooling shows in the
census" even though only a year or few years have passed. This is narratively
misleading since a generation (defined as 25 years in the code) has not actually
occurred.

unittest.TestCase style, like the other focused complaint suites.
"""
import os
import random
import sys
import unittest

_REPOSITORY_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
if _REPOSITORY_ROOT not in sys.path:
    sys.path.insert(0, _REPOSITORY_ROOT)
from sim import simulator
from sim.engine.core import Sim

_TREE, _PRICES, _NODES, _WAGES, _GOODS = simulator.load()


def _fresh_sim():
    return Sim(_NODES, list(_NODES), random.Random(1))


class SchoolingMessageTimingTests(unittest.TestCase):

    def test_young_school_message_different_from_old_school(self):
        # Message should differ based on when the school was founded
        sim = _fresh_sim()

        # Set up with a school that was just opened
        current_year = 100
        school_opened_year = 100
        sim.state.scenario.year = current_year

        # Mark school as done and when it was done
        sim.state.projects.done.add("school_founded")
        if sim.state.projects.done_year is None:
            sim.state.projects.done_year = {}
        sim.state.projects.done_year["school_founded"] = school_opened_year

        # Make it running
        sim.state.projects.operating.add("school_founded")

        # Set up a scenario where literacy would advance
        sim.civ["literacy_elite"] = 0.5

        # Advance literacy which generates the message
        sim._advance_literacy(current_year)

        # Check if message was logged
        messages = sim.state.household.log
        if messages:
            last_message = messages[-1][1]
            # For a young school (just opened this year), should NOT say "a generation"
            # because no 25-year period has passed
            if "a generation of schooling" in last_message:
                # This is the bug - newly opened schools shouldn't say this
                self.fail(f"New school (opened year {school_opened_year}, year {current_year}) "
                         f"says 'a generation of schooling' but only "
                         f"{current_year - school_opened_year} years have passed")

    def test_old_school_message_can_say_generation(self):
        # Message can use "generation" language when school has been open long enough
        sim = _fresh_sim()

        current_year = 130
        school_opened_year = 100  # 30 years ago, more than 25-year generation
        sim.state.scenario.year = current_year

        # Mark school as done and when it was done
        sim.state.projects.done.add("school_founded")
        if sim.state.projects.done_year is None:
            sim.state.projects.done_year = {}
        sim.state.projects.done_year["school_founded"] = school_opened_year

        # Make it running
        sim.state.projects.operating.add("school_founded")

        # Set up literacy advancement
        sim.civ["literacy_elite"] = 0.5

        # Advance literacy
        sim._advance_literacy(current_year)

        # For an established school (25+ years), generation language is appropriate
        # This test mainly documents that old schools are okay
        messages = sim.state.household.log
        if messages:
            last_message = messages[-1][1]
            # Generation language is acceptable here
            self.assertIn("generation", last_message.lower())

    def test_message_format_changes_with_school_age(self):
        # The message format should reflect the school's age
        sim = _fresh_sim()

        # Test with a very young school
        sim.state.scenario.year = 100
        sim.state.projects.done.add("school_founded")
        if sim.state.projects.done_year is None:
            sim.state.projects.done_year = {}
        sim.state.projects.done_year["school_founded"] = 100  # same year
        sim.state.projects.operating.add("school_founded")

        sim.civ["literacy_elite"] = 0.5

        # Manually call _advance_literacy to generate message
        sim._literacy_said = 0  # Reset message timer to allow message
        sim._advance_literacy(100)

        # The message should either:
        # 1. Not be logged (literacy didn't change enough)
        # 2. Use different wording like "beginning to show" instead of "a generation"
        messages = sim.state.household.log
        if messages:
            last_message_text = messages[-1][1]
            school_age = 100 - 100  # 0 years old
            if school_age < 25:
                # Should NOT say "a generation of schooling" for young schools
                if "a generation of schooling" in last_message_text:
                    self.fail(f"School age {school_age} years: message should not say "
                             f"'a generation of schooling'")


if __name__ == "__main__":
    unittest.main()
