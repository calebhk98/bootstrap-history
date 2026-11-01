"""How many hours the mint hires and who pays: the staffing is sized to the coin worn away (not to any amount of
money holders might want), and the mint's wage bill is a first charge on the issuer's cash, taken from the goods
the plan would otherwise buy."""
from sim.constants import declare

MINT_STAFFING_MULTIPLE_OF_WEAR = declare(
    "MINT_STAFFING_MULTIPLE_OF_WEAR", 2.0, kind="temporary_heuristic",
    unit="multiple of the coin worn away in a year that the mint hires hands to strike",
    source=None, confidence="D",
    retire="Complaints/473-the-agent-economy-spin-up-never-settles-so-the-opening-is-a-point-on-a-cycle.md",
    why="Holders' wish for more money (cash targets over the stock) can reach many times the stock when prices rise; "
        "hands hired for that much would be paid for striking metal that no market holds. The mint staffs to replace wear "
        "and a catch-up of the same size; the metal on offer at the mint price should size it.")


def staffed_money(monetisation: float, worn_money: float) -> float:
    """Money the mint hires hands to strike in a year: what holders want added, up to a multiple of the wear."""
    return max(0.0, min(monetisation, MINT_STAFFING_MULTIPLE_OF_WEAR * worn_money))


def goods_budget_cut(balance: float, wage_budget: float, goods_budget: float, funded: float) -> float:
    """How much of the plan's goods line the mint's wage funding took: the part of `funded` beyond the cash the plan
    leaves unplanned (cash in hand over both lines), at most the whole goods line."""
    unplanned = max(0.0, balance - wage_budget - goods_budget)
    return min(max(0.0, goods_budget), max(0.0, funded - unplanned))


MINT_LABOUR_SHARE_OF_COIN_VALUE = declare(
    "MINT_LABOUR_SHARE_OF_COIN_VALUE", 0.05, kind="temporary_heuristic",
    unit="share of the coin's metal value the mint will pay in wages to strike it",
    source=None, confidence="D",
    retire="Complaints/473-the-agent-economy-spin-up-never-settles-so-the-opening-is-a-point-on-a-cycle.md",
    why="A mint that bids only a multiple of last year's wage is outbid for skilled hands whenever their wage jumps, and "
        "then strikes nothing however much metal is on offer. What striking is worth to the issuer (money kept in being "
        "against wear) is not derived; a share of the coin's metal value stands for it.")


def hour_value(parity: float, hours_per_fine_kilogram: float) -> float:
    """The most the mint pays per hour of any trade: the share of a kilogram's coin value it will spend on the
    hours that strike it, over those hours."""
    return MINT_LABOUR_SHARE_OF_COIN_VALUE * parity / hours_per_fine_kilogram if hours_per_fine_kilogram > 0.0 else 0.0
