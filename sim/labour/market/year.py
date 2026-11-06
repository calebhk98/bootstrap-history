"""One year of the labour market: clear, graduate, switch, migrate, form empty trades (DESIGN.md)."""
from typing import Tuple

from . import clearing, expectations, formation, migration, switching, training
from .records import MarketState, YearInputs, YearReport, copy_state


def run_year(state: MarketState, inputs: YearInputs, owned: bool = False) -> Tuple[MarketState, YearReport]:
    """The state a year on and what happened in it. The given state is not changed, unless the caller
    hands over a copy of its own (`owned`) that nobody else holds."""
    if not owned:
        state = copy_state(state)
    report = YearReport()
    report.clearings = clearing.clear_all(state, inputs)
    clearings = expectations.index_clearings(report.clearings)
    training.advance(state, inputs, report)
    switching.switch_trades(state, inputs, clearings, report)
    migration.migrate(state, inputs, clearings, report)
    formation.form_trades(state, inputs, clearings, report)
    return state, report
