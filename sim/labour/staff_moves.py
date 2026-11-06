"""The rules behind hiring, teaching, dismissing and commissioning, on values given: the literacy wall, who is let go
and which apprenticeships stop, the hours a trade can spare and what stops a founder selling his own."""
import dataclasses
import math

WALL_TOLERANCE = 1e-6

FOUNDER_DEAD = "founder_dead"
NO_SUCH_TRADE = "no_such_trade"
TRADE_ABSENT = "trade_absent"
HOURS_NOT_POSITIVE = "hours_not_positive"
HOURS_SHORT = "hours_short"


def stochastic_round(rng, target):
    """Round a continuous headcount target to a whole number of people without biasing where it is heading.

    People are whole; the path toward them need not be. A fractional remainder is spent as this year's chance of
    the next whole person: 6.4 is six for certain and a 40% chance of a seventh, drawn from `rng` so it is
    reproducible. Rounding down every year would stall growth a person short of every ceiling (0.18 of the gap
    a year, floored, never crosses the next whole number); rounding up would over-hire the other way."""
    target = max(0.0, target)
    whole = math.floor(target)
    if rng.random() < target - whole:
        whole += 1
    return float(whole)


def crosses_literacy_wall(have, count, ceiling):
    """Whether taking on `count` more of a lettered trade, over the `have` already employed or being taught, would
    pass the most this society's reading will ever supply."""
    return have + count > ceiling + WALL_TOLERANCE


def whole_people_under_wall(ceiling, have):
    """The whole people that may still be taken on under the wall (none when it is full or passed)."""
    return int(max(0.0, ceiling - have) + 1e-9)


def apprentices_of(training, trade):
    """People of a trade being taught, from training rows."""
    return sum(row.people for row in training if row.trade == trade)


def dismiss(employed, training, trade, count):
    """Let `count` people of a trade go: (people let go, people left employed, people of apprenticeship stopped,
    apprenticeships left, the count not met). Staff go before apprentices. A fraction of a person asked for is
    rounded up to a whole one while that is fewer than are employed. Records with no people left are dropped, but
    only when apprentices are stopped; otherwise the records are returned as given."""
    count = float(count)
    if employed > 0 and abs(count - round(count)) > 1e-6 and count < employed:
        count = float(math.ceil(count))
    gone, remaining = 0.0, employed
    if employed > 0:
        gone = min(count, employed)
        remaining = employed - gone if employed - gone > 1e-9 else 0.0
        count -= gone
    stopped, still = 0.0, training
    if count > 0 and apprentices_of(training, trade) > 0:
        still = []
        for row in training:
            row = dataclasses.replace(row)
            if row.trade == trade and count > 0:
                take = min(count, row.people)
                row.people -= take
                count -= take
                stopped += take
            if row.trade is None or row.people > 1e-9:
                still.append(row)
    return gone, remaining, stopped, still, count


def commission_spare_hours(market_supply, contracted):
    """The hours of a trade the local market can still spare this year once those already commissioned are taken."""
    return market_supply - contracted


def wage_work_blocker(founder_alive, known_trade, trade_open_of, hours, hours_left_of):
    """What stops the founder selling `hours` of his own work in a trade, or None. In the order the refusals are
    given: he is dead; there is no such trade; nobody here employs one (`trade_open_of()`, asked only for a known
    trade); the hours are not positive; he has fewer uncommitted hours (`hours_left_of()`) than asked."""
    if not founder_alive:
        return FOUNDER_DEAD
    if not known_trade:
        return NO_SUCH_TRADE
    if not trade_open_of():
        return TRADE_ABSENT
    if float(hours) <= 0:
        return HOURS_NOT_POSITIVE
    if float(hours) > hours_left_of():
        return HOURS_SHORT
    return None
