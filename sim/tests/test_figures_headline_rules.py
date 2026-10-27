"""Complaint 95: the headline figures read the engine's own functions (revenue, upkeep, capital, population); `figures`
lists every registered figure, an unknown one is refused with a `cause` and the choices, and `why <figure>` falls through
to the figure inspector. Stand-in games carry only what the figures read; the arithmetic of causes is in
test_figures_inspector."""
QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

from sim.engine.readable import readable
from sim.ui import figures as figure_registry
from sim.ui.proto import dispatch_figures, dispatch_inspection
from sim.tests.ui_stand_in import FactViews


class Game(FactViews):
    """What the data-declared figures and `cash` read."""

    year = 1300
    capital = 1234.5
    _dashboard_history = []

    def __init__(self):
        self.population = SimpleNamespace(total=1000.0, children=300.0, working_age=600.0, elderly=100.0)
        self.state = SimpleNamespace(household=SimpleNamespace(cash_periods=[], cash_flow={"wages": -20.0}))

    @readable
    def revenue(self):
        return 77.7

    @readable
    def revenue_sources(self):
        return {"farm": 50.0, "mill": 27.7}

    @readable
    def upkeep(self):
        return 12.3

    @readable
    def upkeep_by_concern(self):
        return {"mill": 12.3}


class HeadlineFigureTests(unittest.TestCase):
    def setUp(self):
        self.game = Game()

    def test_income_is_the_engines_revenue_with_its_sources_as_causes(self):
        reply = dispatch_figures.figure_reply(self.game, "income")
        self.assertTrue(reply["ok"])
        self.assertAlmostEqual(reply["current"], self.game.revenue(), delta=0.05)
        self.assertEqual({cause["cause"] for cause in reply["causes"]}, {"farm", "mill"})

    def test_upkeep_is_the_engines_upkeep(self):
        reply = dispatch_figures.figure_reply(self.game, "upkeep")
        self.assertAlmostEqual(reply["current"], self.game.upkeep(), delta=0.05)

    def test_cash_is_the_households_capital(self):
        reply = dispatch_figures.figure_reply(self.game, "cash")
        self.assertAlmostEqual(reply["current"], self.game.capital, delta=0.05)

    def test_population_is_the_total_with_its_age_groups_as_causes(self):
        reply = dispatch_figures.figure_reply(self.game, "population")
        self.assertEqual(reply["current"], 1000.0)
        self.assertEqual({cause["cause"] for cause in reply["causes"]}, {"children", "working age", "elderly"})

    def test_a_figure_with_no_earlier_year_has_no_previous_value(self):
        reply = dispatch_figures.figure_reply(self.game, "upkeep")
        self.assertIsNone(reply["previous"])

    def test_figures_with_no_name_lists_every_registered_figure(self):
        listing = dispatch_figures.figure_listing()
        self.assertTrue(listing["ok"])
        self.assertEqual({row["name"] for row in listing["figures"]}, set(figure_registry.FIGURES))

    def test_an_unknown_figure_is_refused_with_its_cause_and_the_choices(self):
        reply = dispatch_figures.figure_reply(self.game, "nonsense")
        self.assertFalse(reply["ok"])
        self.assertEqual(reply["error"].cause, "unknown_figure")
        self.assertIn("upkeep", reply["error"].choices)


class WhyFallThroughTests(unittest.TestCase):
    def test_why_of_a_figure_name_that_is_no_node_answers_with_the_figure(self):
        reply = dispatch_inspection._cmd_why(Game(), {}, {"id": "upkeep"}, False)
        self.assertTrue(reply["ok"])
        self.assertEqual(reply["name"], "upkeep")


if __name__ == "__main__":
    unittest.main()
