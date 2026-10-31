"""Runs a producer had hands for in a year: the workforce it hired, which input failures do not undo."""
from typing import Mapping, Optional


def staffed_runs(labour_hours_per_run: Mapping[str, float], hours_hired: Mapping[str, float]) -> Optional[float]:
    """Runs the hours hired in the year would staff: the scarcest trade's hours over the hours a run takes of it.
    None for a recipe that hires no hours (nothing was staffed, so no workforce to size a change from)."""
    needs = [(hours_hired.get(trade, 0.0), per_run) for trade, per_run in labour_hours_per_run.items() if per_run > 0.0]
    if not needs:
        return None
    return min(hired / per_run for hired, per_run in needs)


def change_anchor(last_runs: float, staffed: float) -> float:
    """Runs a year's change in output is counted from: the runs worked, or the runs the hired hands could have worked
    when more (a run that failed for want of an input leaves the crew in place)."""
    return max(last_runs, staffed)
