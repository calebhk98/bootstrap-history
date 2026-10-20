"""A bank's spread over what it pays its depositors: its own loss record plus a widening as its capital thins.

The shape follows the stock-flow-consistent banking models (Caiani et al. 2016 tie the lending rate to the capital
ratio; Lavoie raises the spread after defaults). The loss term is read from the bank's record; the size of the
capital term is not derived.
"""
from sim.constants import declare

from . import lender_ask

BANK_SPREAD_AT_NO_CAPITAL = declare(
    "BANK_SPREAD_AT_NO_CAPITAL", 0.05, kind="temporary_heuristic",
    unit="rate added over the depositors' rate when the bank's capital is gone", source=None, confidence="D",
    retire="Complaints/106: a bank sizes its spread to the losses its capital can bear",
    why="How far a bank widens its spread as its capital falls short of the share it keeps behind its loans. "
        "The direction follows the capital-ratio models (Caiani et al. 2016); the size is not derived.")


def capital_shortfall_share(capital: float, loans_out: float, target_capital_share: float) -> float:
    """Zero at or above the capital the bank keeps behind its loans, one when its capital is gone."""
    if loans_out <= 0.0 or target_capital_share <= 0.0:
        return 0.0
    ratio = capital / loans_out
    return min(1.0, max(0.0, (target_capital_share - ratio) / target_capital_share))


def spread(remembered_loss_rate: float, loans_out: float, capital: float, target_capital_share: float) -> float:
    """What the bank adds to its depositors' rate: the loss rate on its book plus the capital term."""
    return (lender_ask.loss_rate(remembered_loss_rate)
            + BANK_SPREAD_AT_NO_CAPITAL * capital_shortfall_share(capital, loans_out, target_capital_share))
