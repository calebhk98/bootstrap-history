"""What a request to teach, dismiss or commission must satisfy before money or hours move: plain functions of the values
asked and the figures that bound them, each giving the first refusal that applies or None (Complaint 640). The labour
verbs in `labour_training` read the world and call these."""
import math

from sim.refusal import Refusal


def train_request_refusal(trade_known, trade, count, find_source, source_absent):
    """(source trade, refusal) of a request to teach `count` people `trade`: the first of an unknown trade, a count that is
    not positive or not whole, no source trade (`find_source()` is asked only once the count passes), or a source trade
    that does not exist here (`source_absent(source)`). The source is the one named, lowered, when there is no refusal."""
    if not trade_known:
        return None, Refusal("no_such_trade", "no such trade: %s" % trade)
    if count <= 0:
        return None, Refusal("count_not_positive", "n must be greater than zero. Nothing was changed.")
    if abs(count - round(count)) > 1e-6:
        return None, Refusal("count_not_whole", "you teach whole people, not %g of one. Teach %d or %d."
                             % (count, math.floor(count), math.ceil(count)))
    source = (find_source() or "").strip().lower()
    if not source:
        return None, Refusal("no_source_trade", "there is no trade here to teach %ss from" % trade)
    if source_absent(source):
        return None, Refusal("source_trade_absent", "you cannot teach from %ss; there are none" % source)
    return source, None


def teaching_hours_refusal(hours, uncommitted_pool, count, trade):
    """A refusal when teaching takes more of the founder's own hours than he has uncommitted this year."""
    if hours > uncommitted_pool:
        return Refusal("founder_hours_short", "teaching %g %ss takes %.0f of your own hours and you have "
                       "%.0f uncommitted this year" % (count, trade, hours, max(0.0, uncommitted_pool)))
    return None


def teaching_fee(count, source_annual_wage, kept_years, outside_teacher, teaching_hours, hours_per_person_year):
    """Money paid up front to teach `count` people: the source trade's wages while they learn (the years kept), and,
    when another actor teaches, that teacher's hours at the same wage."""
    fee = count * source_annual_wage * kept_years
    if outside_teacher:
        fee += teaching_hours * source_annual_wage / hours_per_person_year
    return fee


def fire_refusal(trade, employed, apprentices):
    """The refusal to dismiss a trade of which nobody is employed and none are being taught; None otherwise."""
    if employed <= 0 and apprentices <= 0:
        return Refusal("nobody_to_dismiss", "you employ no %ss, and none are being taught" % trade)
    return None


def commission_request_refusal(trade_known, trade, hours, trade_exists, trade_note, spare_hours):
    """The refusal to commission `hours` of `trade`: an unknown trade, hours not positive, a trade that does not
    exist here, or more hours than the trade can spare this year; None otherwise."""
    if not trade_known:
        return Refusal("no_such_trade", "no such trade: %s" % trade)
    if hours <= 0:
        return Refusal("hours_not_positive", "hours must be greater than zero. Nothing was changed.")
    if not trade_exists:
        return Refusal("trade_absent", "no %s will take the work; the trade does not exist here: %s" % (trade, trade_note))
    if hours > spare_hours:
        return Refusal("hours_over_spare", "the %ss here can spare %.0f more hours this year, not %.0f"
                       % (trade, max(0.0, spare_hours), hours))
    return None
