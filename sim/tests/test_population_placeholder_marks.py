"""Complaint 172: trades whose population estimate rests on a placeholder (a `temporary_heuristic` constant) show an asterisk in the
population screen, with a legend; trades on a cited estimate or derived from need do not. The screen runs on a reply the test
builds, and which trades are placeholders on a `Labour` over a stand-in world (no game); the screen of a played session is
test_population_placeholder_marks_scenario."""
QUICK_TOPIC = True

import unittest

from sim.constants import REGISTRY
from sim.labour.labour import Labour
from sim.tests.labour_stand_in import stand_in_world
from sim.ui.proto.render_screens_economy import render_population


def _reply(placeholder_trades, plain_trades):
    rows = [{"trade": trade, "is_placeholder": True, "estimated_in_the_country": 100, "within_your_reach": 10, "exists_here": True,
             "you_employ": 0, "share_of_the_reachable_pool_you_employ": 0.0} for trade in placeholder_trades]
    rows += [{"trade": trade, "is_placeholder": False, "estimated_in_the_country": 100, "within_your_reach": 10, "exists_here": True,
              "you_employ": 0, "share_of_the_reachable_pool_you_employ": 0.0} for trade in plain_trades]
    return {"civilisation": "Rome", "population": 1000, "urban_fraction": 0.1, "urban_population_estimate": 100, "trades": rows}


def _trade_lines(text):
    return {line.split()[0].lower(): line for line in text.split("\n") if line.strip() and line.split()[0][0].isalpha()}


class PopulationScreenMarks(unittest.TestCase):
    # presentation: the asterisk, its legend and the table header are the subject of these checks

    def test_a_placeholder_trade_carries_an_asterisk_and_a_plain_one_does_not(self):
        lines = _trade_lines(render_population(_reply(["scribe"], ["smith"])))
        self.assertIn("scribe*", lines["scribe*"])
        self.assertNotIn("*", lines["smith"])

    def test_the_legend_explains_the_asterisk_when_a_placeholder_is_shown(self):
        text = render_population(_reply(["scribe"], ["smith"]))
        self.assertIn("* =", text)
        self.assertIn("placeholder", text.lower())

    def test_there_is_no_legend_when_nothing_is_a_placeholder(self):
        text = render_population(_reply([], ["smith"]))
        self.assertNotIn("* =", text)

    def test_the_screen_has_its_header_and_trade_table(self):
        text = render_population(_reply([], ["smith"]))
        self.assertIn("POPULATION:", text)
        self.assertIn("TRADE", text)
        self.assertIn("IN THE COUNTRY", text)


class PlaceholderFollowsTheRegistry(unittest.TestCase):
    """A trade is a placeholder exactly when the constant its population estimate rests on is a temporary heuristic."""

    def setUp(self):
        self.labour = Labour(stand_in_world())

    def test_the_flag_matches_the_kind_of_the_source_constant_for_every_trade(self):
        mismatches = []
        for trade in sorted(self.labour._world.wages):
            source = self.labour._trade_density_source(trade)
            expected = source is not None and source in REGISTRY and REGISTRY[source].get("kind") == "temporary_heuristic"
            if self.labour._density_is_placeholder(trade) != expected:
                mismatches.append((trade, source))
        self.assertEqual(mismatches, [])

    def test_every_source_constant_a_trade_rests_on_is_declared(self):
        for trade in sorted(self.labour._world.wages):
            source = self.labour._trade_density_source(trade)
            if source is not None:
                self.assertIn(source, REGISTRY, (trade, source))

    def test_a_trade_derived_from_need_is_not_a_placeholder_and_one_on_a_declared_share_is(self):
        derived = [trade for trade in self.labour._world.wages if self.labour._trade_density_source(trade) is None]
        declared = [trade for trade in self.labour._world.wages if self.labour._trade_density_source(trade) is not None]
        self.assertTrue(derived and declared)
        self.assertFalse(any(self.labour._density_is_placeholder(trade) for trade in derived))
        self.assertTrue(any(self.labour._density_is_placeholder(trade) for trade in declared))


if __name__ == "__main__":
    unittest.main()
