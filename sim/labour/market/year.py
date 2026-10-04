"""One year of the labour market: clear, lose, graduate, enter, switch, migrate (DESIGN.md)."""
import copy
from typing import Tuple

from . import clearing, entrants, expectations, migration, switching, training
from .records import MarketState, YearInputs, YearReport


def run_year(state: MarketState, inputs: YearInputs) -> Tuple[MarketState, YearReport]:
    """The state a year on and what happened in it. The given state is not changed."""
    state = copy.deepcopy(state)
    report = YearReport()
    report.clearings = clearing.clear_all(state, inputs)
    clearings = expectations.index_clearings(report.clearings)
    training.apply_attrition(state, inputs, report)
    training.advance(state, inputs, report)
    entrants.place_entrants(state, inputs, clearings, report)
    switching.switch_trades(state, inputs, clearings, report)
    migration.migrate(state, inputs, clearings, report)
    return state, report
