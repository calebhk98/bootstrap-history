"""The warning before a multi-year step that would throw founder-hours away.

Founder-hours do not bank: each year draws a fresh pool and what goes unused is gone. A player with long
calendar-floor projects running can `step 5` and unintentionally waste thousands of usable hours if the portfolio was
not full first. The warning is non-blocking: it says so and the years still run."""

from sim.engine.ui_port import plain_number


def multi_year_hours_warning(years, enabled, hours_going_unused, first_startable_name, hours_available, waiting_words):
    """The warning text, or None.

    None for a single year (the warning protects a MULTI-year request from spending the same idle year more than
    once unnoticed), when the machine-wide setting is off, when this year has no idle hours (`hours_going_unused`
    is the same test `state` reports as free_hours_going_unused), or when nothing is startable (the warning would
    tell the player to do something they cannot do). `first_startable_name()` and `waiting_words()` are only called when everything else
    holds, because finding something startable scans the tree."""
    if years <= 1 or not enabled or not hours_going_unused:
        return None
    startable_name = first_startable_name()
    if not startable_name:
        return None
    return ("before stepping %d years: %s founder-hours this "
            "year are already going to waste, and '%s' is one "
            "thing you could start today that would use some of "
            "them. Founder-hours do not bank at all: step() "
            "draws a fresh pool every year, and what goes "
            "unused this year is simply gone, never carried "
            "into the next one - so 'step %d' spends this "
            "year's slack exactly as idle as it is right now, "
            "%d more times over, unless you start something "
            "first. Running projects wait on: %s. Proceeding anyway."
            % (years, plain_number(hours_available or 0.0), startable_name, years, years, waiting_words()))
