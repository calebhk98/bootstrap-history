"""Scenario: the farm model at its edges, in a game. Barren land, land a farmer cannot live off, the technology that rescues
it and surplus farm labour are each pinned as a property (direction and bounds), never an exact number; the ordinary
game's farm share is a baseline validation (CLAUDE.md 4.2). The ladder over unfarmable ground and the net marginal
product rules are in test_farm_edges."""
import math
import unittest
from unittest import mock

from .harness import *  # noqa: F401,F403
from sim.engine import invariants
from sim.labour import labour_allocation
from sim.engine.food_supply import FoodSupplyMixin
from sim.geography.api import crop_site, tiles_held
from sim.world import agriculture
from sim.labour import labour_market

FARM_TRADE = labour_allocation.FARM_TRADE
CIV_ID = "rome_100ad"
# Years the opening food shortfall takes to work out of the labour market.
WARM_UP_YEARS = 15


def _sites_with_fertility(civ_id, fertility_of_tile):
    """The held tiles' crop sites where each tile's yield factor is `fertility_of_tile(rank, tile_count)`,
    rank 0 being the best tile."""
    share = 1.0 - agriculture.DEFAULT_ROTATION.fallow_share_of_holding
    sites = {tile_id: crop_site(tile_id, share) for tile_id in set(tiles_held(S.load_civ(civ_id)))}
    ranked = sorted(sites, key=lambda tile_id: (-sites[tile_id].yield_factor, tile_id))
    return {tile_id: sites[tile_id]._replace(yield_factor=fertility_of_tile(rank, len(ranked)))
            for rank, tile_id in enumerate(ranked)}


def _sim_with_sites(sites, civ_id=CIV_ID):
    with mock.patch.object(FoodSupplyMixin, "farm_sites", lambda self: sites):
        return sim(civ_id, events=False)


def _sim_on(fertility_of_tile, civ_id=CIV_ID):
    return _sim_with_sites(_sites_with_fertility(civ_id, fertility_of_tile), civ_id)


def _uniform(fertility):
    return lambda _rank, _count: fertility


def _farm_share(test_sim):
    hours = test_sim.state.economy.society_labour_hours
    return hours[FARM_TRADE] / sum(hours.values())


def _run(test_sim, years, first_year=101, until=None):
    """[(population, farm share, nutrition ratio, granary kg)] per year, at most
    `years` of them; stops early once `until(history)` is true."""
    history = []
    for year in range(first_year, first_year + years):
        test_sim._demographic_recovery(year)
        history.append((test_sim.population.total, _farm_share(test_sim),
                        test_sim._last_demographic_step.nutrition_ratio,
                        test_sim.farm_stock_kg))
        invariants.check_simulation_invariants(test_sim.state)
        if until is not None and until(history):
            break
    return history


def _food_ratio_with_everyone_farming(test_sim, fertility):
    """Food one year's harvest yields, net of seed, over the year's food need,
    with every working-age person farming on unlimited land of `fertility`."""
    technique = test_sim.labour._farming_technique()
    workers = test_sim.population.working_age
    hectares = workers * agriculture.hectares_cropped_per_farm_worker(
        technique.crop, technique.toolkit)
    year = agriculture.Storage(stock_kg=0.0, seed=0).step(
        agriculture.Land(hectares, fertility),
        hectares * agriculture.REFERENCE_LABOUR_HOURS_PER_HECTARE,
        test_sim._adult_equivalent_population(test_sim.population),
        crop=technique.crop, rotation=technique.rotation, toolkit=technique.toolkit,
        worker_count=workers, weather_multiplier=1.0)
    return (year.gross_harvest_kg - year.seed_sown_kg) / year.food_demand_kg


_SHARED = {}   # one read-only game and the answers computed from it, built on first use


def _read_only_game():
    """A game nothing runs or changes: tests that only read its opening figures share it."""
    if "game" not in _SHARED:
        _SHARED["game"] = sim(CIV_ID, events=False)
    return _SHARED["game"]


def _fertility_for_food_ratio(target_ratio):
    """Fertility at which everyone farming just yields `target_ratio` of the
    food the whole population needs (bisection on a monotone relation)."""
    if target_ratio in _SHARED:
        return _SHARED[target_ratio]
    probe = _read_only_game()
    low, high = 0.05, 3.0
    for _ in range(50):
        middle = (low + high) / 2.0
        if _food_ratio_with_everyone_farming(probe, middle) < target_ratio:
            low = middle
        else:
            high = middle
    _SHARED[target_ratio] = high
    return high


