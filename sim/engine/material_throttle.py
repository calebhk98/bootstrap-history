"""The stock accounting of the material throttle, for one material at a time, on figures the caller passes.

A year's unused own production banks into stock once, however often the year is recomputed, because every recompute
works from the stock as it stood when the year's accounting began (`year_opening_record`). Within a year, a
material's need is drawn from the stock and own flow first and the market's standing offer last
(`draw_one_material`); what is not drawn of the physically owned part banks again, and the market's offer never banks.
"""
from typing import Any, Dict, NamedTuple, Optional


class MaterialDraw(NamedTuple):
    """What one material's year did: how much of each need it met, the pace it allows, and the stock it leaves."""
    lab_drawn: float
    industrial_drawn: float
    pace: Optional[float]      # the fraction of planned work this material supports; None when it covers the need
    banked: float              # own production and prior stock left undrawn
    net_draw: float            # drawn beyond what was owned, which is what the market was asked for


def year_opening_record(record: Optional[Dict[str, Any]], year: int, stock: Dict[str, float]) -> Dict[str, Any]:
    """The snapshot of stock the year's accounting works from: the record kept if it is this year's, else a
    new one holding a copy of `stock`."""
    if not record or record.get("year") != year:
        return {"year": year, "tonnes": dict(stock)}
    return record


def draw_one_material(opening_stock: float, own_supply: float, market_tonnes: float, lab_need: float,
                      industrial_need: float, pace_floor: float) -> MaterialDraw:
    """One material's year. `opening_stock` plus `own_supply` is physically owned and can bank; `market_tonnes` is a
    standing offer that can be drawn but is never kept. Laboratory-scale need is met first and never sets the pace;
    an industrial need the owned and offered tonnes cannot cover slows work to their share of it, never below
    `pace_floor`."""
    owned = opening_stock + own_supply
    have = owned + market_tonnes
    lab_drawn = min(lab_need, have)
    have -= lab_drawn
    industrial_drawn, pace = 0.0, None
    if industrial_need > 1e-12:
        if have < industrial_need:
            pace = max(pace_floor, have / industrial_need)
            industrial_drawn = have
        else:
            industrial_drawn = industrial_need
    banked = max(0.0, owned - lab_drawn - industrial_drawn)
    return MaterialDraw(lab_drawn, industrial_drawn, pace, banked, lab_drawn + industrial_drawn - owned)
