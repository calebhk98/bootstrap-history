"""The grace window after a staffing closure: whether it is open, what a reopening costs in it, and how to say so."""


def within_grace(closure_age, grace_years):
    """Whether a staffing closure of this age (years, None when the work was not shut for want of staff) is still
    inside the window in which its premises are kept."""
    return closure_age is not None and closure_age <= grace_years


def fee_after_grace(fee, closure_age, grace_years, discount):
    """The reopening fee: the discounted share inside the window, the whole fee outside it or for a work not shut
    for want of staff."""
    return fee * discount if within_grace(closure_age, grace_years) else fee


def grace_note(closure_age, grace_years):
    """A sentence saying which price a reopening is charged, or None when the work was not shut for want of staff."""
    if closure_age is None:
        return None
    if within_grace(closure_age, grace_years):
        return ("the staffing window is still open (shut %d years ago, of %d allowed), so this is the discounted "
                "tenth, not the full price" % (closure_age, grace_years))
    return ("the staffing discount only lasts %d years after a closure, and it has been %d - too long for the "
            "tenth, so this is the ordinary opening price" % (grace_years, closure_age))
