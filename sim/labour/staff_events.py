"""The log line for people who left the payroll: plain function of what was lost and which concerns it stops."""
from sim.refusal import LogLine

KIND_STOPS_CONCERNS = "staff_lost_stops_concerns"
KIND_PLAIN = "staff_lost"
NAMED_STOPS = 4


def people_text(counts):
    """'3 artisans, 1 smith': whole numbers when the count is near one, a tenth otherwise."""
    return ", ".join("%s %s%s" % (("%d" % round(count) if abs(count - round(count)) < 0.05 else "%.1f" % count),
                                  trade, "" if abs(count - 1) < 0.05 else "s")
                     for trade, count in sorted(counts.items()))


def staff_lost_line(cause, counts, stops, earnings_stopped_per_year):
    """The event for people who left, by trade, with why and which running concerns the loss will shut; None when
    nobody left. `cause` completes "you lose <people> to <cause>". A loss that shuts a concern is its own kind."""
    counts = {trade: count for trade, count in counts.items() if count > 0}
    if not counts:
        return None
    stops = sorted(stops)
    text = "you lose %s to %s" % (people_text(counts), cause)
    if stops:
        text += "; %s will close for want of staff unless you replace them" % ", ".join(stops[:NAMED_STOPS])
    return LogLine(KIND_STOPS_CONCERNS if stops else KIND_PLAIN, text, reason=cause.replace(" ", "_"),
                   trades=counts, stops=stops, stops_earnings_per_year=round(earnings_stopped_per_year, 1))
