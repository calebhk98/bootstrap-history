"""Complaint 95: figures for wages, state notice, epidemics and project throughput, and the per-year `cashbook` screen that
reconciles cash. Complaint 640: the figures are read from a stand-in game, the cash book's rows are built from a book made
here, and the screens are rendered from hand-written replies; there are no played-game checks."""
QUICK_TOPIC = True

import unittest
from types import SimpleNamespace
from unittest import mock

from sim.tests.ui_stand_in import StandIn
from sim.ui import figures as figure_registry
from sim.ui import figures_world  # noqa: F401  (registers the figures)
from sim.ui.proto import dispatch_cash_ledger
from sim.ui.proto.render_cash_ledger import render_cash_ledger
from sim.ui.proto.render_figures import render_figures

NEW_FIGURES = ("wages", "state_notice", "epidemic", "project_throughput")


class _Game(StandIn):
    """Only what the four world figures read."""

    def __init__(self):
        self.employees = {"smith": 2, "weaver": 1}
        super().__init__(
            wage_index=1.25, pop_scale=0.9, price_index=1.1, material_throttle=0.8, year=100,
            staff=lambda: {"employees": self.employees},
            eminence_report={"now": 3.0, "settles_at_if_nothing_changes": 5.0, "chance_of_ruin_this_year": 0.01},
            state_notice=0.25, state_reach=0.4, household_scale=1.5, hazard_figure=lambda kind, hazard: 0.2,
            techniques_held={"a", "b", "c"}, techniques_granted={"a"}, active_projects={"x": {}}, civilisation={"hazards": []})


class FigureTests(unittest.TestCase):

    def test_the_new_figures_are_registered(self):
        self.assertTrue(set(NEW_FIGURES) <= set(figure_registry.FIGURES))

    def test_the_wage_figure_is_the_engines_wage_index_with_its_drivers(self):
        reading = figure_registry.read_figure(_Game(), "wages")
        self.assertAlmostEqual(reading["value"], 1.25, places=4)
        self.assertEqual(set(reading["drivers"]), {"population_scale", "price_index"})

    def test_the_state_notice_figure_reads_the_notice_and_its_drivers(self):
        reading = figure_registry.read_figure(_Game(), "state_notice")
        self.assertEqual(reading["value"], 0.25)
        self.assertEqual(reading["drivers"]["eminence"], 3.0)

    def test_project_throughput_counts_the_projects_done_that_are_not_granted(self):
        reading = figure_registry.read_figure(_Game(), "project_throughput")
        self.assertEqual(reading["value"], 2)
        self.assertEqual(reading["drivers"]["employees"], 3)

    def test_the_epidemic_figure_is_zero_with_no_epidemic_under_way(self):
        forecast = {"expected_deaths": 0, "expected_working_age_share": 0.0, "by_pathogen": []}
        with mock.patch.object(figures_world.ui_port, "epidemic_forecast", lambda sim: forecast), \
                mock.patch.object(figures_world.ui_port, "last_demographic_step", lambda sim: None), \
                mock.patch.object(figures_world.ui_port, "disease_burden", lambda sim: 0.1):
            reading = figure_registry.read_figure(_Game(), "epidemic")
        self.assertEqual(reading["value"], 0.0)
        self.assertEqual(reading["drivers"], {"disease_burden": 0.1, "expected_deaths": 0, "people_infected": 0})

    def test_the_epidemic_figure_is_the_models_forecast_share_of_working_age_people(self):
        forecast = {"expected_deaths": 900, "expected_working_age_share": 0.2,
                    "by_pathogen": [{"infected": 40, "expected_deaths": 500}, {"infected": 2, "expected_deaths": 400}]}
        with mock.patch.object(figures_world.ui_port, "epidemic_forecast", lambda sim: forecast), \
                mock.patch.object(figures_world.ui_port, "last_demographic_step", lambda sim: None), \
                mock.patch.object(figures_world.ui_port, "disease_burden", lambda sim: 0.1):
            reading = figure_registry.read_figure(_Game(), "epidemic")
        self.assertEqual(reading["value"], 0.2)
        self.assertEqual(reading["drivers"]["people_infected"], 42)


class CashBookRowTests(unittest.TestCase):

    def test_a_year_whose_causes_add_up_has_nothing_not_itemised(self):
        row = dispatch_cash_ledger._year_row(10, 1000.0, 1500.0, {"sales": 700.0, "wages": -200.0}, False)
        self.assertEqual(row["not_itemised"], 0.0)
        self.assertEqual(row["closing"] - row["opening"], sum(cause["amount"] for cause in row["causes"]))

    def test_what_the_causes_leave_out_is_named_so_every_row_reconciles(self):
        row = dispatch_cash_ledger._year_row(11, 1500.0, 1400.0, {"wages": -150.0}, True)
        self.assertEqual(row["not_itemised"], 50.0)
        self.assertAlmostEqual(row["closing"] - row["opening"] - sum(c["amount"] for c in row["causes"])
                               - row["not_itemised"], 0.0)

    def test_a_gap_within_the_rounding_of_the_book_is_not_called_unitemised(self):
        row = dispatch_cash_ledger._year_row(11, 1500.0, 1400.5, {"wages": -100.0}, True)
        self.assertEqual(row["not_itemised"], 0.0)

    def test_causes_are_listed_largest_first(self):
        row = dispatch_cash_ledger._year_row(10, 0.0, 480.0, {"a": 10.0, "b": 500.0, "c": -30.0}, False)
        self.assertEqual([cause["cause"] for cause in row["causes"]], ["b", "c", "a"])

    def test_the_ledger_shows_the_last_closed_years_and_the_open_year_last(self):
        earlier = [{"year": year, "opening": 0.0, "closing": 0.0, "causes": {}} for year in range(5)]
        book = {"earlier_years": earlier, "year": 5, "opening": 0.0, "closing": 40.0, "causes": {"sales": 40.0}}
        ledger = dispatch_cash_ledger.cash_ledger(SimpleNamespace(view=lambda name: (lambda: book)))
        self.assertEqual([row["year"] for row in ledger["years"]], [2, 3, 4, 5])
        self.assertEqual([row["open_year"] for row in ledger["years"]], [False, False, False, True])


class RenderTests(unittest.TestCase):
    """The screens, on hand-written replies; the subject is presentation."""

    def test_the_cashbook_lists_opening_causes_and_closing_for_a_closed_year_and_marks_the_open_one(self):
        text = render_cash_ledger({"ok": True, "years": [
            {"year": 10, "open_year": False, "opening": 1000.0, "closing": 1500.0,
             "causes": [{"cause": "sales", "amount": 700.0}, {"cause": "wages", "amount": -200.0}],
             "not_itemised": 0.0},
            {"year": 11, "open_year": True, "opening": 1500.0, "closing": 1400.0,
             "causes": [{"cause": "wages", "amount": -150.0}], "not_itemised": 50.0}]})
        # presentation: the labels a player reads on the cash book screen
        for word in ("opening cash", "sales", "wages", "closing cash", "open, so far", "not itemised"):
            self.assertIn(word, text)

    def test_the_figures_listing_renders(self):
        listing = render_figures({"figures": [{"name": "wages", "label": "wage level", "unit": "index"}]})
        self.assertIn("wages", listing)   # presentation: the listing shows each figure's name


if __name__ == "__main__":
    unittest.main()
