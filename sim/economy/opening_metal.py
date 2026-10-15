"""The metal the opening's money loses each year, as a demand the opening sizes producers to.

Money made of a metal wears (struck coin), is lost (weighed metal) or spoils (a commodity). A stock that is to
last is replaced by new metal at the rate it is lost, so the producers of the backing good have a final
demand that no household bids: the mint's. The opening sizes it from the money stock the first pass left, so
the supply chain behind the coin (ore, smelting, fuel) exists from the first year at the scale the money needs
and the stock does not drain in the years it would take entry to build one.
"""
from . import mint
from .metal_stock import COIN_WEAR_PER_YEAR, METAL_GOODS_LOSS_PER_YEAR


def yearly_loss_share(setup, spec) -> float:
    """Share of the money in circulation that the backing good loses in a year, by the regime's own loss."""
    if spec.regime == "struck_coin":
        return COIN_WEAR_PER_YEAR
    if spec.regime == "weighed_metal":
        return METAL_GOODS_LOSS_PER_YEAR
    if spec.regime == "commodity":
        return mint.loss_share(setup, spec)
    return 0.0


def yearly_replacement(setup, record) -> float:
    """Units of the backing good the money in `record` loses in a year (zero for fiat money)."""
    spec = record.currency
    if spec.backing_good is None or spec.backing_per_unit <= 0.0:
        return 0.0
    return yearly_loss_share(setup, spec) * record.book.money_supply(spec.currency_id) * spec.backing_per_unit
