"""Does a controlled run settle? Bounded year-over-year change and no monotone drift in the price level, the
unskilled wage, the money stock and the interest rate over the last years of a run (Complaints 473 and 554).
Reads a list of yearly rows; changes nothing."""
import math
from dataclasses import dataclass
from typing import List, Mapping, Sequence

from sim.constants import declare

SETTLING_WINDOW_YEARS = declare(
    "SETTLING_WINDOW_YEARS", 20, kind="temporary_heuristic", unit="years",
    why="the last years of a controlled run over which drift is judged; long enough to span a cycle of a few "
        "years, short enough to leave the warm-up out", retire="Complaints/473")
MAX_LOG_CHANGE_PER_YEAR = declare(
    "MAX_LOG_CHANGE_PER_YEAR", 0.15, kind="temporary_heuristic", unit="natural log of year over year ratio",
    why="a settled economy with no shocks moves a price, wage or money stock by well under this in a year; "
        "unsourced, set to flag a swing, not to tune a result", retire="Complaints/473")
MAX_LOG_TREND_PER_YEAR = declare(
    "MAX_LOG_TREND_PER_YEAR", 0.01, kind="temporary_heuristic", unit="natural log per year",
    why="slope of the log series over the window above which a series is drifting rather than resting",
    retire="Complaints/473")
MAX_RATE_CHANGE_PER_YEAR = declare(
    "MAX_RATE_CHANGE_PER_YEAR", 0.02, kind="temporary_heuristic", unit="interest rate, absolute, per year",
    why="largest year over year move of the interest rate in a run with no shocks; unsourced",
    retire="Complaints/473")
MAX_RATE_TREND_PER_YEAR = declare(
    "MAX_RATE_TREND_PER_YEAR", 0.002, kind="temporary_heuristic", unit="interest rate, absolute, per year",
    why="slope of the interest rate over the window above which it is drifting; unsourced",
    retire="Complaints/473")
MONOTONE_SHARE = declare(
    "MONOTONE_SHARE", 0.7, kind="temporary_heuristic", unit="share of the window's years",
    why="a trend only counts as drift when at least this share of the year over year moves go the same way as "
        "the net move; a cycle around a level fails it", retire="Complaints/473")

# (row key, whether the change is judged as a ratio (log) or as a difference)
SERIES = (("price_level", True), ("wage", True), ("money_supply", True), ("rate", False))


@dataclass(frozen=True)
class SeriesSettling:
    name: str
    largest_step: float      # largest absolute year over year change in the window (log or difference)
    trend_per_year: float    # least-squares slope of the series (log or level) against the year, over the window
    monotone_share: float    # share of the window's moves that go the way of the net move
    step_bound: float
    trend_bound: float

    @property
    def steps_bounded(self) -> bool:
        return self.largest_step <= self.step_bound

    @property
    def drifting(self) -> bool:
        return abs(self.trend_per_year) > self.trend_bound and self.monotone_share >= MONOTONE_SHARE

    @property
    def settled(self) -> bool:
        return self.steps_bounded and not self.drifting


def _transform(values: Sequence[float], as_ratio: bool) -> List[float]:
    if not as_ratio:
        return list(values)
    return [math.log(value) if value > 0.0 else math.nan for value in values]


def _slope(values: Sequence[float]) -> float:
    count = len(values)
    mean_year = (count - 1) / 2.0
    mean_value = math.fsum(values) / count
    spread = math.fsum((year - mean_year) ** 2 for year in range(count))
    return math.fsum((year - mean_year) * (value - mean_value) for year, value in enumerate(values)) / spread


def series_settling(name: str, values: Sequence[float], as_ratio: bool, window_years: int = None) -> SeriesSettling:
    """The statistics of one series over its last `window_years` years (a window is one more point than steps)."""
    window = _transform(list(values)[-((window_years or SETTLING_WINDOW_YEARS) + 1):], as_ratio)
    if len(window) < 3 or any(math.isnan(value) for value in window):
        return SeriesSettling(name, math.inf, math.inf, 1.0, 0.0, 0.0)
    steps = [later - earlier for earlier, later in zip(window, window[1:])]
    net = window[-1] - window[0]
    along = sum(1 for step in steps if step * net > 0.0)
    return SeriesSettling(
        name, max(abs(step) for step in steps), _slope(window), along / len(steps),
        MAX_LOG_CHANGE_PER_YEAR if as_ratio else MAX_RATE_CHANGE_PER_YEAR,
        MAX_LOG_TREND_PER_YEAR if as_ratio else MAX_RATE_TREND_PER_YEAR)


def settling_report(rows: Sequence[Mapping[str, float]], window_years: int = None) -> List[SeriesSettling]:
    """Settling statistics for the price level, the unskilled wage, the money stock and the interest rate, from
    yearly rows with those keys (`economy_port_trace.spin_up_trace`)."""
    return [series_settling(key, [row[key] for row in rows], as_ratio, window_years) for key, as_ratio in SERIES]


def format_report(report: Sequence[SeriesSettling]) -> str:
    """One line per series: the statistics and whether it settled."""
    return "\n".join(
        "%-13s largest step %+.3f (bound %.3f)  trend %+.4f/yr (bound %.4f)  monotone %.2f  %s"
        % (item.name, item.largest_step, item.step_bound, item.trend_per_year, item.trend_bound,
           item.monotone_share, "settled" if item.settled else "NOT SETTLED")
        for item in report)
