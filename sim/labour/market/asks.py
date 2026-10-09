"""What workers ask, as a multiple of the reservation wage, remembered per (area, trade).

A worker sells hours like a seller sells goods. The reservation wage (the family's subsistence per hour plus
pay for the trade's danger) is where the ask starts; the bound under it is the wage floor (the household's
costs less its plot, economy/labour_ask_floor.py): hours employers would not take at
the ask are offered cheaper the next year, by the share of them left unsold, and when employers want more
than is offered the ask is raised by the share of demand left unmet. Nothing here names a trade or an area.
A family with hours nobody buys still eats from its own plot and savings (the economy keeps those hours
back; households_own.py), which is what lets the ask fall.
"""
from sim.constants import declare

from .records import MarketState

ASK_ADJUSTMENT_SHARE_PER_YEAR = declare(
    "ASK_ADJUSTMENT_SHARE_PER_YEAR", 0.15, kind="temporary_heuristic",
    unit="share of the ask moved in a year when every hour is unsold, or demand doubles the supply",
    source=None, confidence="D",
    why="A seller that cannot sell lowers the ask until it sells, and one that sells out raises it until it "
        "does not; how fast follows how long a family can go without a sale (its own plot, savings, kin) "
        "and how well it knows what others are paid, which the model does not carry. The same rate as a "
        "goods seller's markdown (producers.UNSOLD_ASK_MARKDOWN_SHARE).")


def scale_of(state: MarketState, area: str, trade: str) -> float:
    """The ask over the reservation wage; one before any year has moved it."""
    return state.asks.get(area, {}).get(trade, 1.0)


def moved_scale(scale: float, offered: float, wanted: float) -> float:
    """The next ask after a year in which employers wanted `wanted` hours at the wage and `offered` were
    on offer: lowered by the unsold share, raised by the share of demand that went unmet (capped at one)."""
    if offered <= 0.0:
        return scale
    if wanted >= offered:
        return scale * (1.0 + ASK_ADJUSTMENT_SHARE_PER_YEAR * min(1.0, (wanted - offered) / offered))
    return scale * (1.0 - ASK_ADJUSTMENT_SHARE_PER_YEAR * (offered - wanted) / offered)


def record(state: MarketState, area: str, trade: str, offered: float, wanted: float, wage: float,
           reservation: float, lowest: float = 0.0) -> None:
    """Move the ask for the year just cleared. It is never raised past the wage the hours just fetched (a
    seller does not ask more than anyone has been seen to pay) and never lowered past `lowest`, the wage
    floor: what the household costs to keep alive and working, less what its own plot gives."""
    before = scale_of(state, area, trade)
    scale = moved_scale(before, offered, wanted)
    if scale > before and reservation > 0.0:
        # a raise only means something where the ask is what the hours fetched; a wage already well above
        # it says the buyers set the price, and a higher ask would only stick when demand falls
        binding = wage <= reservation * before * (1.0 + ASK_ADJUSTMENT_SHARE_PER_YEAR)
        scale = min(scale, max(before, wage / reservation)) if binding else before
    if reservation > 0.0:
        scale = max(scale, lowest / reservation)
    state.asks.setdefault(area, {})[trade] = scale
