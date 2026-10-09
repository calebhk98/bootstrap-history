"""The labour a mint spends striking coin. The minting recipe (a production entry the coin standard names)
gives hours per kilogram of coin; the standard's fineness turns that into hours per kilogram of fine
metal struck. The issuer funds a mint account that bids for the hours before the year's labour market
clears; the hours hired set how much metal the mint can strike; what is not spent goes back to the issuer.

The alloy metal and fuel the recipe lists are not bought (MINT_ALLOY_AND_FUEL_NOT_BOUGHT)."""
import math
from typing import Dict, List, Mapping

from sim.constants import declare

from . import currency
from .setup import labour_area
from .state_budget import STATE_WAGE_CEILING_MULTIPLE
from .types import LabourBid, Transfer

MINT_ALLOY_AND_FUEL_NOT_BOUGHT = declare(
    "MINT_ALLOY_AND_FUEL_NOT_BOUGHT", 0.0, kind="temporary_heuristic",
    unit="share of the recipe's alloy and fuel inputs the mint buys",
    source=None, confidence="D",
    why="The mint pays the recipe's labour and takes in the fine metal, but does not yet buy the base "
        "metal it alloys or the charcoal it melts with: they are a small part of the coin's value. "
        "Bid for them in the goods markets like any buyer.")


def mint_agent(setup) -> str:
    return "mint:" + setup.civ_id


def hours_per_fine_kilogram(recipe, spec) -> Dict[str, float]:
    """Hours of each trade to strike one kilogram of fine metal into coin of the standard's fineness."""
    coin_kilograms = recipe.outputs[recipe.recipe_id]
    return {trade: hours / coin_kilograms / spec.fineness for trade, hours in recipe.labour_hours.items()}


def capacity_hours(setup, spec, capacity_fine_kilograms: float) -> Dict[str, float]:
    """Hours by trade the mint needs to strike `capacity_fine_kilograms` in a year; none where it does not strike."""
    if not _striking(setup, spec) or capacity_fine_kilograms <= 0.0:
        return {}
    return {trade: capacity_fine_kilograms * per_kilogram
            for trade, per_kilogram in hours_per_fine_kilogram(setup.mint_recipe, spec).items()}


def _striking(setup, spec) -> bool:
    return (getattr(setup, "mint_recipe", None) is not None and currency.has_mint(spec)
            and spec.backing_per_unit > 0.0)


def staff(setup, record, view, labour_bids: List[LabourBid], capacity_fine_kilograms: float) -> None:
    """Bid for the hours the mint needs to strike `capacity_fine_kilograms` this year, at the capital,
    and fund the mint account from the issuer's cash for the wages it bids."""
    spec = record.currency
    if not _striking(setup, spec) or capacity_fine_kilograms <= 0.0:
        return
    agent, area = mint_agent(setup), labour_area(setup.capital_tile)
    level = view.basket_price_level(setup.currency_id)
    bids = []
    for trade, per_kilogram in sorted(hours_per_fine_kilogram(setup.mint_recipe, spec).items()):
        wage = view.wage(trade, area) or setup.opening_wages.get(trade, 0.0) * level
        if wage > 0.0:
            bids.append(LabourBid(agent, trade, area, capacity_fine_kilograms * per_kilogram,
                                  wage * STATE_WAGE_CEILING_MULTIPLE))
    wage_bill = math.fsum(bid.hours * bid.maximum_wage for bid in bids)
    funded = min(wage_bill, record.book.balance(setup.state_agent, setup.currency_id))
    if funded > 0.0:
        record.book.transfer(Transfer(setup.state_agent, agent, setup.currency_id, funded, "mint wages funded"))
    labour_bids.extend(bids)


def strike_limit_fine_kilograms(setup, spec, hours_hired: Mapping[str, float]) -> float:
    """Most fine metal the hours hired let the mint strike; unlimited where no recipe is stated."""
    if not _striking(setup, spec):
        return math.inf
    return min((hours_hired.get(trade, 0.0) / per_kilogram
                for trade, per_kilogram in hours_per_fine_kilogram(setup.mint_recipe, spec).items()),
               default=math.inf)


def close_year(setup, record) -> None:
    """Wage money the mint did not spend goes back to the issuer."""
    agent = mint_agent(setup)
    left = record.book.balance(agent, setup.currency_id)
    if left > 0.0:
        record.book.transfer(Transfer(agent, setup.state_agent, setup.currency_id, left, "mint wages returned"))
