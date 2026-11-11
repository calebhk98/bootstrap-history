"""The modes of `auto_hire`: replace-only hires back the people lost this year and never grows the staff."""
REPLACE_ONLY = "replace"


def staff_grows(hire_mode, has_room):
    """Whether the yearly staff phase smooths the staff toward capacity: the auto_hire setting is on (and not replace-only,
    which hires back only what the clearing's standing bids replace) and the credit line leaves room to hire."""
    return bool(hire_mode) and hire_mode != REPLACE_ONLY and has_room


def completion_grants_staff(hire_mode):
    """Whether a finished institution hands its staff over outright: only where the yearly staff phase does not already grow
    the pools toward a capacity that counts the institution (auto_hire off, or replace-only)."""
    return not staff_grows(hire_mode, True)


def replacement_wanted(trade_id, have, taught, drawn_on, target_headcount, generic_staff):
    """The headcount a specialist trade is topped back up to, or None when it is not. Only a trade something draws on
    (a project in hand or an open concern) is replaced, so idle specialists are not paid for decades; of those only a trade
    the household taught is raised to `target_headcount`, and the `generic_staff` trades are left to the staff target."""
    if trade_id in generic_staff or trade_id not in drawn_on:
        return None
    return max(have, target_headcount if taught else 0.0)


def replacement_targets(employees, trades_created, drawn_on, target_headcount, generic_staff, tolerance=0.02):
    """[(trade, headcount)] the yearly staff step tops back up, in sorted trade order: every trade held or taught (a trade drops
    out of `employees` once its last person is lost) that `replacement_wanted` raises by more than `tolerance` people."""
    targets = []
    for trade_id in sorted(set(employees) | set(trades_created)):
        have = employees.get(trade_id, 0.0)
        want = replacement_wanted(trade_id, have, trade_id in trades_created, drawn_on, target_headcount, generic_staff)
        if want is not None and want - have > tolerance:
            targets.append((trade_id, want))
    return targets
