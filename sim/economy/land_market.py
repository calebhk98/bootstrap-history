"""The land market: what a tile's arable land is worth to the producers who want it.

Supply on a tile is its arable hectares, whose quality falls smoothly from the best land to the worst
(LAND_BAND_* give the spread). Demand is each producer's land per run times the runs it wants, plus the
hectares households work for themselves. The best land is used first, so hectares worked on worse land
yield less: land is let at a Ricardian differential rent, per hectare the value of the extra output the
land in use gives over the marginal hectare, at the output price producers expected; it rises
continuously with the land used. Where demand exceeds all the arable land the marginal hectare is the
worst and rent also rises to ration it: LAND_SCARCITY_RENT_SHARE of what a hectare of the worst land
still earns above the other costs of working it. Producers are then granted only a share of what they
asked for, which caps their runs.

Pure functions: `clear_land` and `rent_postings`. `settle_year` applies them to an economy record.
Households pay no rent on the plots they work (they own them); producers pay the tile's owner cohort,
and `ownership.spread` shares it among the tile's cohorts.
"""
import dataclasses
import math
from dataclasses import dataclass
from typing import Dict, List, Mapping, Optional, Sequence

from sim.constants import declare

from . import ownership, unit_cost
from .land_lease import LAND_RENT_ADJUSTMENT_SHARE, posted_rents  # noqa: F401
from .producers import expected_output_prices, live_input_prices, live_wages
from .types import AgentId, CurrencyId, TileId, Transfer

LAND_BAND_AREA_SHARES = declare(
    "LAND_BAND_AREA_SHARES", (0.2, 0.3, 0.3, 0.2), kind="temporary_heuristic",
    unit="share of a tile's arable hectares, best band first", source=None, confidence="D",
    why="Fields within one tile differ in soil, slope and water, and the tile record keeps one mean "
        "fertility. A fixed spread of quality bands stands in for that variation; soil-class and slope "
        "layers per tile would give the real spread and replace it.")
LAND_BAND_RELATIVE_FERTILITY = declare(
    "LAND_BAND_RELATIVE_FERTILITY", (1.3, 1.1, 0.9, 0.7), kind="temporary_heuristic",
    unit="yield of the band relative to the tile's mean fertility", source=None, confidence="D",
    why="Pairs with LAND_BAND_AREA_SHARES (area-weighted mean one). The spread of fertility inside a "
        "tile is not in the data; soil-class and slope layers per tile would replace it.")
LAND_SCARCITY_RENT_SHARE = declare(
    "LAND_SCARCITY_RENT_SHARE", 0.5, kind="temporary_heuristic",
    unit="share of the worst band's surplus per hectare charged as rent when land is short",
    source=None, confidence="D",
    why="With every hectare spoken for, landlords can ask up to all of what the worst land earns above "
        "its other costs; producers need no demand curve for land here, so how much they get to keep "
        "is a bargaining outcome the model does not derive. A land auction or tenancy contract model "
        "would replace the share.")
HECTARES_PER_SQUARE_KILOMETRE = declare(
    "HECTARES_PER_SQUARE_KILOMETRE", 100.0, kind="physical_constant", unit="hectares per km2",
    source="definition", confidence="A", why="Unit conversion from a tile's area in km2 to hectares.")


@dataclass(frozen=True)
class LandDemand:
    agent_id: AgentId
    tile: TileId
    hectares: float                        # hectare-years wanted: land per run times runs wanted
    output_value_per_hectare: float        # at average fertility and the price producers expect
    other_cost_per_hectare: float          # inputs and labour for the runs that work a hectare


@dataclass(frozen=True)
class LandResult:
    rent_per_hectare_by_tile: Dict[TileId, float]    # mean rent a producer pays per hectare granted
    granted_hectares: Dict[AgentId, float]


def arable_hectares(tile) -> float:
    return max(0.0, tile.land_area_km2 * HECTARES_PER_SQUARE_KILOMETRE * tile.arable_fraction)


def _weighted(demands: Sequence[LandDemand], attribute: str) -> float:
    total = sum(demand.hectares for demand in demands)
    return sum(getattr(demand, attribute) * demand.hectares for demand in demands) / total if total > 0.0 else 0.0


def _fertility_knots():
    """(cumulative share of the tile's land, relative fertility) from the best land down: each band's
    fertility sits at the middle of the band and the fertility of the land between is interpolated, so
    the quality of the marginal hectare falls smoothly as more land is used."""
    knots, taken = [(0.0, None)], 0.0
    for fertility, share in sorted(zip(LAND_BAND_RELATIVE_FERTILITY, LAND_BAND_AREA_SHARES), reverse=True):
        knots.append((taken + share / 2.0, fertility))
        taken += share
    knots[0] = (0.0, knots[1][1])
    knots.append((1.0, knots[-1][1]))
    return knots


def _used_land_quality(fraction: float):
    """(fertility of the marginal hectare, mean fertility of all the land used) when `fraction` of the
    tile's land is in use, the best land first."""
    knots = _fertility_knots()
    fraction = min(max(fraction, 0.0), 1.0)
    area = 0.0
    for (start, high), (end, low) in zip(knots, knots[1:]):
        if end <= start:
            continue
        reach = min(fraction, end)
        if reach <= start:
            break
        marginal = high + (low - high) * (reach - start) / (end - start)
        area += (high + marginal) / 2.0 * (reach - start)
        if fraction <= end:
            return marginal, area / fraction
    return knots[-1][1], area / fraction if fraction > 0.0 else knots[0][1]


