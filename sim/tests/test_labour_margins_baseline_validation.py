"""BASELINE VALIDATION (CLAUDE.md 4.2, Complaint 640), slow only. Not a rule test: it reads the whole Rome economy after
a year with no intervention, the idle labour, the wage against its floor and the hunger share as
`simulator.py economy-check` prints them (Complaint 398). Prints the figures so a run can be compared before and
after a change; asserts only the relationships that must hold whatever the numbers are, and a failure names
Complaint 398 (labour margins) and 640 (a baseline, not a rule). Run with
`python3 -m sim.tests --slow --only labour_margins_baseline_validation`."""

import functools
import math
import random
import unittest

from . import harness  # noqa: F401  (sets the short spin-up the suite's games open on)
from sim.engine.ui_port import Sim, load, load_civ
from sim.ui.cli_economy_check import FIGURE_LABELS

# One year already shows every figure read below; measure with `simulator.py economy-check` for a longer run.
YEARS = 1


def play(civ_id, seed=1, years=YEARS):
    _tree, _prices, nodes, _wages, _goods = load()
    game = Sim(nodes, [], random.Random(seed), events=False, manual=True, civ=load_civ(civ_id))
    game.done_year = {}
    for _year in range(years):
        game.step()
    return game


@functools.lru_cache(maxsize=None)
def played(civ_id, years):
    """One game per request: the runner calls setUpClass again for every test method."""
    return play(civ_id, years=years)


class BaselineValidation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rome = played("rome_100ad", YEARS)
        cls.report = cls.rome.economy.health()
        for key, meaning in FIGURE_LABELS:
            print("rome_100ad %-20s %s  %s" % (key, cls.report["figures"].get(key), meaning))

    def test_validation_every_decomposition_figure_is_reported(self):
        for key, _meaning in FIGURE_LABELS:
            self.assertIn(key, self.report["figures"])

    def test_validation_some_hours_are_hired_and_none_beyond_those_offered(self):
        self.assertTrue(0.0 < self.report["figures"]["hired_share"] <= 1.0, "baseline validation, Complaints 398 and 640")

    def test_validation_the_unskilled_wage_never_falls_below_the_floor(self):
        figures = self.report["figures"]
        if not math.isnan(figures["wage_over_floor"]):
            self.assertGreaterEqual(figures["wage_over_floor"], 1.0 - 1e-6, "baseline validation, Complaints 398 and 640")

    def test_validation_no_one_starves_on_the_new_floor(self):
        self.assertLess(self.report["figures"]["hunger_share"], 0.2, "baseline validation, Complaints 398 and 640")


if __name__ == "__main__":
    unittest.main()
