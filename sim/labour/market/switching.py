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
from typing import Dict, List, Mapping, Optional, Tuple

import numpy as np

from sim.constants import declare

from . import aptitude, expectations, switching_kernel, training
from .records import MarketState, YearInputs, YearReport
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

Move = Tuple[str, str, List[float], float]   # source trade, destination trade, people per band, share of the training years


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


def switch_trades(state: MarketState, inputs: YearInputs, clearings: Mapping, report: YearReport) -> None:
    allowed = inputs.enterable_trades
    fallback = fallback_trade(inputs.trades)
    destinations = sorted(trade for trade in inputs.trades if allowed is None or trade in allowed)
    rounds = int(expectations.DECISION_ROUNDS_PER_YEAR)
    chances = {trade: aptitude.completion_by_band(inputs.trades[trade].difficulty) for trade in destinations}
    destination_position = {trade: position for position, trade in enumerate(destinations)}
    fixed = _DestinationArrays(
        chances=np.array([chances[trade] for trade in destinations]).reshape(len(destinations), aptitude.band_count()),
        years=np.array([inputs.trades[trade].training_years for trade in destinations]),
        families=[inputs.trades[trade].family for trade in destinations],
        position=destination_position, fallback_position=destination_position.get(fallback, -1))
    for area in sorted(state.workers):
        subsistence = inputs.subsistence_per_worker_year.get(area)
        if subsistence is None or subsistence <= 0.0:
            continue
        sources = [trade for trade in sorted(state.workers[area])
                   if trade in inputs.trades and aptitude.band_total(state.workers[area][trade]) > 0.0]
        if not sources:
            continue
        income = {trade: expectations.expected_income(state, inputs, clearings, area, trade)
                  for trade in sources}
        idle = {trade: expectations.idle_share_of(clearings.get((area, trade))) for trade in sources}
        baseline = expectations.expected_income(state, inputs, clearings, area, fallback)   # the young's unskilled option
        vacancies = {trade for trade in destinations
                     if (area, trade) in clearings and clearings[(area, trade)].vacant_hours > 0.0}
        # a switcher trains first, so a destination is weighed by its income after training (capped at the long-run
        # training cost), not by today's scarcity wage; a source is weighed by what it pays today (Complaint 678)
        later_income: Dict[str, float] = {}
        plan = _AreaPlan(inputs, fixed, sources, fallback, income, idle, baseline, vacancies, destinations, subsistence)
        stale = destinations   # trades whose income after training must be re-read (enrolling changes it)
        for _round in range(rounds):
            for trade in stale:
                later_income[trade] = expectations.income_at_graduation(state, inputs, clearings, area, trade,
                                                                        chances[trade])
            moves = _planned_moves(inputs, state.workers[area], plan, np.array([later_income[trade] for trade in destinations]))
            stale = _carry_out(state, inputs, report, area, plan, moves)


class _DestinationArrays:
    """What the year's destinations have whatever the area: chance of finishing per band, training years, family."""

    def __init__(self, chances, years, families, position, fallback_position):
        self.chances, self.years, self.families, self.position, self.fallback_position = chances, years, families, position, fallback_position


