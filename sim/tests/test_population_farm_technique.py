"""Complaints 57 and 58: the cohort model is the only population, and a
civilisation's farming technique reaches yield, labour and literacy through
the labour market rather than through side scalars.
"""
import os
import unittest

from .harness import *  # noqa: F401,F403

from sim.labour import labour_allocation
from sim.world import agriculture

_REPOSITORY_SIM_DIRECTORY = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MECHANISATION_NODES = ("horse_collar", "fud_heavy_mouldboard_plough_coulter",
                       "fud_mechanical_reaper", "ag2_reaper")
# Long enough for adoption of a new technique to show in population and in the farm share.
YEARS = 30
# Long enough for a land-bound society's food to bind its people.
LAND_BOUND_YEARS = 60


def _complete(test_sim, node_ids):
    """Mark technologies as completed by the founder this year."""
    for node_id in node_ids:
        test_sim.state.projects.done.add(node_id)
        test_sim.state.projects.done_year[node_id] = test_sim.state.scenario.year


def _run_years(test_sim, years):
    for _ in range(years):
        year = test_sim.state.scenario.year
        test_sim._demographic_recovery(year)
        test_sim.advance_society(year)
        test_sim.state.scenario.year = year + 1


def _rome():
    return sim(civ="rome_100ad", events=False)


def _farm_share(test_sim):
    hours = test_sim.state.economy.society_labour_hours
    return hours[labour_allocation.FARM_TRADE] / sum(hours.values())


def _measure(test_sim):
    farm_year = getattr(test_sim, "_last_farm_year", None)
    hours = test_sim.state.economy.society_labour_hours
    return {"population": test_sim.population.total, "farm_share": _farm_share(test_sim) if hours else None,
            "harvest_kg": farm_year.gross_harvest_kg if farm_year else None,
            "farm_workers": getattr(test_sim, "_last_farm_workers_fte", None)}


_TRAJECTORIES = {}


def _trajectory(name, node_ids, checkpoints):
    """{years run: measurements} for one game that completes `node_ids` at the start and runs on through
    `checkpoints` in order. A game run is the same however many tests read it, so each is run once."""
    if name not in _TRAJECTORIES:
        game = _rome()
        _complete(game, node_ids)
        measured, years_run = {}, 0
        for years in checkpoints:
            _run_years(game, years - years_run)
            years_run = years
            measured[years] = _measure(game)
        _TRAJECTORIES[name] = measured
    return _TRAJECTORIES[name]


def _control():
    """The game with no technology added, measured at the start and after 1, YEARS and YEARS + 1 years."""
    return _trajectory("control", (), (0, 1, YEARS, YEARS + 1))


