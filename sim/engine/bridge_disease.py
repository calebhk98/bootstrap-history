"""Bridge entries the disease module reads until the owners behind them move into modules.

Each view carries the name its owner will publish (docs/architecture/catalogue), asks the engine exactly as the old
disease adapter did, and is never cached. The `legacy_*` view is raw state the module still needs; it goes when that
state moves."""
from sim.assembly.api import KEYED, QUOTE
from sim.disease.api import nation_tuning

from .bridge import bridge_view


# ---- demography ---------------------------------------------------------------------------------------------------

@bridge_view("people_by_band")
def people_by_band(sim):
    """{band: people} of the nation's three age bands."""
    return {band: float(getattr(sim.population, band)) for band in nation_tuning.BANDS}


@bridge_view("nutrition_ratio", kind=QUOTE)
def nutrition_ratio(sim, food_kcal_per_day):
    """How far the food (kcal per day) meets what the nation's people need: 1.0 is exactly enough."""
    return sim.population.nutrition_ratio(food_kcal_per_day)


@bridge_view("legacy_regions_of_people")
def legacy_regions_of_people(sim):
    """{tile: people by band, in band order} the engine tracks, or None before it does (the object itself: a debt)."""
    return getattr(getattr(sim.state, "population", None), "regions", None)


@bridge_view("urban_fraction")
def urban_fraction(sim):
    """Share of the nation's people living in town, from its regions."""
    return sim.urban_fraction()


@bridge_view("regional_flows_last_year")
def regional_flows_last_year(sim):
    """{tile: the regional step's flows} of the last year the regions were stepped, or None before one (the object itself)."""
    return getattr(sim, "_last_regional_step", None)


# ---- land and public works -----------------------------------------------------------------------------------------

@bridge_view("home_tiles_held")
def home_tiles_held(sim):
    """The tiles the home country owns, sorted."""
    return sim.home_tiles_held()


@bridge_view("coverage_share", kind=KEYED)
def coverage_share(sim, node_id):
    """The share of the people who can use the work that it serves while it is open, 0 to 1."""
    return sim.coverage_share(node_id)
