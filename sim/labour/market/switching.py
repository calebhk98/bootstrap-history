"""Workers re-weigh their trade against the others, with a stay option (DESIGN.md, step 4).

A switcher becomes a trainee of the new trade (shorter within a skill family) through the same places
as any trainee; those not admitted stay in their old trade. The fallback trade takes people straight in.

Of the people who consider a change in a year, one career's worth in a lifetime of them (`1 / career_years` of
a trade's people) are the young who have just come of working age: they hold no trade yet, so their baseline is the
unskilled income, their horizon is a whole career and they weigh a trade with no stay threshold, since the training
premium (premium.py) leaves exactly such a person indifferent at the long-run wage. Their own trade is one of their
options, scored at what it pays now over a career against the unskilled income with no training to pay, so a trade that
pays best keeps its young. The rest are established workers:
half a career ahead, the old trade's income to give up, and only a move worth more than staying. The economy keeps
the core's people equal to demography's by scaling every worker and trainee of a tile by one factor
(`scale_people` in sim/economy/labour_state.py), so trainees in a cohort are not lost or created by it.
"""
from typing import Dict, Mapping

import numpy as np

from sim.constants import declare

from . import aptitude, cohort_book, expectations, switch_year, training
from .year_rates import rates_of
from .records import MarketState, YearInputs, YearReport
from .results_grid import grid_of
from .switch_kernel import Destinations, DONE, Switched, SwitchRules
from .trades import fallback_trade

RETRAINING_SHARE_WITHIN_FAMILY = declare(
    "RETRAINING_SHARE_WITHIN_FAMILY", 0.3, kind="temporary_heuristic",
    unit="share of a trade's full training years", source=None, confidence="D",
    why="Someone already skilled in a trade's family (same materials, tools and habits) learns a related "
        "trade faster than a newcomer. Not fitted; to be derived from the skills the two trades share.")

REMAINING_CAREER_SHARE = declare(
    "REMAINING_CAREER_SHARE", 0.5, kind="temporary_heuristic",
    unit="share of a full career still ahead of a worker weighing a switch", source=None, confidence="D",
    why="Workers are spread across their careers, so on average half remains. Replace with the age "
        "structure when workers carry an age.")

SWITCHING_TASTE_SCALE = declare(
    "SWITCHING_TASTE_SCALE", 1.0, kind="temporary_heuristic",
    unit="years of an area's subsistence income per e-fold of choice odds", source=None, confidence="D",
    why="How sharply considering workers follow the gain of a switch. Not fitted.")

SWITCHING_CONSIDERATION_SHARE_PER_YEAR = declare(
    "SWITCHING_CONSIDERATION_SHARE_PER_YEAR", 0.05, kind="temporary_heuristic",
    unit="share of a trade's workers who reconsider it in a year", source=None, confidence="D",
    why="Most workers do not weigh a change of trade in any year (ties, custom, lack of information); "
        "this caps yearly switching. Not fitted.")

NEGLIGIBLE_MOVE_SHARE = declare(
    "NEGLIGIBLE_MOVE_SHARE", 1e-3, kind="temporary_heuristic", unit="share of the workers weighing a switch",
    source=None, confidence="D",
    why="A destination that fewer than this share of the workers weighing a switch would pick is not trained "
        "for; its few go to the destination most of them pick. Every destination has some logit weight, and "
        "training a few for each costs a cohort record apiece. Not fitted.")

PLAN_REUSE_TOLERANCE = declare(
    "PLAN_REUSE_TOLERANCE", 0.01, kind="temporary_heuristic",
    unit="years of an area's subsistence income", source=None, confidence="D",
    why="A later round of switching keeps the choice odds of the round before when no destination's "
        "income after training has moved by more than this; saves re-weighing every trade for a change "
        "too small to alter anyone's choice. Not fitted.")



