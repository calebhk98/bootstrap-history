"""Shared by the full-length opening topics (one topic per civilisation, so the runner places them side by side):
the expected-failure table and the generated checks of one civilisation's opening. See
test_full_length_opening_checks.py for the rule."""
import contextlib
import os
import unittest

from sim.engine import opening_checks_run, shipped_openings, solve_cache

# Set to compute a stale opening instead of failing (tens of minutes per civilisation).
COMPUTE_STALE_ENV = "ROME_COMPUTE_STALE_OPENINGS"
# The cache namespaces whose miss is a spin-up or a margin solve, minutes each; the rest are cheap to solve.
EXPENSIVE_NAMESPACES = ("agent_economy", "opening_traces", "backing_margin")

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

class StaleShippedOpening(AssertionError):
    """The opening a player gets is neither on disk nor shipped for the current source."""


@contextlib.contextmanager
def refusing_to_compute_openings():
    """Within the block a cache miss on a spin-up, trace or margin (no disk entry, none shipped) raises
    StaleShippedOpening at once instead of computing it."""
    real = solve_cache.cached_json

    def guarded(key, compute, cache_dir=None):
        directory = cache_dir or solve_cache.DEFAULT_CACHE_DIRECTORY
        namespace = os.path.basename(directory)
        if (namespace in EXPENSIVE_NAMESPACES and not os.path.exists(os.path.join(directory, key + ".json"))
                and shipped_openings.read(namespace, key) is None):
            raise StaleShippedOpening(
                "the shipped openings are stale (no %s entry for this source); run `python3 sim/simulator.py openings` "
                "to regenerate them, or set %s=1 to compute this opening here" % (namespace, COMPUTE_STALE_ENV))
        return real(key, compute, cache_dir=cache_dir)

    solve_cache.cached_json = guarded
    try:
        yield
    finally:
        solve_cache.cached_json = real


_results = {}


def results_of(civilisation):
    """The checks of `civilisation`'s full-length opening, run once per process. A stale opening fails every
    check at once with the message to regenerate it."""
    if civilisation not in _results:
        guard = contextlib.nullcontext() if os.environ.get(COMPUTE_STALE_ENV) else refusing_to_compute_openings()
        try:
            with guard:
                _results[civilisation] = {each.name: each for each in opening_checks_run.check_civilisation(civilisation)}
        except StaleShippedOpening as stale:
            _results[civilisation] = stale
    if isinstance(_results[civilisation], Exception):
        raise _results[civilisation]
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
        def opening_is_current(self):
            # outside expectedFailure, so a stale opening is never read as an expected failure
            results_of(civilisation)
        opening_is_current.__doc__ = "the opening of %s is on disk or shipped" % civilisation
        setattr(test_class, "test_opening_is_current_%s" % civilisation, opening_is_current)
        for check in CHECK_NAMES:
            setattr(test_class, "test_%s_%s" % (check, civilisation), _test_of(check, civilisation))
        return test_class
    return add
