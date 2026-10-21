"""Complaint 95: a figure registers its components once, and `explain_figure` shows last year, this year and the named causes.
`figures.register_figure` and `explain_figure` are called on a stub game with figures the test registers; the headline
figures are checked to be registered. The `figures` and `why` commands on a game are
`test_figures_inspector_scenario`."""
QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

from sim.ui import figures as figure_registry
from sim.ui import figures_headline  # noqa: F401  (registers the headline figures)

HEADLINE = ("cash", "recurring_net", "income", "upkeep", "population",
            "literacy_general", "price_index", "hazard")


class Game(SimpleNamespace):
    """A game at a year whose figures read from plain attributes."""


def history_record(year, figure_name, value, components=None):
    return {"year": year, "figures": {figure_name: {"value": value, "components": components or {}, "flows": {}, "drivers": {}}}}


class FigureInspectorTests(unittest.TestCase):
    def setUp(self):
        self.registered = []

    def tearDown(self):
        for name in self.registered:
            figure_registry.FIGURES.pop(name, None)

    def register(self, name, compute, digits=1):
        figure_registry.register_figure(name, name, "units", digits, compute)
        self.registered.append(name)

    def test_every_headline_figure_is_registered(self):
        self.assertTrue(set(HEADLINE) <= set(figure_registry.FIGURES))

    def test_a_newly_registered_figure_is_explained_with_no_list_edited(self):
        self.register("test_probe", lambda game: {"value": 7.0, "components": {"alpha": 3.0, "beta": 4.0}})
        probe = figure_registry.explain_figure(Game(year=1300), "test_probe", [])
        self.assertTrue(probe["ok"])
        self.assertEqual(probe["current"], 7.0)
        self.assertEqual({cause["cause"] for cause in probe["causes"]}, {"alpha", "beta"})

    def test_before_a_year_has_passed_there_is_no_previous_value(self):
        self.register("test_probe", lambda game: {"value": 7.0, "components": {"alpha": 7.0}})
        probe = figure_registry.explain_figure(Game(year=1300), "test_probe", [])
        self.assertIsNone(probe["previous"])
        self.assertIsNone(probe["change"])

    def test_a_figure_reports_last_year_this_year_and_the_change(self):
        self.register("test_probe", lambda game: {"value": game.value, "components": {"alpha": game.value}})
        history = [history_record(1299, "test_probe", 4.0, {"alpha": 4.0})]
        probe = figure_registry.explain_figure(Game(year=1300, value=10.0), "test_probe", history)
        self.assertEqual((probe["previous"], probe["current"], probe["change"]), (4.0, 10.0, 6.0))

    def test_the_causes_add_up_to_the_change(self):
        self.register("test_probe", lambda game: {"value": 10.0, "components": {"alpha": 6.0, "beta": 4.0}})
        history = [history_record(1299, "test_probe", 4.0, {"alpha": 3.0, "beta": 1.0})]
        probe = figure_registry.explain_figure(Game(year=1300), "test_probe", history)
        self.assertAlmostEqual(sum(cause["contribution"] for cause in probe["causes"]), probe["change"], delta=0.05)

    def test_what_the_named_parts_leave_out_is_reported_as_its_own_cause(self):
        self.register("test_probe", lambda game: {"value": 10.0, "components": {"alpha": 6.0}})
        history = [history_record(1299, "test_probe", 4.0, {"alpha": 3.0})]
        probe = figure_registry.explain_figure(Game(year=1300), "test_probe", history)
        unexplained = [cause for cause in probe["causes"] if cause["cause"] == figure_registry.UNEXPLAINED_CAUSE]
        self.assertEqual(len(unexplained), 1)
        self.assertAlmostEqual(unexplained[0]["contribution"], 3.0)
        self.assertAlmostEqual(sum(cause["contribution"] for cause in probe["causes"]), probe["change"], delta=0.05)

    def test_only_an_earlier_year_counts_as_last_year(self):
        self.register("test_probe", lambda game: {"value": 10.0, "components": {}})
        history = [history_record(1300, "test_probe", 99.0)]
        probe = figure_registry.explain_figure(Game(year=1300), "test_probe", history)
        self.assertIsNone(probe["previous"])


if __name__ == "__main__":
    unittest.main()
