"""Wear and loss of coin."""
from typing import Mapping

from sim.constants import declare

from . import types
from .types import AgentId, CurrencySpec, Transfer

COIN_WEAR_PER_YEAR = declare(
    "COIN_WEAR_PER_YEAR", 0.01, kind="temporary_heuristic", unit="share of coin per year",
    why="abrasion, clipping, hoarding and burial of circulating coin; physical in kind but unsourced. "
        "Hoard-find and coin-weight-loss studies (weight of worn against fresh specimens by age) would fix it.")

METAL_GOODS_LOSS_PER_YEAR = declare(
    "METAL_GOODS_LOSS_PER_YEAR", 0.005, kind="temporary_heuristic", unit="share of stock per year",
    why="plate and ornament lost to wear, theft and burial; unsourced. Shipwreck and burial-site "
        "recovery rates against estimated stock would fix it.")


def yearly_wear(money_holdings_by_agent: Mapping[AgentId, float], spec: CurrencySpec) -> list:
    """Struck coin wears; weighed metal is lost as metal (clipping, hoarding, burial) and has no coin to
    wear; commodity money spoils as a good and fiat does not wear."""
    if spec.regime == "struck_coin":
        share, purpose = COIN_WEAR_PER_YEAR, "coin wear"
    elif spec.regime == "weighed_metal":
        share, purpose = METAL_GOODS_LOSS_PER_YEAR, "metal loss"
    else:
        return []
    return [Transfer(agent, types.EDGE_WEAR, spec.currency_id, amount * share, purpose)
            for agent, amount in money_holdings_by_agent.items()
            if amount > 0.0 and not types.is_edge(agent)]
