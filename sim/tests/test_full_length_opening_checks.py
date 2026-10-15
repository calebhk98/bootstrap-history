"""Complaint 523: relationship checks on each civilisation's full-length opening, the one a player gets.

The suite shortens the spin-up (`ROME_SPIN_UP_YEARS`), so a relationship that holds there says little about the
game a player opens. This topic opens each civilisation on the declared-length spin-up (the shipped openings when
they match the source, else computed and kept in the disk cache), runs sim/engine/opening_checks_run.py on it and
asserts every check. Slow: a cold opening is minutes per civilisation, a warm one a cache read and a year's step.

A check that fails today is marked `expectedFailure` against the complaint that owns it (EXPECTED_FAILURES), so
the topic is green, and reports an unexpected success when that complaint's work makes it pass: remove the entry
then. A check not in the table must pass.
"""
import unittest

from sim.engine import opening_checks_run

CIVILISATIONS = ("rome_100ad", "han_china_100ad", "mexica_1500", "norse_900ad", "england_1300")

# {(check, civilisation): the complaint whose work makes it pass}
EXPECTED_FAILURES = {
    # a sited ore opens at many times its making cost (Complaints/519)
    ("price_over_cost_sited_ores", "rome_100ad"): "519",
    ("price_over_cost_sited_ores", "han_china_100ad"): "519",
    ("price_over_cost_sited_ores", "mexica_1500"): "519",
    ("price_over_cost_sited_ores", "norse_900ad"): "519",
    # the coin metal opens at many times its making cost: the opening's prices are not seeded from the
    # calculator at the economy's wages (Complaints/507, Stage 2)
    ("price_over_cost_coin_metal", "rome_100ad"): "507 Stage 2",
    ("price_over_cost_coin_metal", "han_china_100ad"): "507 Stage 2",
    ("price_over_cost_coin_metal", "norse_900ad"): "507 Stage 2",
    ("price_over_cost_coin_metal", "england_1300"): "507 Stage 2",
    # the opening's wage is below the household's floor: capacity and income do not agree (Complaints/507, Stage 2)
    ("wage_over_floor", "england_1300"): "507 Stage 2",
    # the coin lost to wear is not replaced, and the spin-up does not settle (Complaints/473)
    ("money_against_wear", "rome_100ad"): "473",
    ("money_against_wear", "han_china_100ad"): "473",
    ("money_against_wear", "england_1300"): "473",
    ("spin_up_settled", "rome_100ad"): "473",
    ("spin_up_settled", "han_china_100ad"): "473",
    ("spin_up_settled", "mexica_1500"): "473",
    ("spin_up_settled", "norse_900ad"): "473",
    ("spin_up_settled", "england_1300"): "473",
}

_results = {}


def results_of(civilisation):
    """The checks of `civilisation`'s full-length opening, run once per process."""
    if civilisation not in _results:
        _results[civilisation] = {each.name: each for each in opening_checks_run.check_civilisation(civilisation)}
    return _results[civilisation]


CHECK_NAMES = ("price_over_cost_sited_ores", "price_over_cost_staple", "price_over_cost_coin_metal",
               "money_against_wear", "wage_over_floor", "spin_up_settled")


class FullLengthOpeningTests(unittest.TestCase):
    pass


def _test_of(check, civilisation):
    def test(self):
        result = results_of(civilisation)[check]
        self.assertTrue(result.passed, "%s of %s: value %s against %s %s; %s" % (
            check, civilisation, result.value, result.bound_kind, result.bound, dict(result.detail)))
    test.__doc__ = "%s of %s" % (check, civilisation)
    return unittest.expectedFailure(test) if (check, civilisation) in EXPECTED_FAILURES else test


for _civilisation in CIVILISATIONS:
    for _check in CHECK_NAMES:
        setattr(FullLengthOpeningTests, "test_%s_%s" % (_check, _civilisation), _test_of(_check, _civilisation))


class ExpectedFailureTableTests(unittest.TestCase):
    def test_every_expected_failure_names_a_known_check_civilisation_and_complaint(self):
        for (check, civilisation), complaint in EXPECTED_FAILURES.items():
            self.assertIn(check, CHECK_NAMES)
            self.assertIn(civilisation, CIVILISATIONS)
            self.assertRegex(complaint, r"^\d+")


if __name__ == "__main__":
    unittest.main()
