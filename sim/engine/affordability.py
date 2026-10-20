"""What a household can raise, when it is warned about its credit line, what it spends on appearances and when an
earning concern opens in arrears. Plain arithmetic on the numbers handed in."""

NEAR_LIMIT_FROM = 0.7
START_KIND = "start"
OPEN_KIND = "open"


def calculate_affordability(capital, credit_ceiling, credit_share, preserve_debt=False):
    """Pure calculation used by every quote and state-changing spend check."""
    if preserve_debt:
        return max(0.0, capital) + credit_ceiling * credit_share
    return max(0.0, capital + credit_ceiling * credit_share)


def spending_power_of(kind, capital, credit_limit, ordinary_share):
    """What could be raised for a spend of this kind. A start may draw the whole credit line, other spends the
    ordinary share of it; the debt already carried counts against any spend but a door fee on a built concern (`open`),
    which asks only what the line could advance, and nothing at all once the debt is past the line."""
    share = 1.0 if kind == START_KIND else ordinary_share
    if kind == OPEN_KIND:
        if capital < -credit_limit:
            return 0.0
        return calculate_affordability(capital, credit_limit, share, preserve_debt=True)
    return calculate_affordability(capital, credit_limit, share)


def near_limit(capital, credit_limit, said_before):
    """(warn now, said by the end of the year, share of the line used) for the warning that comes before the line
    is crossed: given once on entering the band, not again while in it, and not at all past the line, where the
    creditors have already acted."""
    if credit_limit <= 0 or capital >= 0:
        return False, False, 0.0
    used = -capital / credit_limit
    if used >= 1.0:
        return False, True, used
    if used < NEAR_LIMIT_FROM:
        return False, False, used
    if said_before:
        return False, True, used
    return True, True, used


def appearances_spending(listed_status, capital, room, per_capital, room_share):
    """What a household spends on keeping up appearances: the status its standing lists and the share of its wealth
    it must track, but never more than a share of what is left after eating (room) plus that wealth share."""
    nominal = listed_status + max(0.0, capital) * per_capital
    return min(nominal, room * room_share + max(0.0, capital) * per_capital)


def payback_years(capex, revenue, upkeep):
    """Years an earning concern takes to pay for its own doors."""
    return capex / max(0.01, revenue - upkeep)


def deep_in_arrears(capital, credit_limit, share):
    """Whether the debt carried is past a share of the credit line."""
    return capital < 0 and -capital > credit_limit * share


def reputation_hit_taken(hit, reputation):
    """The part of a reputation penalty that can actually be taken: none from a name already at nothing."""
    return min(hit, max(0.0, reputation))
