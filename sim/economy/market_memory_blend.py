"""The price a market remembers after a year, one continuous rule for every market (`goods_remember_kernel.blended` does the same over
columns, bit for bit): the old price moves toward what was paid in proportion to the trade, relaxes toward the making cost when the trade
was thin, and drifts toward the year's quote or cost in proportion to what buyers wanted. No branch on whether a market traded or had a
bid, so a rounding-sized trade or bid moves the price a rounding-sized step."""
from typing import Optional

from sim.constants import declare

from .market_memory_asks import RESUMED_TRADE_MEMORY_SHARE
from .market_memory_offers import NO_OFFER_MEMORY_SHARE, price_after_thin_trade

MEMORY_VOLUME_FLOOR = declare(
    "MEMORY_VOLUME_FLOOR", 1.0, kind="temporary_heuristic",
    unit="units of a good: the smallest volume a market's trade or demand is weighed against in its price memory",
    source=None, confidence="D", retire="Complaints/473-the-agent-economy-spin-up-never-settles-so-the-opening-is-a-point-on-a-cycle.md",
    why="A market with no usual volume, no buyers and no sibling market of its good has no scale of its own, and a rounding-sized trade "
        "weighed against nothing would replace its price whole. Used only when the market's usual volume, what its buyers wanted "
        "and the good's usual volume across its areas are all smaller. A unit of the good is as arbitrary as any scale; a measured "
        "volume of the good's trade would replace it.")


def reference_volume(usual: float, wanted_at_old: float, good_scale: float, representative_share: float) -> float:
    """The volume a market's trade and demand are weighed against: its usual volume, or a representative share of what its buyers wanted at
    the old price, or of the good's mean usual volume over its areas, whichever is largest, and never below `MEMORY_VOLUME_FLOOR`."""
    return max(usual, representative_share * wanted_at_old, representative_share * good_scale, MEMORY_VOLUME_FLOOR)


def blended_price(old: Optional[float], was_quote: bool, quiet_years: int, reference: float, total: float, cleared: Optional[float],
                  wanted: float, demand_led: bool, target: Optional[float], cost: Optional[float]) -> Optional[float]:
    """The price a market remembers: None when it traded nothing and has no target (its planning price is then forgotten), or has nothing at all.

    `total` is the quantity traded at `cleared` (None, with a total of zero, where nothing traded), `wanted` what buyers wanted at the old
    price, `demand_led` whether no offer was left unsold (the target then is the cost or the best bid, and the pull of it is weighed by the
    demand), `target` the quote or making cost the year's markets point to, `cost` the good's making cost. Nothing remembered starts from
    the target, else from the trade."""
    if cleared is None and target is None:
        return None
    base = old if old is not None else (target if target is not None else cleared)
    if base is None:
        return None
    paid = base if cleared is None else cleared
    traded_share = min(1.0, total / reference)
    step = traded_share * (paid - base)
    if old is not None and not was_quote and quiet_years > 0:
        step = RESUMED_TRADE_MEMORY_SHARE * step
    price = base + step
    if old is not None:
        price = price_after_thin_trade(price, cost, total, reference)
    if target is None:
        return price
    demand_share = min(1.0, wanted / reference) if demand_led else 1.0
    return price + (1.0 - traded_share) * demand_share * NO_OFFER_MEMORY_SHARE * (target - price)
