"""The tools households' own plots wear, at the opening.

A year's household bids for the stock of tools its plot hours keep in use, less what it holds (`tool_wear.tool_bids`),
and works its plot at the recipe's hours only with the tools in hand (`plot_means`). The opening grows the plots at
those hours (`opening_own.OwnPlots.grow`), so it gives each cohort that stock and adds the stock's yearly wear to its
tile's final demand, which sizes the tools' makers. A cohort opened with none bids for the whole stock in the first
year, several years of the makers' output, and takes the tools the farms were sized on."""
from typing import Dict, List, Mapping

from .tool_wear import tool_stock_wanted
from .types import EDGE_PRODUCTION, AgentId, GoodId, GoodSpec, GoodsMove, Recipe, TileId


def stock_by_good(hours_by_recipe: Mapping[str, float], recipes: Mapping[str, Recipe],
                  specs: Mapping[GoodId, GoodSpec]) -> Dict[GoodId, float]:
    """The stock of each tool a cohort's plot hours keep in use (`tool_wear.tool_stock_wanted`, over its recipes)."""
    stock: Dict[GoodId, float] = {}
    for recipe_id, hours in sorted(hours_by_recipe.items()):
        for good, quantity in tool_stock_wanted(recipes[recipe_id], hours, specs).items():
            stock[good] = stock.get(good, 0.0) + quantity
    return stock


def yearly_wear(stock: Mapping[GoodId, float], specs: Mapping[GoodId, GoodSpec]) -> Dict[GoodId, float]:
    """What a year wears of a stock held: the part `tool_wear.tool_bids` replaces."""
    return {good: quantity * min(1.0, 1.0 / specs[good].service_life_years) for good, quantity in stock.items()}


def _priced_stock(hours_by_recipe, recipes, specs, priced_goods) -> Dict[GoodId, float]:
    """`stock_by_good` of the tools with an opening price: a household bids for no other."""
    return {good: quantity for good, quantity in stock_by_good(hours_by_recipe, recipes, specs).items()
            if priced_goods.get(good, 0.0) > 0.0 and quantity > 0.0}


def add_wear(final_by_tile: Dict[TileId, Dict[GoodId, float]], tile_of_cohort: Mapping[AgentId, TileId],
             hours_by_cohort: Mapping[AgentId, Mapping[str, float]], recipes: Mapping[str, Recipe],
             specs: Mapping[GoodId, GoodSpec], priced_goods: Mapping[GoodId, float]) -> None:
    """Add to each tile's final demand, in place, the yearly wear of its cohorts' plot tools."""
    for agent_id in sorted(hours_by_cohort):
        stock = _priced_stock(hours_by_cohort[agent_id], recipes, specs, priced_goods)
        demand = final_by_tile.setdefault(tile_of_cohort[agent_id], {}) if stock else {}
        for good, quantity in sorted(yearly_wear(stock, specs).items()):
            demand[good] = demand.get(good, 0.0) + quantity


def seed_moves(tile_of_cohort: Mapping[AgentId, TileId], hours_by_cohort: Mapping[AgentId, Mapping[str, float]],
               recipes: Mapping[str, Recipe], specs: Mapping[GoodId, GoodSpec],
               priced_goods: Mapping[GoodId, float]) -> List[GoodsMove]:
    """The moves that give each cohort the tool stock its plot hours keep in use, in cohort and good order."""
    return [GoodsMove(EDGE_PRODUCTION, agent_id, good, tile_of_cohort[agent_id], quantity, "opening stock of plot tools")
            for agent_id in sorted(hours_by_cohort)
            for good, quantity in sorted(_priced_stock(hours_by_cohort[agent_id], recipes, specs, priced_goods).items())]
