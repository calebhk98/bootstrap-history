"""Shared by the full-length opening topics (one topic per civilisation, so the runner places them side by side):
the expected-failure table and the generated checks of one civilisation's opening. See
test_full_length_opening_checks.py for the rule."""
import unittest

from sim.engine import opening_checks_run

CIVILISATIONS = ("rome_100ad", "han_china_100ad", "mexica_1500", "norse_900ad", "england_1300")

# {(check, civilisation): the complaint whose work makes it pass}
EXPECTED_FAILURES = {
    # a sited ore opens at many times its making cost (Complaints/519)
    ("price_over_cost_sited_ores", "rome_100ad"): "519",
    ("price_over_cost_sited_ores", "han_china_100ad"): "519",
    ("price_over_cost_sited_ores", "england_1300"): "519",
    # the coin metal's price is fixed by the coin standard while its making cost follows the wage, which falls over the
    # spin-up (Complaints/473, Update 4; the opening is seeded from the calculator and the coin worth from the marginal
    # cost of its metal, Complaints/507 Stage 2, but the wage still drifts)
    ("price_over_cost_coin_metal", "rome_100ad"): "507 Stage 2",
    ("price_over_cost_coin_metal", "han_china_100ad"): "507 Stage 2",
    ("price_over_cost_coin_metal", "norse_900ad"): "507 Stage 2",
    ("price_over_cost_coin_metal", "england_1300"): "507 Stage 2",
    # the wage falls below the household's floor in the first year: the labour market clears far below the cost table's
    # wage and prices follow it down slowly (Complaints/473, Update 4)
    ("wage_over_floor", "rome_100ad"): "473",
    # the coin lost to wear is not replaced, and the spin-up does not settle (Complaints/473)
    ("money_against_wear", "han_china_100ad"): "473",
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



def _test_of(check, civilisation):
    def test(self):
        result = results_of(civilisation)[check]
        self.assertTrue(result.passed, "%s of %s: value %s against %s %s; %s" % (
            check, civilisation, result.value, result.bound_kind, result.bound, dict(result.detail)))
    test.__doc__ = "%s of %s" % (check, civilisation)
    return unittest.expectedFailure(test) if (check, civilisation) in EXPECTED_FAILURES else test


def opening_check_tests(civilisation):
    """Class decorator: one test per opening check of `civilisation`."""
    def add(test_class):
        for check in CHECK_NAMES:
            setattr(test_class, "test_%s_%s" % (check, civilisation), _test_of(check, civilisation))
        return test_class
    return add
