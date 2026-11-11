"""The year's carriage hours by carrier trade (Complaints 552, 613): the hours merchants bid for, the hours the labour market
hired them, and the carriage money paid through the fallback that pays a fee to a household of the tile the goods leave
instead of to hired crew. Plain functions over the figures the year already holds."""
from dataclasses import dataclass
from typing import Dict, Iterable, Mapping, Tuple

from .merchants import EDGE_CARRIAGE


@dataclass(frozen=True)
class TradeHours:
    trade: str
    demanded: float      # crew hours the merchants' bids asked for
    hired: float         # crew hours the labour market sold them


@dataclass(frozen=True)
class FeeSplit:
    to_households: float     # carriage fees paid to a household of the source tile (the fallback)
    to_edge: float           # carriage fees paid to the edge account, where the tile has no household


@dataclass(frozen=True)
class CarriageReport:
    trades: Tuple[TradeHours, ...]
    fees: FeeSplit


def demanded_by_trade(bid_figures: Iterable[Tuple[str, str, str, float, float]]) -> Dict[str, float]:
    """{trade: hours} of the merchants' bids, `carriage_hours.bid_figures` rows being (employer, trade, area, hours, maximum wage)."""
    demanded: Dict[str, float] = {}
    for _employer, trade, _area, hours, _wage in bid_figures:
        demanded[trade] = demanded.get(trade, 0.0) + hours
    return demanded


def hired_by_trade(crew_hours_bought: Mapping[str, Mapping[Tuple[str, str], float]]) -> Dict[str, float]:
    """{trade: hours} of `YearLedger.crew_hours_bought` ({merchant: {(trade, area): hours}}), summed over merchants and areas."""
    hired: Dict[str, float] = {}
    for by_market in crew_hours_bought.values():
        for (trade, _area), hours in by_market.items():
            hired[trade] = hired.get(trade, 0.0) + hours
    return hired


def fee_split(fees: Iterable) -> FeeSplit:
    """The carriage fees (transfers with `payee` and `amount`) split by whether the edge account or a household took them."""
    households = edge = 0.0
    for fee in fees:
        if fee.payee == EDGE_CARRIAGE:
            edge += fee.amount
        else:
            households += fee.amount
    return FeeSplit(households, edge)


def build(bid_figures, crew_hours_bought, fees) -> CarriageReport:
    """The report over a year's bids, hours bought and fees; every trade bid for or hired appears, in name order."""
    demanded, hired = demanded_by_trade(bid_figures), hired_by_trade(crew_hours_bought)
    return CarriageReport(tuple(TradeHours(trade, demanded.get(trade, 0.0), hired.get(trade, 0.0))
                                for trade in sorted(set(demanded) | set(hired))), fee_split(fees))


def format_report(report: CarriageReport) -> str:
    """The report as text: one line per carrier trade, then the fallback fee."""
    lines = ["  carriage hours by carrier trade (demanded by merchants, hired at the labour clearing)"]
    for row in report.trades:
        share = "-" if row.demanded <= 0.0 else "%.3f" % (row.hired / row.demanded)
        lines.append("    %-20s demanded %12.5g  hired %12.5g  hired share %6s" % (row.trade, row.demanded, row.hired, share))
    if not report.trades:
        lines.append("    no carriage hours bid or hired")
    lines.append("  carriage fee paid to a household of the source tile (fallback) %.5g, to the edge account %.5g" % (
        report.fees.to_households, report.fees.to_edge))
    return "\n".join(lines)
