"""Households and cleared ground in the year (Complaint 538): a clearer's owner farms what its floors need of the
clearer's stock first, a cohort with hours left over bids for ground it could farm, and the hectares it bought
become its title. The rules are in land_bid.py."""
import dataclasses
from typing import Dict, List, Mapping

from . import land_bid, sites, titles_ground, titles_value, titles_worked
from .households_own import Option, plot_hectares
from .protocols import AgentOrders
from .setup import labour_area
from .types import EDGE_CONSUMPTION, Bid, GoodsMove


def best_margin(setup, view, cohort, options: Mapping[str, List[Option]], tile_spec):
    """(crop margin per hectare, hours a hectare takes, recipe id) of the recipe, of those the cohort grows its needs
    with, that nets most at the prices and the wage it sees. The margin is net of the wage, so a rising wage lowers it."""
    wage = view.wage(setup.servant_trade, labour_area(cohort.tile)) or 0.0
    rows = []
    for recipe_id in sorted({rows_of_need[0][1] for rows_of_need in options.values() if rows_of_need}):   # the recipe it grows each need with
        recipe, land = setup.recipes[recipe_id], setup.land_per_run.get(recipe_id, 0.0)
        if not recipe.climate_classes or not sites.climate_allows(recipe, tile_spec):    # a crop grows in a climate; a mine's ground is its deposit
            continue
        prices = {good: view.price(good, view.area_of(good, cohort.tile)) or 0.0 for good in recipe.outputs}
        rows.append((land_bid.crop_margin_per_hectare(recipe, land, tile_spec.fertility, prices, wage),
                     land_bid.hours_per_hectare(recipe, land), recipe_id))
    return max(rows, default=(0.0, 0.0, ""))


def _best_earning(setup, view, cohort, options: Mapping[str, List[Option]], tile_spec, rent: float):
    """(earning per hectare, hours a hectare takes): the best crop margin, with the tile's rent as the floor."""
    margin, hours, _recipe_id = best_margin(setup, view, cohort, options, tile_spec)
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
    """Every cohort's ground bought this year becomes its title: new arable land on its tile (land_bid.take_up),
    and the stock is consumed. Returns hectares titled by cohort."""
    titled: Dict[str, float] = {}
    for good in land_bid.land_goods(setup.specs, setup.recipes):
        for cohort in sorted(record.cohorts.values(), key=lambda each: each.agent_id):
            bought = record.book.stock(cohort.agent_id, good, cohort.tile)
            tile = setup.tiles.get(cohort.tile)
            if bought <= 0.0 or tile is None:
                continue
            added = land_bid.take_up(record, cohort.agent_id, cohort.tile, bought,
                                     titles_ground.arable_hectares(record, cohort.tile, tile))
            if added > 0.0:
                record.book.move_many([GoodsMove(cohort.agent_id, EDGE_CONSUMPTION, good, cohort.tile, added,
                                                 "ground taken up as a title")])
                titled[cohort.agent_id] = titled.get(cohort.agent_id, 0.0) + added
    return titled


def take_up_own(setup, record, options: Mapping[str, List[Option]]) -> Dict[str, float]:
    """A cohort that owns a clearer farms what it needs of the clearer's stock itself before anything is sold: the
    hectares its own plots need to grow its floors beyond the land it holds (land_bid.own_use) become its title.
    Returns hectares kept by cohort."""
    kept: Dict[str, float] = {}
    for good in land_bid.land_goods(setup.specs, setup.recipes):
        for producer_id, producer in sorted(record.producers.items()):
            owner, tile = record.cohorts.get(producer.owner), setup.tiles.get(producer.tile)
            if owner is None or tile is None or good not in setup.recipes[producer.recipe_id].outputs:
                continue
            arable = titles_ground.arable_hectares(record, producer.tile, tile)
            floors = {need.need_id: need.subsistence_per_person * owner.people for need in setup.basket_for(owner.tile).needs}
            needed = plot_hectares(floors, options, setup.recipes, setup.land_per_run, tile.fertility)
            held = titles_worked.worked_share(record, owner.tile, owner.agent_id) * arable
            taken = land_bid.own_use(record.book.stock(producer_id, good, producer.tile), needed, held)
            if titles_ground.add_ground(record, producer.tile, owner.agent_id, taken, arable) > 0.0:
                record.book.move_many([GoodsMove(producer_id, EDGE_CONSUMPTION, good, producer.tile, taken,
                                                 "ground kept for its owner's own plots")])
                kept[owner.agent_id] = kept.get(owner.agent_id, 0.0) + taken
    return kept
