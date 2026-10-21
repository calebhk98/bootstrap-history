"""Tenancies in the year (Complaints 538, 551): what landlords ask of tenants given labour's scarcity, and the leases
households with too little land make with holders who have more than their hands work. The rules are in
land_tenancy.py; this reads the economy's record and view for them.

A cohort wants the hectares its floors need beyond what it works, no more than its hands and tools can work; a
holder lets what it holds beyond what it works for its own floors and what it has let already (a holder that is not
a household has no hands and lets everything). Both read the crop margin at the wage the cohort sees, so the ask
falls when labour is scarce.
"""
from typing import Dict, List, Mapping, Tuple

from . import land_bid_year, land_tenancy, titles, titles_ground, titles_worked
from .households_own import Option, plot_hectares
from .setup import labour_area


def _margins(setup, record, view, options: Mapping[str, List[Option]]) -> Dict[str, Tuple[float, str]]:
    """Tile -> (crop margin per hectare net of the wage, the recipe it is grown with), read at a cohort of the tile."""
    margins: Dict[str, Tuple[float, str]] = {}
    for cohort in sorted(record.cohorts.values(), key=lambda each: each.agent_id):
        tile = setup.tiles.get(cohort.tile)
        if tile is not None and cohort.tile not in margins:
            margin, _hours, recipe_id = land_bid_year.best_margin(setup, view, cohort, options, tile)
            margins[cohort.tile] = (margin, recipe_id)
    return margins


def _outside_options(setup, margins: Mapping[str, Tuple[float, str]], posted: Mapping[str, float]) -> Dict[str, float]:
    """Per tile, what a tenant would keep per hectare by taking land on another tile of its labour area instead."""
    options: Dict[str, float] = {}
    for tile in margins:
        options[tile] = land_tenancy.outside_option(
            [margin - posted.get(other, 0.0) for other, (margin, _recipe) in margins.items()
             if other != tile and labour_area(other) == labour_area(tile)])
    return options


def asks(setup, record, view, options: Mapping[str, List[Option]]) -> Dict[str, float]:
    """The rent per hectare landlords ask of tenants on each tile: the posted rent cut to what the tenants can bear
    over their outside option (land_tenancy.rent_ask)."""
    margins = _margins(setup, record, view, options)
    outside = _outside_options(setup, margins, record.land_rent)
    return {tile: land_tenancy.rent_ask(record.land_rent.get(tile, 0.0), margin, outside[tile])
            for tile, (margin, _recipe) in margins.items()}


def _own_hectares(setup, record, cohort, tile, options, recipe_id: str, held_tools_of) -> Tuple[float, float]:
    """(hectares the cohort's floors need, hectares its hands and tools can work)."""
    floors = {need.need_id: need.subsistence_per_person * cohort.people for need in setup.basket_for(cohort.tile).needs}
    needed = plot_hectares(floors, options, setup.recipes, setup.land_per_run, tile.fertility)
    recipe = setup.recipes.get(recipe_id)
    if recipe is None:
        return needed, 0.0
    workable = land_tenancy.hectares_workable(recipe, setup.land_per_run.get(recipe_id, 0.0), held_tools_of(cohort, recipe),
                                              cohort.working_people * setup.working_hours_per_year)
    return needed, workable


def lease_in_market(setup, record, view, options: Mapping[str, List[Option]]) -> List[land_tenancy.Lease]:
    """Offers for tenancies meet holders' lots tile by tile at the ask; each lease becomes a tenancy (titles.lease).
    Returns the leases made."""
    margins = _margins(setup, record, view, options)
    if not margins:
        return []
    outside = _outside_options(setup, margins, record.land_rent)

    def tools_of(cohort, recipe):
        goods = set(recipe.tool_wear) | {step.good for steps in recipe.tool_fallbacks.values() for step in steps if step.good}
        return {good: view.stock(cohort.agent_id, good, cohort.tile) for good in goods}

    offers: List[land_tenancy.Offer] = []
    lots: List[land_tenancy.Lot] = []
    arable_by_tile: Dict[str, float] = {}
    capacity: Dict[Tuple[str, str], float] = {}
    for cohort in sorted(record.cohorts.values(), key=lambda each: each.agent_id):
        tile = setup.tiles.get(cohort.tile)
        if tile is None or cohort.tile not in margins:
            continue
        margin, recipe_id = margins[cohort.tile]
        arable = arable_by_tile.setdefault(cohort.tile, titles_ground.arable_hectares(record, cohort.tile, tile))
        needed, workable = _own_hectares(setup, record, cohort, tile, options, recipe_id, tools_of)
        worked = titles_worked.worked_share(record, cohort.tile, cohort.agent_id) * arable
        capacity[(cohort.tile, cohort.agent_id)] = min(needed, workable)
        wanted = land_tenancy.wanted_hectares(min(needed, workable), worked)
        if wanted > 0.0 and margin - outside[cohort.tile] > 0.0:
            offers.append(land_tenancy.Offer(cohort.agent_id, cohort.tile, wanted, margin - outside[cohort.tile]))
    for tile_id in sorted(arable_by_tile):
        for holder, share in sorted(titles.shares(record, tile_id).items()):
            lettable = land_tenancy.lettable_hectares(share * arable_by_tile[tile_id],
                                                     titles.let_out_share(record, tile_id, holder) * arable_by_tile[tile_id],
                                                     capacity.get((tile_id, holder), 0.0))
            lettable = min(lettable, titles.free_share(record, holder, tile_id) * arable_by_tile[tile_id]
                           - titles.let_out_share(record, tile_id, holder) * arable_by_tile[tile_id])
            if lettable > 0.0:
                lots.append(land_tenancy.Lot(holder, tile_id, lettable))
    asked = {tile: land_tenancy.rent_ask(record.land_rent.get(tile, 0.0), margins[tile][0], outside[tile]) for tile in margins}
    leases = land_tenancy.match(offers, lots, record.land_rent, asked)
    made = []
    for lease in leases:
        if titles.lease(record, lease.tile, lease.tenant, lease.lessor, lease.hectares / arable_by_tile[lease.tile]) > 0.0:
            made.append(lease)
    return made
