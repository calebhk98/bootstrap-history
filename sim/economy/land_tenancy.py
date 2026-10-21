"""Tenancies made in the land market (Complaints 538 and 551): what a landlord can ask of tenants, and the offers
for tenancies that meet the land holders have no hands to work.

A tenant's best use of a hectare nets its crop margin: output at the prices it sees, less its hours at the
wage (so the wage, its outside option as a labourer, is already taken off). It would rather take other land
at its rent than pay more than the margin less what that land would leave it. A landlord therefore asks no
more than the posted rent and no more than the tenants can bear over their outside option: when labour is
scarce the wage rises, the margin and the ask fall, and rent falls before wages alone do. Plain functions of the
figures the caller has; any actor can lease out or lease in.
"""
import math
from dataclasses import dataclass
from typing import Dict, List, Mapping, Sequence

from . import tool_fallback
from .types import AgentId, GoodId, Recipe, TileId


@dataclass(frozen=True)
class Offer:
    """A tenancy wanted: hectares a tenant has hands to work on `tile` and the most it pays per hectare."""
    tenant: AgentId
    tile: TileId
    hectares: float
    rent_ceiling: float


@dataclass(frozen=True)
class Lot:
    """Land to let: hectares a holder cannot or will not work itself on `tile`."""
    lessor: AgentId
    tile: TileId
    hectares: float


@dataclass(frozen=True)
class Lease:
    tenant: AgentId
    lessor: AgentId
    tile: TileId
    hectares: float
    rent_per_hectare: float


def outside_option(margins_net_of_rent_elsewhere: Sequence[float]) -> float:
    """What a tenant would keep per hectare by taking other land at its rent instead: the best of them, never
    below nothing (no other land to take is worth nothing)."""
    return max([0.0] + [margin for margin in margins_net_of_rent_elsewhere if math.isfinite(margin)])


def rent_ask(posted_rent: float, crop_margin: float, outside_option_per_hectare: float) -> float:
    """The rent a landlord asks per hectare: the posted rent, cut to what the tenants can pay and still keep what
    their outside option gives. Never below nothing."""
    return max(0.0, min(posted_rent, crop_margin - outside_option_per_hectare))


def lettable_hectares(held: float, let_out: float, workable: float) -> float:
    """The hectares a holder has to let: what it holds beyond what it has already let out and what its own hands can
    work. An actor with no hands (a state, a firm that hires, a lender) lets everything it holds."""
    return max(0.0, held - let_out - max(0.0, workable))


def wanted_hectares(workable: float, worked: float) -> float:
    """The hectares more a tenant can work beyond the land it already works."""
    return max(0.0, workable - worked)


def hectares_workable(recipe: Recipe, land_per_run: float, held_tools: Mapping[GoodId, float], hours: float) -> float:
    """The hectares `hours` can work with the tools held (its own or rented): a run on a hectare takes the recipe's
    hours, plus the extra hours a short tool asks (tool_fallback.draws: the next tool, then by hand). A tool shortage
    slows the work and never stops it; no tool at all is the by-hand hours."""
    base = math.fsum(recipe.labour_hours.values())
    if land_per_run <= 0.0 or hours <= 0.0:
        return 0.0
    if base <= 0.0:
        return math.inf                                 # a recipe that takes no hours is limited by no hands

    def hours_for(runs: float) -> float:
        _used, extra = tool_fallback.draws(recipe, held_tools, runs)
        return runs * base + math.fsum(extra.values())

    low, high = 0.0, hours / base                     # the tools can only add hours, so `high` runs may be too many
    for _ in range(60):
        middle = (low + high) / 2.0
        if hours_for(middle) <= hours:
            low = middle
        else:
            high = middle
    return low * land_per_run


def match(offers: Sequence[Offer], lots: Sequence[Lot], posted_rent_by_tile: Mapping[TileId, float],
          ask_by_tile: Mapping[TileId, float]) -> List[Lease]:
    """Offers meet lots tile by tile: the tenant that bears the highest rent is served first from the largest-first
    lots, at the tile's ask (the posted rent, cut by tenants' outside option), none where the tenant's ceiling is below
    the ask. Returns the leases."""
    leases: List[Lease] = []
    for tile in sorted({offer.tile for offer in offers} & {lot.tile for lot in lots}):
        rent = min(posted_rent_by_tile.get(tile, 0.0), ask_by_tile.get(tile, posted_rent_by_tile.get(tile, 0.0)))
        wanting = sorted((offer for offer in offers if offer.tile == tile and offer.hectares > 0.0
                          and offer.rent_ceiling >= rent),
                         key=lambda offer: (-offer.rent_ceiling, offer.tenant))
        supply: Dict[AgentId, float] = {lot.lessor: lot.hectares for lot in lots if lot.tile == tile and lot.hectares > 0.0}
        for offer in wanting:
            left = offer.hectares
            for lessor in sorted(supply, key=lambda each: (-supply[each], each)):
                if left <= 1e-12:
                    break
                if lessor == offer.tenant or supply[lessor] <= 1e-12:
                    continue
                taken = min(left, supply[lessor])
                supply[lessor] -= taken
                left -= taken
                leases.append(Lease(offer.tenant, lessor, tile, taken, rent))
    return leases
