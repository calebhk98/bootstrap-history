"""The labour a state's masonry works take, read from a laid-wall service recipe.

A work is counted in square metres of public building (`sim/agents/state_works.py`); a square metre holds a volume of laid
wall, and the recipe for a cubic metre of that wall says the hours each trade spends on it. Plain functions; the service
named in `data/world/state_masonry.json` is data, so a mod or a scenario can name another."""
import json
import os
from typing import Dict, Mapping

_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                     "data", "world", "state_masonry.json")


def service_material() -> str:
    """The production entry whose labour the state's masonry is counted in."""
    with open(_FILE, encoding="utf-8") as handle:
        return str(json.load(handle)["service"])


def person_years_per_square_metre(hours_per_cubic_metre: Mapping[str, float], cubic_metres_per_square_metre: float,
                                  hours_per_person_year: float) -> Dict[str, float]:
    """Person-years of each trade to lay one square metre of public building: the recipe's hours per cubic metre of wall,
    times the wall a square metre holds, over the hours in a working year."""
    return {trade: hours * cubic_metres_per_square_metre / hours_per_person_year
            for trade, hours in sorted(hours_per_cubic_metre.items()) if hours > 0.0}


def fold_absent_trades(person_years: Mapping[str, float], exists: Mapping[str, bool], fallback_trade: str) -> Dict[str, float]:
    """The same labour with each trade the country has no one in (`exists` false) done by `fallback_trade` instead."""
    folded: Dict[str, float] = {}
    for trade, years in person_years.items():
        target = trade if exists.get(trade, False) else fallback_trade
        folded[target] = folded.get(target, 0.0) + years
    return folded