def _clear_tile(supply: float, own_plots: float, demands: Sequence[LandDemand]):
    """(rent per hectare, hectares granted to each demand) on one tile."""
    own = min(max(0.0, own_plots), supply)
    wanted = sum(demand.hectares for demand in demands)
    room = supply - own
    scale = min(1.0, room / wanted) if wanted > 0.0 else 1.0
    granted = [demand.hectares * scale for demand in demands]
    in_use = own + sum(granted)
    if in_use <= 0.0 or wanted <= 0.0:
        return 0.0, granted
    value, cost = _weighted(demands, "output_value_per_hectare"), _weighted(demands, "other_cost_per_hectare")
    marginal, mean_fertility = _used_land_quality(in_use / supply if supply > 0.0 else 1.0)
    differential = value * max(0.0, mean_fertility - marginal)
    short = own + wanted > supply * (1.0 + 1e-12)
    scarcity = LAND_SCARCITY_RENT_SHARE * max(0.0, value * marginal - cost) if short else 0.0
    return differential + scarcity, granted


def clear_land(arable_by_tile: Mapping[TileId, float], demands: Sequence[LandDemand],
               own_plot_hectares: Optional[Mapping[TileId, float]] = None) -> LandResult:
    """Rent per hectare for each tile that has producers asking for land, and each one's grant."""
    own_plot_hectares = own_plot_hectares or {}
    by_tile: Dict[TileId, List[LandDemand]] = {}
    for demand in demands:
        by_tile.setdefault(demand.tile, []).append(demand)
    rents: Dict[TileId, float] = {}
    granted: Dict[AgentId, float] = {}
    for tile, tile_demands in sorted(by_tile.items()):
        rent, shares = _clear_tile(max(0.0, arable_by_tile.get(tile, 0.0)), own_plot_hectares.get(tile, 0.0),
                                   tile_demands)
        rents[tile] = rent
        for demand, hectares in zip(tile_demands, shares):
            granted[demand.agent_id] = hectares
    return LandResult(rents, granted)


def rent_postings(result: LandResult, demands: Sequence[LandDemand], owner_by_tile: Mapping[TileId, AgentId],
                  currency: CurrencyId, cash_by_agent: Optional[Mapping[AgentId, float]] = None) -> List[Transfer]:
    """Each producer pays its tile's owner the tile's rent per hectare times the hectares granted, no
    more than the cash it holds when `cash_by_agent` is given."""
    postings = []
    for demand in demands:
        owner = owner_by_tile.get(demand.tile)
        amount = result.rent_per_hectare_by_tile.get(demand.tile, 0.0) * result.granted_hectares.get(demand.agent_id, 0.0)
        if cash_by_agent is not None:
            amount = min(amount, max(0.0, cash_by_agent.get(demand.agent_id, 0.0)))
        if owner is not None and amount > 0.0:
            postings.append(Transfer(demand.agent_id, owner, currency, amount, "rent"))
    return postings


def demands_of(setup, record, view, wanted_runs: Mapping[AgentId, float]) -> List[LandDemand]:
    """One demand per producer whose recipe takes land and that wants runs this year."""
    demands = []
    for producer_id, producer in sorted(record.producers.items()):
        land_per_run = setup.land_per_run.get(producer.recipe_id, 0.0)
        runs = wanted_runs.get(producer_id, 0.0)
        if land_per_run <= 0.0 or runs <= 0.0:
            continue
        recipe = setup.recipes[producer.recipe_id]
        revenue = unit_cost.revenue_per_run(recipe, expected_output_prices(producer, recipe, view)) * producer.yield_factor
        cost = unit_cost.variable_cost_per_run(recipe, live_input_prices(producer, recipe, view),
                                               live_wages(producer, recipe, view))
        if not math.isfinite(cost):
            continue
        demands.append(LandDemand(producer_id, producer.tile, land_per_run * runs,
                                  revenue / land_per_run, cost / land_per_run))
    return demands


def settle_year(setup, record, view, wanted_runs: Mapping[AgentId, float],
                own_plot_hectares: Optional[Mapping[TileId, float]] = None) -> List[Transfer]:
    """Clear each tile's land for the runs producers want, set next year's rent (land_lease.posted_rents
    follows the clearing rent slowly) and caps on the record
    and its producers, and book the rent: producers pay the tile's owner, shared by ownership.spread.
    Returns the payments made (to cohorts), for the year's property income."""
    demands = demands_of(setup, record, view, wanted_runs)
    arable = {tile_id: arable_hectares(tile) for tile_id, tile in setup.tiles.items()}
    cleared = clear_land(arable, demands, own_plot_hectares)
    result = dataclasses.replace(cleared, rent_per_hectare_by_tile=posted_rents(record.land_rent,
                                                                              cleared.rent_per_hectare_by_tile))
    record.land_rent = dict(result.rent_per_hectare_by_tile)
    for producer_id, producer in list(record.producers.items()):
        land_per_run = setup.land_per_run.get(producer.recipe_id, 0.0)
        if land_per_run <= 0.0:
            continue
        asked = next((demand.hectares for demand in demands if demand.agent_id == producer_id), 0.0)
        granted = result.granted_hectares.get(producer_id, asked)
        record.producers[producer_id] = dataclasses.replace(
            producer, land_rent_per_run=result.rent_per_hectare_by_tile.get(producer.tile, 0.0) * land_per_run,
            land_run_cap=granted / land_per_run if granted < asked - 1e-9 else -1.0)
    money = setup.currency_id
    owners = {tile: ownership.owner_cohort(record, tile) for tile in result.rent_per_hectare_by_tile}
    cash = {demand.agent_id: record.book.balance(demand.agent_id, money) for demand in demands}
    payments = ownership.spread(record, rent_postings(result, demands, owners, money, cash))
    record.book.transfer_many(payments)
    return payments