def _families(inputs: YearInputs, trade_names) -> np.ndarray:
    """A number per trade for its skill family: trades of one family share a number (a trade the year does not list gets one of its own)."""
    codes: Dict[str, int] = {}
    numbers = []
    for name in trade_names:
        spec = inputs.trades.get(name)
        numbers.append(codes.setdefault(spec.family, len(codes)) if spec is not None else -1)
    return np.array(numbers, np.int64)


def _school_grid(state: MarketState, inputs: YearInputs):
    """School seats and their seat-weighted completion bonus on the grid (`training.school_places` for every pair)."""
    rows = len(state.ids.areas) * len(state.ids.trades)
    seats, weight, bonus = np.zeros(rows), np.zeros(rows), np.zeros(rows)
    for school in inputs.schools:
        row = state.grid_row(school.area, school.trade)
        if row is not None and school.seats > 0.0:
            seats[row] += school.seats
            weight[row] += school.seats * school.completion_bonus
    held = seats > 0.0
    bonus[held] = weight[held] / seats[held]
    return seats, bonus


def _destinations(state: MarketState, inputs: YearInputs) -> Destinations:
    ids = state.ids
    allowed = inputs.enterable_trades
    names = [name for name in ids.trades.names if name in inputs.trades and (allowed is None or name in allowed)]
    numbers = np.array([ids.trades.number(name) for name in names], np.int64)
    position = np.full(len(ids.trades), -1, np.int64)
    position[numbers] = np.arange(len(names))
    fallback = ids.trades.number(fallback_trade(inputs.trades))
    chances = np.array([aptitude.completion_by_band(inputs.trades[name].difficulty) for name in names]).reshape(len(names), state.bands)
    seats, bonus = _school_grid(state, inputs)
    return Destinations(numbers, chances, np.array([inputs.trades[name].training_years for name in names]),
                        np.array([name in inputs.trades for name in ids.trades.names], np.bool_), _families(inputs, ids.trades.names),
                        position, fallback, int(position[fallback]), seats, bonus)


def switch_trades(state: MarketState, inputs: YearInputs, clearings, report: YearReport) -> None:
    """Workers re-weigh their trade against the others in every area (`switch_year.switch_all`), and the report records the net
    change per trade. `clearings` is the year's `Clearings`, a sequence of `LabourClearing`s or a mapping of them."""
    state.admit((), list(inputs.trades))
    grid = grid_of(state, clearings.values() if isinstance(clearings, Mapping) else clearings)
    destinations = _destinations(state, inputs)
    rules = SwitchRules(SWITCHING_CONSIDERATION_SHARE_PER_YEAR, REMAINING_CAREER_SHARE, PLAN_REUSE_TOLERANCE, SWITCHING_TASTE_SCALE,
                        NEGLIGIBLE_MOVE_SHARE, RETRAINING_SHARE_WITHIN_FAMILY, int(expectations.DECISION_ROUNDS_PER_YEAR),
                        training.APPRENTICES_PER_MASTER)
    rows = len(state.workers_table.present)
    room = len(state.ids.areas) * rules.rounds * 2 * max(len(destinations.trade), 1)      # at most two training lengths per destination per round
    book = cohort_book.new_book(state, room)
    counter = np.array([state._order], np.int64)
    switched = Switched(np.zeros(rows), np.zeros(rows, np.bool_), np.zeros(rows, np.int64), counter)
    status = switch_year.switch_all(rates_of(state, inputs), rules, grid.results, grid.demand_caps, grid.demand_hours, state.workers_table,
                                    state.areas_table, state.market_table, book, destinations, switched)
    if status != DONE:
        raise RuntimeError("switching ran out of room for new cohorts (%d reserved)" % room)
    state._order = int(counter[0])
    state.merge_cohorts(book.pending)
    trade_count = len(state.ids.trades)
    seen = np.flatnonzero(switched.seen)
    for row in seen[np.argsort(switched.order[seen], kind="stable")].tolist():
        report.switched.setdefault(state.ids.areas.names[row // trade_count], {})[state.ids.trades.names[row % trade_count]] = float(switched.net[row])
