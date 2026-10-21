"""Scenarios (Complaints 57 and 58) on a built Rome game run for decades: a food technology reaches the cohort model through the labour
market (and raises population once the land is all cleared), and mechanisation moves workers off the farms no faster than the market
lets them while food holds. The technique, food, labour and literacy rules are in test_population_farm_technique."""
import unittest

from .harness import *  # noqa: F401,F403

from sim.labour import labour_allocation

MECHANISATION_NODES = ("horse_collar", "fud_heavy_mouldboard_plough_coulter",
                       "fud_mechanical_reaper", "ag2_reaper")
# A food technology whose effect is a yield per hectare: a crop with more calories per hectare. A rotation no
# longer carries a yield multiplier; it acts through the cropped share and the soil nitrogen stock, over centuries.
CROP_NODES = ("mat_newworld_crops",)
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


class FoodTechnologyReachesPopulationTests(unittest.TestCase):
    def test_a_food_technology_reaches_the_cohort_model_through_labour_where_food_is_not_scarce(self):
        # Rome's food is not what limits its people, so the technology does not add people; it frees farm workers
        # and the cohorts are no smaller for it.
        improved = _trajectory("food", CROP_NODES, (YEARS,))[YEARS]
        control = _control()[YEARS]
        self.assertGreaterEqual(improved["population"], control["population"])
        self.assertLess(improved["farm_workers"], control["farm_workers"])

    def test_a_food_technology_raises_population_once_the_land_is_all_cleared(self):
        # With the arable ground all cleared, land is the limit, and a technique that yields more per hectare feeds more people.
        def land_bound_population(node_ids):
            game = _rome()
            _complete(game, node_ids)
            game._farm_arable_ceiling = game.farm_land.hectares
            _run_years(game, LAND_BOUND_YEARS)
            return game.population.total
        self.assertGreater(land_bound_population(CROP_NODES), land_bound_population(()))

    def test_it_does_not_move_population_on_the_day_it_completes(self):
        improved = _rome()
        _complete(improved, ("crop_rotation",))
        self.assertEqual(improved.population.total, _control()[0]["population"])


class MechanisationTests(unittest.TestCase):
    def test_mechanisation_raises_food_per_farm_worker(self):
        control, improved = _control()[1], _mechanised()[YEARS // 2 + 1]
        self.assertGreater(improved["harvest_kg"] / improved["farm_workers"], control["harvest_kg"] / control["farm_workers"])

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
        # A reaper the society took up decades ago: food per worker is now higher than the workforce was sized for.
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
        self.assertGreater(after_one_year, 0.5 * before)       # mobility bounds one year's move


if __name__ == "__main__":
    unittest.main()
