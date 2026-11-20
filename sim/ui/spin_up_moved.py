"""What the spin-up's years moved the opening away from: for the figures the opening sizes, the value in the first
year and in the last, and the last over the first. Printed after the settle gaps by `spin-up-trace --civ <id> --stages`.
An opening the years leave where it is shows every figure's last over first near one."""
from typing import Callable, List, Optional, Sequence, Tuple


def _over(top: str, bottom: str) -> Callable[[dict], Optional[float]]:
    def figure(row: dict) -> Optional[float]:
        above, below = row.get(top), row.get(bottom)
        if above is None or below is None or not below:
            return None
        return above / below
    return figure


def _hired_share(row: dict) -> Optional[float]:
    hired, idle = row.get("hired_hours"), row.get("idle_hours")
    if hired is None or idle is None or not hired + idle > 0.0:
        return None
    return hired / (hired + idle)


def _column(name: str) -> Callable[[dict], Optional[float]]:
    return lambda row: row.get(name)


FIGURES: Tuple[Tuple[str, Callable[[dict], Optional[float]]], ...] = (
    ("hours hired over hours offered", _hired_share),
    ("wage over price level", _over("wage", "price_level")),
    ("hours hired", _column("hired_hours")),
    ("real output", _column("real_output")),
    ("price level", _column("price_level")),
    ("wage", _column("wage")),
    ("rate", _column("rate")),
    ("money supply", _column("money_supply")),
    ("coin of households", _column("money_households")),
    ("coin of producers", _column("money_producers")),
    ("coin of merchants", _column("money_merchants")),
    ("inventory value over real output", _over("inventory_value", "real_output")),
    ("unmet need over food need", _over("unmet_need", "food_need")),
)


def moved(rows: Sequence[dict]) -> List[Tuple[str, Optional[float], Optional[float], Optional[float]]]:
    """(figure, its value in the first row, in the last row, the last over the first) for each of `FIGURES`; a value a
    row does not carry is None, and so is a ratio whose first value is none or nothing."""
    if not rows:
        return []
    first, last = rows[0], rows[-1]
    table = []
    for name, figure in FIGURES:
        before, after = figure(first), figure(last)
        ratio = None if before is None or after is None or not before else after / before
        table.append((name, before, after, ratio))
    return table


def _shown(value: Optional[float]) -> str:
    return "-" if value is None else "%.4g" % value


def format_moved(table: Sequence[Tuple[str, Optional[float], Optional[float], Optional[float]]]) -> str:
    """The table as lines: figure, first year, last year, last over first."""
    lines = ["what the years moved (first year, last year, last over first):"]
    lines.extend("  %-34s %12s %12s %8s" % (name, _shown(before), _shown(after), _shown(ratio)) for name, before, after, ratio in table)
    return "\n".join(lines)