def _undisturbed_run(years):
    """(history of the first `years` years, farm share at the end of the run) of an ordinary game left alone
    for `years` years; the run is made once and its early rows serve every test that reads a shorter one."""
    if "undisturbed" not in _SHARED:
        game = sim(CIV_ID, events=False)
        history = _run(game, years)
        _SHARED["undisturbed"] = (history, _farm_share(game), years)
    history, final_share, run_years = _SHARED["undisturbed"]
    assert run_years == years
    return history, final_share


def _ample_land_sim(fertility):
    """Rome's people on ground of one fertility, with far more of it than
    they can crop, so fertility alone decides what a farmer produces."""
    probe = sim(CIV_ID, events=False)
    huge = probe.farm_land.hectares * 10.0
    test_sim = probe
    test_sim._farm_ladder = [(fertility, huge)]
    test_sim._farm_arable_ceiling = huge
    test_sim.labour._set_farm_area(min(probe.farm_land.hectares, huge))
    return test_sim


class BarrenLandTests(unittest.TestCase):
    """Smoke scenario: a world with no arable ground opens no farm and its people starve. The rules are
    `farmland_for_population` on an empty ladder (test_farm_clearing) and the ladder leaving out unfarmable
    ground (test_farm_edges); zero and near-zero fertility reach the same empty ladder."""

    def test_no_arable_ground_at_all_builds_and_starves(self):
        sites = {tile_id: site._replace(arable_hectares=0.0, cropped_hectares=0.0)
                 for tile_id, site in _sites_with_fertility(CIV_ID, _uniform(1.0)).items()}
        test_sim = _sim_with_sites(sites)
        self.assertEqual(test_sim.farm_land.hectares, 0.0)
        history = _run(test_sim, 5)
        self.assertLess(history[-1][0], history[0][0])
        for population, share, nutrition, stock in history:
            self.assertTrue(all(math.isfinite(value) for value in (population, share, nutrition, stock)))
            self.assertLess(nutrition, 1.0)
            self.assertGreaterEqual(stock, 0.0)


class SubSubsistenceLandTests(unittest.TestCase):
    """Land where one farmer, all dependants counted, feeds less than one
    farmer-year of food."""

    def setUp(self):
        self.fertility = _fertility_for_food_ratio(0.95)

    def test_the_construction_is_below_subsistence(self):
        probe = _read_only_game()
        self.assertLess(_food_ratio_with_everyone_farming(probe, self.fertility), 1.0)

    def test_population_declines_and_everyone_ends_up_farming(self):
        # The checks read year 80, so the run must pass it; it stops once the decline holds.
        def declined(rows):
            return (len(rows) > 80 and rows[-1][0] < rows[10][0] * 0.8
                    and rows[80][0] < rows[30][0] and rows[-1][1] > 0.9)
        history = _run(_ample_land_sim(self.fertility), 100, until=declined)
        populations = [row[0] for row in history]
        self.assertLess(populations[-1], populations[10] * 0.8)
        self.assertLess(populations[80], populations[30])
        self.assertGreater(history[-1][1], 0.9)
        self.assertGreaterEqual(min(row[3] for row in history), 0.0)

    def test_the_same_land_just_above_subsistence_holds_its_people(self):
        fertility = _fertility_for_food_ratio(1.05)
        # Long enough for a decline on this land to show (the sub-subsistence test above declines well within it).
        history = _run(_ample_land_sim(fertility), 50)
        self.assertGreater(history[-1][0], history[10][0] * 0.9)


class TechnologyRescueTests(unittest.TestCase):
    def test_doubling_the_land_a_farmer_crops_turns_decline_into_recovery(self):
        test_sim = _ample_land_sim(_fertility_for_food_ratio(0.95))
        decline = _run(test_sim, 40)
        trough = decline[-1][0]
        self.assertLess(trough, decline[5][0])
        base = test_sim.labour._farming_technique()
        doubled = base._replace(toolkit=base.toolkit._replace(
            reaping_rate_multiplier=base.toolkit.reaping_rate_multiplier * 2.0))
        test_sim.labour._farming_technique = lambda: doubled
        def recovered(rows):
            return (max(row[0] for row in rows) > trough * 1.05 and rows[-1][0] > trough
                    and rows[-1][1] < 1.0 and rows[-1][2] > 0.99)
        recovery = _run(test_sim, 60, first_year=141, until=recovered)
        populations = [row[0] for row in recovery]
        self.assertGreater(max(populations), trough * 1.05)
        self.assertGreater(populations[-1], trough)
        self.assertLess(recovery[-1][1], 1.0)
        self.assertGreater(recovery[-1][2], 0.99)


