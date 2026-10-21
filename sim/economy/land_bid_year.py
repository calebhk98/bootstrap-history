"""Households and cleared ground in the year (Complaint 538): a cohort with hours left over bids for ground it could
farm, and the hectares it bought become its title. The rules are in land_bid.py."""
import dataclasses
from typing import Dict, List, Mapping

from . import land_bid, sites, titles_value
from .households_own import Option
from .protocols import AgentOrders
from .setup import labour_area
from .types import EDGE_CONSUMPTION, Bid, GoodsMove


def _best_earning(setup, view, cohort, options: Mapping[str, List[Option]], tile_spec, rent: float):
    """(earning per hectare, hours a hectare takes) for the recipe, of those it grows its needs with, that nets most, at the prices
    and the wage it sees; the tile's rent is the floor on the earning."""
    wage = view.wage(setup.servant_trade, labour_area(cohort.tile)) or 0.0
    rows = []
    for recipe_id in sorted({rows_of_need[0][1] for rows_of_need in options.values() if rows_of_need}):   # the recipe it grows each need with
        recipe, land = setup.recipes[recipe_id], setup.land_per_run.get(recipe_id, 0.0)
        if not recipe.climate_classes or not sites.climate_allows(recipe, tile_spec):    # a crop grows in a climate; a mine's ground is its deposit
            continue
        prices = {good: view.price(good, view.area_of(good, cohort.tile)) or 0.0 for good in recipe.outputs}
        rows.append((land_bid.crop_margin_per_hectare(recipe, land, tile_spec.fertility, prices, wage),
                     land_bid.hours_per_hectare(recipe, land)))
    margin, hours = max(rows, default=(0.0, 0.0))
    return land_bid.earning_per_hectare(margin, rent), hours


def land_bids(setup, record, view, cohort, options, spare_hours: float, cash: float) -> List[Bid]:
    """The cohort's bids for ground on its tile: for the hectares its spare hours can work, at no more than the
    earning capitalised. None for a cohort that owns the land that is sold (it would buy from itself)."""
    tile = setup.tiles.get(cohort.tile)
    if tile is None or spare_hours <= 0.0 or cash <= 0.0:
        return []
    bids = []
    for good in land_bid.land_goods(setup.specs, setup.recipes):
        sellers = land_bid.owners_of_sellers(record, setup.recipes, good, cohort.tile)
        if not sellers or cohort.agent_id in sellers:
            continue
        area = view.area_of(good, cohort.tile)
        rate = view.interest_rate(view.currency_of(area))
        earning, hours = _best_earning(setup, view, cohort, options, tile, record.land_rent.get(cohort.tile, 0.0))
        bid = land_bid.hectare_bid(cohort.agent_id, good, area, cohort.tile, earning, view.price(good, area),
                                   titles_value.capitalising_rate(rate, setup.opening_rate),
                                   land_bid.workable_hectares(spare_hours, hours), cash)
        if bid is not None:
            bids.append(bid)
    return bids


def with_land_bids(orders: AgentOrders, bids: List[Bid]) -> AgentOrders:
    """The orders with the land bids added and the budget they set aside taken off the savings on offer."""
    if not bids:
        return orders
    reserved = sum(bid.budget for bid in bids)
    funds = []
    for offer in orders.funds_offers:
        taken = min(offer.amount, reserved)
        reserved -= taken
        if offer.amount - taken > 0.0:
            funds.append(dataclasses.replace(offer, amount=offer.amount - taken))
    return dataclasses.replace(orders, bids=tuple(orders.bids) + tuple(bids), funds_offers=tuple(funds))


def take_up_bought(setup, record) -> Dict[str, float]:
    """Every cohort's ground bought this year becomes its title, passed from the owner of the seller; what the
    seller's owner could not give stays in the cohort's stock. Returns hectares titled by cohort."""
    titled: Dict[str, float] = {}
    for good in land_bid.land_goods(setup.specs, setup.recipes):
        for cohort in sorted(record.cohorts.values(), key=lambda each: each.agent_id):
            bought = record.book.stock(cohort.agent_id, good, cohort.tile)
            tile = setup.tiles.get(cohort.tile)
            if bought <= 0.0 or tile is None:
                continue
            for giver in land_bid.owners_of_sellers(record, setup.recipes, good, cohort.tile):
                moved = land_bid.take_up(record, giver, cohort.agent_id, cohort.tile, bought, tile.cropland_hectares)
                if moved > 0.0:
                    record.book.move_many([GoodsMove(cohort.agent_id, EDGE_CONSUMPTION, good, cohort.tile, moved,
                                                     "ground taken up as a title")])
                    titled[cohort.agent_id] = titled.get(cohort.agent_id, 0.0) + moved
                    bought -= moved
                if bought <= 0.0:
                    break
    return titled
