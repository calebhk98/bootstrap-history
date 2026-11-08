"""The year's clearings on the state's grid: one row per (area, trade), for the phases after the clearing to read by grid row.

`RESULTS` has a row for every grid row; `cleared` says whether the pair had a market this year, and the rest are that market's
figures (what a `LabourClearing` carries). The bids' demand schedule of each market is a slice of two arrays beside the table
(`demand_first`, `demand_count` index them).
"""
from typing import NamedTuple, Sequence

import numpy

from sim.compiled_tables.spec import Column, TableSpec

from .clearing_results import Clearings

RESULTS = TableSpec("Results", (
    Column("cleared", numpy.bool_, "the pair had a market this year", "flag"),
    Column("wage", numpy.float64, "the wage every hour hired was paid", "currency per hour"),
    Column("hours_offered", numpy.float64, "hours the workers sold at that wage", "hours per year"),
    Column("hours_wanted", numpy.float64, "hours the employers wanted at that wage", "hours per year"),
    Column("hours_hired", numpy.float64, "hours hired", "hours per year"),
    Column("target_wage", numpy.float64, "where the wage is heading; NaN: nowhere in particular (read as the wage)", "currency per hour"),
    Column("hours_held", numpy.float64, "hours the trade's workers had at the clearing, sold or kept; NaN: not recorded", "hours per year"),
    Column("demand_first", numpy.int64, "first entry of the market's demand schedule in `Grid.demand_caps`", "index"),
    Column("demand_count", numpy.int64, "how many entries the schedule has", "entries"),
))
Results = RESULTS.make_type(__name__)


class Grid(NamedTuple):
    """The year's results and the demand schedules they point into: (maximum wage, hours) of each bid of a market."""
    results: Results
    demand_caps: numpy.ndarray
    demand_hours: numpy.ndarray


def grid_of(state, clearings: Sequence) -> Grid:
    """The clearings of the year on the state's grid. `clearings` is a `Clearings` (columns, read straight) or any sequence of
    `LabourClearing` objects."""
    rows = len(state.ids.areas) * len(state.ids.trades)
    results = RESULTS.new_table(Results, rows, rows)
    results.target_wage[:] = numpy.nan
    results.hours_held[:] = numpy.nan
    if isinstance(clearings, Clearings):
        return _from_columns(state, clearings, results)
    caps, hours = [], []
    for clearing in clearings:
        row = state.grid_row(clearing.area, clearing.trade)
        results.cleared[row] = True
        results.wage[row], results.hours_offered[row] = clearing.wage, clearing.hours_offered
        results.hours_wanted[row], results.hours_hired[row] = clearing.hours_wanted, clearing.hours_hired
        if clearing.target_wage is not None:
            results.target_wage[row] = clearing.target_wage
        if clearing.hours_held is not None:
            results.hours_held[row] = clearing.hours_held
        results.demand_first[row], results.demand_count[row] = len(caps), len(clearing.demand)
        caps.extend(cap for cap, _hours in clearing.demand)
        hours.extend(share for _cap, share in clearing.demand)
    return Grid(results, numpy.array(caps), numpy.array(hours))


def _from_columns(state, clearings: Clearings, results: Results) -> Grid:
    rows = clearings.area * len(state.ids.trades) + clearings.trade
    results.cleared[rows] = True
    for name in ("wage", "hours_offered", "hours_wanted", "hours_hired", "target_wage", "hours_held"):
        getattr(results, name)[rows] = getattr(clearings, name)
    results.demand_first[rows] = clearings.bid_offsets[clearings.markets]
    results.demand_count[rows] = clearings.bid_offsets[clearings.markets + 1] - clearings.bid_offsets[clearings.markets]
    return Grid(results, clearings.caps, clearings.bid_hours)
