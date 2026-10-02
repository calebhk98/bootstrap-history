"""Wear and loss of coin and metal goods, and the opening money stock."""
from typing import Mapping, Tuple

from sim.constants import declare

from . import types
from .types import AgentId, CurrencySpec, GoodId, GoodsMove, TileId, Transfer

COIN_WEAR_PER_YEAR = declare(
    "COIN_WEAR_PER_YEAR", 0.01, kind="temporary_heuristic", unit="share of coin per year",
    why="abrasion, clipping, hoarding and burial of circulating coin; physical in kind but unsourced. "
        "Hoard-find and coin-weight-loss studies (weight of worn against fresh specimens by age) would fix it.")

METAL_GOODS_LOSS_PER_YEAR = declare(
    "METAL_GOODS_LOSS_PER_YEAR", 0.005, kind="temporary_heuristic", unit="share of stock per year",
    why="plate and ornament lost to wear, theft and burial; unsourced. Shipwreck and burial-site "
        "recovery rates against estimated stock would fix it.")


def yearly_wear(money_holdings_by_agent: Mapping[AgentId, float], spec: CurrencySpec) -> list:
    """Coin and weighed metal wear away; commodity money spoils as a good and fiat does not wear."""
    if spec.regime not in ("struck_coin", "weighed_metal"):
        return []
    return [Transfer(agent, types.EDGE_WEAR, spec.currency_id, amount * COIN_WEAR_PER_YEAR, "coin wear")
            for agent, amount in money_holdings_by_agent.items()
            if amount > 0.0 and not types.is_edge(agent)]


def metal_loss(goods_holdings: Mapping[Tuple[AgentId, GoodId, TileId], float],
               loss_share: float = METAL_GOODS_LOSS_PER_YEAR) -> list:
    """Holdings of metal goods, keyed (agent, good, tile); the caller chooses which goods are metal."""
    return [GoodsMove(agent, types.EDGE_WEAR, good, tile, quantity * loss_share, "metal loss")
            for (agent, good, tile), quantity in goods_holdings.items()
            if quantity > 0.0 and not types.is_edge(agent)]


def opening_money_stock(cash_targets_by_agent: Mapping[AgentId, float]) -> float:
    """The opening stock is derived from what agents want to hold, not authored."""
    return sum(cash_targets_by_agent.values())