_SETTLE_YEARS_AFTER_WARM_UP = 40   # long enough for a 90% farm share to ease back to the right-sized share


def _oversupplied_shares():
    """Farm share per year (first row: just after the oversupply is imposed) of a game whose farm
    share is forced to 90% after warm-up, run at least 30 years and until it is within 0.05 of an
    undisturbed game's share in the same year; one run serves every test that reads it."""
    if "oversupplied" not in _SHARED:
        reference = _undisturbed_run(WARM_UP_YEARS + _SETTLE_YEARS_AFTER_WARM_UP)[0]
        test_sim = sim(CIV_ID, events=False)
        _run(test_sim, WARM_UP_YEARS)
        hours = test_sim.state.economy.society_labour_hours
        total = sum(hours.values())
        others = total - hours[FARM_TRADE]
        for trade in hours:
            hours[trade] = (0.9 * total if trade == FARM_TRADE
                            else hours[trade] * 0.1 * total / others)
        shares = [_farm_share(test_sim)]
        for step in range(_SETTLE_YEARS_AFTER_WARM_UP):
            test_sim._demographic_recovery(WARM_UP_YEARS + 101 + step)
            shares.append(_farm_share(test_sim))
            reference_share = reference[WARM_UP_YEARS + step][1]
            if len(shares) > 30 and abs(shares[-1] - reference_share) <= 0.03:   # inside the 0.05 the test asserts
                break
        _SHARED["oversupplied"] = (shares, reference_share)
    return _SHARED["oversupplied"]


class FarmLabourOversupplyTests(unittest.TestCase):
    def test_workers_leave_the_farm_within_the_mobility_ceiling(self):
        shares = _oversupplied_shares()[0][:31]
        ceiling = labour_market.OCCUPATIONAL_MOBILITY_RATE_CEILING_PER_YEAR
        settled_share = shares[-1]
        for before, after in zip(shares, shares[1:]):
            if before > settled_share + 0.05:
                self.assertLessEqual(after, before + 1e-6)
            self.assertGreaterEqual(after, before * (1.0 - ceiling) - 1e-6)
        self.assertLess(shares[10], shares[0] - 0.2)

    def test_the_farm_settles_between_the_share_that_feeds_need_and_the_share_that_feeds_satiation(self):
        # Hands stay while a farm hour pays at least the wage (Complaint 513), so the farm settles
        # between a right-sized farm and one that feeds the people to the satiation level.
        shares, reference_share = _oversupplied_shares()
        self.assertGreaterEqual(shares[-1], reference_share - 0.05)
        self.assertLessEqual(shares[-1], reference_share * agriculture.MAXIMUM_INTAKE_MULTIPLE_OF_SUBSISTENCE + 0.05)


class ClearingLadderTests(unittest.TestCase):
    def test_clearing_never_brings_worthless_ground_in(self):
        test_sim = _sim_on(lambda rank, count: 0.0 if rank >= count // 2 else 0.5)
        farmable = sum(hectares for _f, hectares in test_sim._farm_ladder)
        _run(test_sim, 40)
        self.assertLessEqual(test_sim.farm_land.hectares, farmable + 1e-6)
        self.assertGreater(test_sim.farm_land.quality, 0.0)


class BaselineValidationTests(unittest.TestCase):
    def test_baseline_validation_ordinary_land_is_farmed_as_before(self):
        # Reference values recorded from the suite's short spin-up with endemic disease (malaria and the herd
        # losses it brings) in the baseline: the people it kills and the herds it thins shift the farm share.
        # Re-recorded when the farm's land quality became the tiles' yield factor (Complaint 537): Rome's cleared best
        # ground includes flood-watered land, so the same people need fewer hands. The tolerances are unchanged.
        history = _undisturbed_run(WARM_UP_YEARS + _SETTLE_YEARS_AFTER_WARM_UP)[0]
        for year_index, population, farm_share in (
                (9, 65332987.2, 0.33958), (19, 65910166.3, 0.34187),
                (29, 66478368.4, 0.34584)):
            note = "baseline validation (4.2), reference values re-recorded under Complaint 537, year index %d" % year_index
            self.assertAlmostEqual(history[year_index][0] / population, 1.0, delta=0.01, msg=note)
            self.assertAlmostEqual(history[year_index][1], farm_share, delta=0.01, msg=note)


if __name__ == "__main__":
    unittest.main()
