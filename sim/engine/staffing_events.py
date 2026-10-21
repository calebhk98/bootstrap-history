"""The log line for concerns the staffing rule shut: a plain function of what closed and what it was short of."""
from sim.refusal import LogLine

NAMED_CLOSED = 4


def unstaffed_closure_line(closed, shortfalls, shortfall_words, shut_count, remedies, earnings_stopped_per_year):
    """The event for concerns closed for want of staff, naming them, the shortfall and what they stopped earning."""
    return LogLine(
        "concerns_closed_unstaffed", "nobody left to keep an eye on %d concern%s (short of %s), so "
        "%s closed; %d now shut for want of staff after this "
        "year's reopenings. You still know how; reopen with "
        "'open' once you have the people. The premises "
        "and the stock stand for a few years yet, so "
        "reopening soon costs a tenth of what opening did. %s"
        % (len(closed), "" if len(closed) == 1 else "s", shortfall_words,
           ", ".join(sorted(closed)[:NAMED_CLOSED]) + (" and others" if len(closed) > NAMED_CLOSED else ""),
           shut_count, remedies),
        concerns=sorted(closed), closed_because="short_staffed", short=shortfalls,
        stops_earnings_per_year=earnings_stopped_per_year)