class _AreaPlan:
    """An area's sources, destinations and incomes as arrays, with the odds each (source, young or established) group planned on,
    carried from one round of switching to the next (`switching_kernel.plan_area`)."""

    def __init__(self, inputs, fixed, sources, fallback, income, idle, baseline, vacancies, destinations, subsistence):
        count_sources, count_destinations, count_bands = len(sources), len(destinations), fixed.chances.shape[1]
        self.sources, self.destinations, self.fixed, self.subsistence, self.baseline = sources, destinations, fixed, subsistence, baseline
        self.income = np.array([income[trade] for trade in sources])
        self.idle = np.array([idle[trade] for trade in sources])
        self.vacancies = np.array([trade in vacancies for trade in destinations], np.bool_)
        self.source_position = np.array([fixed.position.get(trade, -1) for trade in sources], np.int64)
        self.source_is_fallback = np.array([trade == fallback for trade in sources], np.bool_)
        source_families = [inputs.trades[trade].family for trade in sources]
        same = np.array([[family == other for other in fixed.families] for family in source_families]).reshape(count_sources, count_destinations)
        self.training_share = np.where(same, RETRAINING_SHARE_WITHIN_FAMILY, 1.0)
        self.valid = np.zeros((count_sources, 2), np.bool_)
        self.then = np.zeros((count_sources, 2, count_destinations))
        self.targets = np.zeros((count_sources, 2, count_destinations), np.bool_)
        self.shares = np.zeros((count_sources, 2, count_bands, count_destinations))
        self.moving = np.zeros((count_sources, 2, count_bands), np.bool_)
        self.active = np.zeros((count_sources, 2), np.bool_)
        self.considering = np.zeros((count_sources, 2))


class _Moves:
    """The round's moves in the order they are carried out (by destination, source, training share), one row each: source and
    destination positions, the share of the training years, and the people per band."""

    def __init__(self, counts, sources, destinations, shares, rows):
        self.counts, self.sources, self.destinations, self.shares, self.rows = counts, sources, destinations, shares, rows

    def as_tuples(self, plan: "_AreaPlan") -> List[Move]:
        return [(plan.sources[source], plan.destinations[destination], row, share) for source, destination, share, row in
                zip(self.sources.tolist(), self.destinations.tolist(), self.shares.tolist(), self.rows.tolist())]


def _planned_moves(inputs, workers, plan: _AreaPlan, later_income) -> Optional[_Moves]:
    """The moves of one round (None where there are none): for each source, the established workers then the young, the
    people of each ability band sent to each destination the band picks (`switching_kernel.plan_area` works out the odds)."""
    rounds = expectations.DECISION_ROUNDS_PER_YEAR
    counts = np.array([workers[source] for source in plan.sources])
    switching_kernel.plan_area(
        counts, plan.income, plan.idle, plan.baseline, later_income, plan.vacancies, plan.fixed.chances, plan.fixed.years,
        plan.training_share, plan.source_position, plan.source_is_fallback, plan.fixed.fallback_position, plan.subsistence,
        inputs.discount_rate, inputs.career_years, SWITCHING_CONSIDERATION_SHARE_PER_YEAR, REMAINING_CAREER_SHARE,
        PLAN_REUSE_TOLERANCE, SWITCHING_TASTE_SCALE, NEGLIGIBLE_MOVE_SHARE, plan.valid, plan.then, plan.targets, plan.shares,
        plan.moving, plan.active, plan.considering)
    possible = counts.shape[0] * 2 * len(plan.destinations)
    moves_source, moves_destination = np.empty(possible, np.int64), np.empty(possible, np.int64)
    moves_share, moves_rows = np.empty(possible), np.empty((possible, counts.shape[1]))
    found = switching_kernel.collect_moves(counts, plan.considering, plan.active, plan.moving, plan.shares, plan.training_share, rounds,
                                           moves_source, moves_destination, moves_share, moves_rows)
    if found == 0:
        return None
    return _Moves(counts, moves_source[:found], moves_destination[:found], moves_share[:found], moves_rows[:found])


