"""The money gate on beginning a project: the bill, plus what is already owed on work in hand, must fit inside
the cash held and the credit line."""


def start_shortfall(price, owed_on_work_in_hand, extra_owed, capital, credit_limit):
    """(owed in all, what cash plus credit can raise, how far the bill is past it). Debt adds nothing to what can
    be raised: only positive capital counts, on top of the credit line. A shortfall of zero means the start is
    affordable, including when the total exactly equals the ceiling."""
    owed = extra_owed + owed_on_work_in_hand
    ceiling = max(0.0, capital) + credit_limit
    return owed, ceiling, max(0.0, owed + price - ceiling)
