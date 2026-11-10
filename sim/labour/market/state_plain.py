"""`MarketState.to_plain` read a column at a time: the tables are turned into Python lists once and cut up by pair."""
import numpy

from .state_fields import AsksField, HiredField, TraineesField, WagesField, WorkersField


def _pairs(state, field):
    """[(area name, [(trade name, grid row), ...]), ...] in the order the field's view lists them."""
    trade_names = state.ids.trades.names
    area_names = state.ids.areas.names
    trade_count = len(trade_names)
    pairs = []
    for area in state.named_areas(field.name):
        trades = []
        if trade_count:
            rows = slice(area * trade_count, (area + 1) * trade_count)
            present = numpy.flatnonzero(field.present(state, rows))
            ordered = present[numpy.argsort(field.order(state, rows)[present], kind="stable")].tolist()
            first = area * trade_count
            trades = [(trade_names[trade], first + trade) for trade in ordered]
        pairs.append((area_names[area], trades))
    return pairs


def _band_lists(people, lengths, rows):
    """{row: its band list} for the rows, each cut to its stored length (only these rows leave the table)."""
    wanted = numpy.unique(numpy.array(rows, dtype=numpy.int64))
    cut = people[wanted].tolist()
    return {row: bands[:length] for row, bands, length in zip(wanted.tolist(), cut, lengths[wanted].tolist())}


def _workers(state, pairs):
    table = state.workers_table
    bands = _band_lists(table.people, table.length, [row for _area, trades in pairs for _trade, row in trades])
    return {area: {trade: bands[row].copy() for trade, row in trades} for area, trades in pairs}


def _scalars(state, pairs, column):
    values = getattr(state.market_table, column).tolist()
    return {area: {trade: values[row] for trade, row in trades} for area, trades in pairs}


def _trainees(state, pairs):
    market, table = state.market_table, state.trainee_table
    first, count = market.cohort_first.tolist(), market.cohort_count.tolist()
    years_left, bonus = table.years_left.tolist(), table.bonus.tolist()
    cohorts = [cohort for _area, trades in pairs for _trade, row in trades for cohort in range(first[row], first[row] + count[row])]
    people = _band_lists(table.people, table.length, cohorts) if cohorts else {}
    return {area: {trade: [[years_left[cohort], people[cohort], bonus[cohort]]
                           for cohort in range(first[row], first[row] + count[row])]
                   for trade, row in trades} for area, trades in pairs}


def _hired(state, pairs):
    market, table = state.market_table, state.hired_table
    first, count = market.hired_first.tolist(), market.hired_count.tolist()
    names = state.ids.employers.table.names
    employers, hours = table.employer.tolist(), table.hours.tolist()
    plain = {}
    for area, trades in pairs:
        by_trade = plain[area] = {}
        for trade, row in trades:
            start, stop = first[row], first[row] + count[row]
            by_employer = dict(zip([names[number] for number in employers[start:stop]], hours[start:stop]))
            if len(by_employer) != stop - start:      # an employer twice in one market: the view reads its first row
                by_employer = {name: hours[start + employers[start:stop].index(number)]
                               for name, number in ((names[each], each) for each in employers[start:stop])}
            by_trade[trade] = by_employer
    return plain


def to_plain(state) -> dict:
    """Nested dicts and lists of numbers and strings, as the dict views would give them."""
    return {"workers": _workers(state, _pairs(state, WorkersField)),
            "trainees": _trainees(state, _pairs(state, TraineesField)),
            "wages": _scalars(state, _pairs(state, WagesField), "wage"),
            "hired_hours": _hired(state, _pairs(state, HiredField)),
            "asks": _scalars(state, _pairs(state, AsksField), "ask")}