def _carry_out(state: MarketState, inputs: YearInputs, report: YearReport, area: str, plan: _AreaPlan,
               moves: Optional[_Moves]) -> List[str]:
    """Take the switchers out of their trades and into training. Sources moving to one target on the
    same training length apply together, and the target's places are shared out between them in
    proportion to the people each sends (band by band; `switching_kernel.enrol_groups` is `training.enrol` for each group).
    Returns the trades that took trainees in."""
    if moves is None:
        return []
    workers = state.workers[area]
    have = moves.counts.copy()
    taken_amounts = np.empty_like(moves.rows)
    switching_kernel.take_moves(moves.sources, moves.rows, have, taken_amounts)      # `have` unless the move asks for less
    move_count = moves.sources.shape[0]
    group_of, members, group_starts = np.empty(move_count, np.int64), np.empty(move_count, np.int64), np.zeros(move_count + 1, np.int64)
    group_count = switching_kernel.group_moves(moves.destinations, moves.shares, group_of, members, group_starts)
    group_starts = group_starts[:group_count + 1]
    group_destination, group_share = moves.destinations[members[group_starts[:-1]]], moves.shares[members[group_starts[:-1]]]
    destination_count, band_count = len(plan.destinations), have.shape[1]
    source_of_destination = np.full(destination_count, -1, np.int64)
    for position, trade in enumerate(plan.sources):
        destination = plan.fixed.position.get(trade, -1)
        if destination >= 0:
            source_of_destination[destination] = position
    seats, school_bonus, enrolled = np.zeros(destination_count), np.zeros(destination_count), np.zeros(destination_count)
    last_years, last_bonus = np.zeros(destination_count), np.zeros(destination_count)
    last_exists = np.zeros(destination_count, np.bool_)
    for destination in np.unique(group_destination).tolist():      # the cohorts and school seats of the destinations the groups go to
        trade = plan.destinations[destination]
        if inputs.schools:
            seats[destination], school_bonus[destination] = training.school_places(inputs, area, trade)
        enrolled[destination] = training.enrolled(state, area, trade)
        cohorts = state.trainees.get(area, {}).get(trade)
        if cohorts:
            last_exists[destination], last_years[destination], last_bonus[destination] = True, cohorts[-1][0], cohorts[-1][2]
    admitted = np.zeros((group_count, band_count))
    kind, years, bonus = np.zeros(group_count, np.int64), np.zeros(group_count), np.zeros(group_count)
    moved = np.zeros(moves.sources.shape[0])
    added = np.zeros((destination_count, band_count))
    changed = np.zeros(have.shape[0], np.bool_)
    switching_kernel.enrol_groups(group_starts, members, group_destination, group_share, taken_amounts, moves.sources, have,
                                  source_of_destination, added, plan.fixed.years, training.APPRENTICES_PER_MASTER, seats, school_bonus,
                                  enrolled, last_years, last_bonus, last_exists, admitted, kind, years, bonus, moved, changed)
    for position in set(np.unique(moves.sources).tolist()) | set(np.flatnonzero(changed).tolist()):
        workers[plan.sources[position]][:] = have[position].tolist()
    for destination in np.flatnonzero(added.any(axis=1)).tolist():
        aptitude.add_bands(aptitude.bands_of(workers, plan.destinations[destination]), added[destination].tolist())
    targets: List[str] = []
    kinds = kind.tolist()
    for group in range(group_count):
        target = plan.destinations[int(group_destination[group])]
        targets.append(target)
        if kinds[group] == 1:
            state.trainees.setdefault(area, {}).setdefault(target, []).append([float(years[group]), admitted[group].tolist(), float(bonus[group])])
        elif kinds[group] == 2:
            aptitude.add_bands(state.trainees[area][target][-1][1], admitted[group].tolist())
    net: Dict[str, float] = {}
    for names, positions in ((plan.destinations, moves.destinations), (plan.sources, moves.sources)):
        sign = 1.0 if names is plan.destinations else -1.0
        counts = np.bincount(positions, minlength=len(names))
        changes = np.bincount(positions, weights=moved, minlength=len(names))
        for position in np.flatnonzero(counts).tolist():
            net[names[position]] = net.get(names[position], 0.0) + sign * float(changes[position])
    record = report.switched.setdefault(area, {})
    for trade, change in net.items():
        record[trade] = record.get(trade, 0.0) + change
    return targets


def _move_order(move: Move):
    return move[1], move[0], move[3]
