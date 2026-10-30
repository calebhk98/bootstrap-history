"""What workers ask, as a multiple of the reservation wage, remembered per (area, trade).

A worker sells hours like a seller sells goods. The reservation wage (the family's subsistence per hour plus
pay for the trade's danger) is where the ask starts; the bound under it is the wage floor (what an hour is worth on the
household's own plot, economy/labour_ask_floor.py): hours employers would not take at
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
        "and how well it knows what others are paid, which the model does not carry. A goods seller's "
        "unsold stock is marked down inside the year instead (economy/unsold_search.py).")

SEARCH_ROUNDS_PER_YEAR = declare(
    "SEARCH_ROUNDS_PER_YEAR", 12, kind="temporary_heuristic", unit="rounds of search and wage revision per year",
    source=None, confidence="D",
    retire="Complaints/608: a wage method driven by the market\'s own state replaces this fixed fraction",
    why="Eurace's labour loop (Labour/Firm_Employer_Functions.c, Firm_update_wage_offer; Household_Employee_Functions.c, "
        "Household_read_application_rejection_update_wage_reservation) revises offers and reservations once a round "
        "and its raise runs once a month; the yearly step compounds that many rounds. Not fitted.")

RESERVATION_CUT_PER_ROUND = declare(
    "RESERVATION_CUT_PER_ROUND", 0.02, kind="temporary_heuristic", unit="share of the ask cut per failed search round",
    source=None, confidence="D",
    retire="Complaints/608: a wage method driven by the market\'s own state replaces this fixed fraction",
    why="Eurace's WAGE_RESERVATION_UPDATE (default 0.02 in Labour/model.xml): an unemployed household cuts its "
        "reservation wage by this share each round it stays unemployed, never under its floor (there the "
        "benefit share of last pay; here the wage floor). How fast a family gives ground is not fitted.")


def scale_of(state: MarketState, area: str, trade: str) -> float:
    """The ask over the reservation wage; one before any year has moved it."""
    return state.asks.get(area, {}).get(trade, 1.0)


def moved_scale(scale: float, offered: float, wanted: float) -> float:
    """The next ask after a year in which employers wanted `wanted` hours at the wage and `offered` were
    on offer: lowered by the unsold share, raised by the share of demand that went unmet (capped at one).
    The cut follows Household_read_application_rejection_update_wage_reservation (Eurace, Labour/
    Household_Employee_Functions.c): each round without work takes `RESERVATION_CUT_PER_ROUND` off the ask, and only
    the unsold share of the hours is still searching, so the ask falls by that share of the compounded cut."""
    if offered <= 0.0:
        return scale
    if wanted >= offered:
        return scale * (1.0 + ASK_ADJUSTMENT_SHARE_PER_YEAR * min(1.0, (wanted - offered) / offered))
    year_cut = 1.0 - (1.0 - RESERVATION_CUT_PER_ROUND) ** SEARCH_ROUNDS_PER_YEAR
    return scale * (1.0 - year_cut * (offered - wanted) / offered)


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