def _mechanised():
    return _trajectory("mechanised", MECHANISATION_NODES, (1, YEARS // 2 + 1, YEARS + 1))


class NoSecondPopulationTests(unittest.TestCase):
    def test_no_population_scale_scalar_anywhere(self):
        banned = ("_pop_scale" + "_base", "_pop_tech" + "_pending")
        offenders = []
        for directory, _, files in os.walk(_REPOSITORY_SIM_DIRECTORY):
            for name in files:
                path = os.path.join(directory, name)
                if not name.endswith(".py") or path == os.path.abspath(__file__):
                    continue
                with open(path, encoding="utf-8") as handle:
                    text = handle.read()
                offenders += [(path, word) for word in banned if word in text]
        self.assertEqual(offenders, [])


class FoodTechnologyReachesPopulationTests(unittest.TestCase):
    def test_a_food_technology_reaches_the_cohort_model_through_labour_where_food_is_not_scarce(self):
        # Rome's food is not what limits its people, so the technology does not add people; it frees farm workers
        # and the cohorts are no smaller for it.
        improved = _trajectory("food", ("crop_rotation", "fud_three_field_rotation"), (YEARS,))[YEARS]
        control = _control()[YEARS]
        self.assertGreaterEqual(improved["population"], control["population"])
        self.assertLess(improved["farm_workers"], control["farm_workers"])

    def test_a_food_technology_raises_population_once_the_land_is_all_cleared(self):
        # Rome's territory holds several times the farmland it has cleared, so clearing and farm hands meet its food
        # and nutrition stays at need: only the demographic rates move its people. With the arable ground all
        # cleared, land is the limit, and a technique that yields more per hectare feeds more people.
        def land_bound_population(node_ids):
            game = _rome()
            _complete(game, node_ids)
            game._farm_arable_ceiling = game.farm_land.hectares
            _run_years(game, LAND_BOUND_YEARS)
            return game.population.total
        self.assertGreater(
            land_bound_population(("crop_rotation", "fud_three_field_rotation")), land_bound_population(()))

    def test_it_does_not_move_population_on_the_day_it_completes(self):
        improved = _rome()
        _complete(improved, ("crop_rotation",))
        self.assertEqual(improved.population.total, _control()[0]["population"])


class MechanisationTests(unittest.TestCase):
    def test_mechanisation_raises_food_per_farm_worker(self):
        control, improved = _control()[1], _mechanised()[YEARS // 2 + 1]
        control_per_worker = control["harvest_kg"] / control["farm_workers"]
        improved_per_worker = improved["harvest_kg"] / improved["farm_workers"]
        self.assertGreater(improved_per_worker, control_per_worker)

    def test_farm_share_falls_through_the_labour_market_and_food_holds(self):
        control, improved = _control()[YEARS + 1], _mechanised()[YEARS + 1]
        first_year_share = _mechanised()[1]["farm_share"]
        self.assertLess(improved["farm_share"], control["farm_share"])
        self.assertLess(improved["farm_share"], first_year_share)
        self.assertGreaterEqual(improved["harvest_kg"], 0.95 * control["harvest_kg"])

    def test_mechanisation_does_not_cut_the_workforce_in_one_year(self):
        # Workers move only as fast as the labour market lets them.
        self.assertGreater(_mechanised()[1]["farm_share"], 0.5 * _control()[1]["farm_share"])

    def test_a_food_surplus_releases_farm_workers_within_mobility_limits(self):
        test_sim = _rome()
        _run_years(test_sim, 1)
        before = _farm_share(test_sim)
        # A reaper the society took up decades ago: food per worker is
        # now higher than the workforce was sized for.
        year = test_sim.state.scenario.year
        test_sim.state.projects.done.add("fud_mechanical_reaper")
        test_sim.state.projects.done_year["fud_mechanical_reaper"] = year - 50
        _run_years(test_sim, 1)
        after_one_year = _farm_share(test_sim)
        _run_years(test_sim, 9)
        after_ten_years = _farm_share(test_sim)
        _run_years(test_sim, 15)
        self.assertLess(after_ten_years, before)
        self.assertLess(_farm_share(test_sim), after_ten_years)
        # Mobility bounds one year's move.
        self.assertGreater(after_one_year, 0.5 * before)


class LiteracyCostTests(unittest.TestCase):
    def test_literacy_can_pass_the_old_elite_ceiling_with_a_small_farm_share(self):
        test_sim = _rome()
        _run_years(test_sim, 1)
        hours = test_sim.state.economy.society_labour_hours
        total = sum(hours.values())
        farm = 0.02 * total
        for trade in hours:
            hours[trade] = ((total - farm) * hours[trade]
                            / (total - hours[labour_allocation.FARM_TRADE]))
        hours[labour_allocation.FARM_TRADE] = farm
        self.assertGreater(test_sim.literacy_ceiling_elite(), 0.97)
        self.assertGreater(test_sim.literacy_ceiling_general(), 0.97 - 0.05)

    def test_a_large_farm_share_lowers_attainable_literacy(self):
        low = _rome()
        high = _rome()
        for test_sim, farm_share in ((low, 0.05), (high, 0.7)):
            _run_years(test_sim, 1)
            hours = test_sim.state.economy.society_labour_hours
            total = sum(hours.values())
            rest = total - hours[labour_allocation.FARM_TRADE]
            for trade in hours:
                hours[trade] = (total * (1 - farm_share) * hours[trade] / rest)
            hours[labour_allocation.FARM_TRADE] = total * farm_share
        self.assertLess(high.literacy_ceiling_general(), low.literacy_ceiling_general())

    def test_no_mechanisation_count_gates_literacy(self):
        self.assertFalse(hasattr(_rome(), "agrarian_slack"))


class TechniqueTests(unittest.TestCase):
    def test_default_technique_is_the_reference_one(self):
        self.assertEqual(_rome().labour._farming_technique().toolkit, agriculture.DEFAULT_TOOLKIT)

    def test_adoption_grows_with_age(self):
        test_sim = _rome()
        _complete(test_sim, ("fud_mechanical_reaper",))
        early = test_sim.labour._farming_technique().toolkit.reaping_rate_multiplier
        test_sim.state.scenario.year += 60
        late = test_sim.labour._farming_technique().toolkit.reaping_rate_multiplier
        self.assertGreater(late, early)


class SurplusResponseTests(unittest.TestCase):
    def test_a_surplus_lowers_farm_need_and_a_shortfall_raises_it(self):
        common = dict(baseline_fte=100.0, current_fte=100.0,
                      marginal_product_kg_per_hour=5.0, land_hectares=1e9)
        surplus = labour_allocation.farm_workers_needed(
            shortfall_kg=0.0, surplus_kg=1e6, **common)
        shortfall = labour_allocation.farm_workers_needed(
            shortfall_kg=1e6, surplus_kg=0.0, **common)
        self.assertLess(surplus, 100.0)
        self.assertGreater(shortfall, 100.0)
        self.assertGreaterEqual(surplus, 0.0)
