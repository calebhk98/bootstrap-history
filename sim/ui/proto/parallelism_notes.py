"""The two notes that teach parallel play: once on the first long calendar-floor project, and whenever the founder's
free hours are going to waste."""
from sim.engine import ui_port
from sim.engine.ui_port import plain_number

LONG_CALENDAR_FLOOR_YEARS = 2
UNUSED_HOURS_FLOOR = 200      # spare founder-hours a year below which nothing is shouted


def calendar_floor_note(name, years, already_said):
    """The one-time note on a project whose calendar floor is long enough that it cannot be the only thing in hand;
    None for a shorter one, or once it has been said."""
    if years < LONG_CALENDAR_FLOOR_YEARS or already_said is not None:
        return None
    return ("%s will take at least %d year%s, whatever else you do. That "
            "time is not spent watching it: your founder-hours and staff "
            "are free the moment this year's share of the work is paid "
            "for, and nothing stops you spending them on something else "
            "in the meantime. The strongest play is usually to keep "
            "several things running at once - start preparing the next "
            "layer now rather than waiting for this one to finish."
            % (name, years, "" if years == 1 else "s"))


def free_hours_note(founder_hours_left_by_project, spare_hours):
    """The warning that founder-hours are going into nothing: every project in hand has spent its hours for the year (it
    waits on the calendar), or none is in hand, and more than a floor of hours is spare. None otherwise."""
    if spare_hours <= UNUSED_HOURS_FLOOR:
        return None
    hours = plain_number(max(0.0, spare_hours))
    if founder_hours_left_by_project:
        if not all(left <= 0 for left in founder_hours_left_by_project):
            return None
        return ("%s founder-hours this year are going into nothing: every "
                "project you have in hand is only waiting on the calendar "
                "now, not on you or your money. A calendar floor is not "
                "exclusive research time - start something else alongside "
                "it while it runs. 'available' or 'stuck' says what you "
                "could begin today; 'idle' splits the hours and names the delay." % hours)
    return ("%s founder-hours this year are going into nothing at all: "
            "you have no work in hand. Hours do not carry to next year. "
            "'available' or 'stuck' says what you could begin today; 'idle' splits the hours and names the delay." % hours)


KEY_CALENDAR_FLOOR = "a_calendar_floor_is_not_exclusive_research_time"


def add_calendar_floor_note(reply, sim, name, years):
    """Put the one-time calendar-floor note in a `start` reply when it has not been said in this game, and record that it was."""
    note = calendar_floor_note(name, years, ui_port.said_parallelism(sim))
    if note is not None:
        ui_port.set_said_parallelism(sim, True)
        reply[KEY_CALENDAR_FLOOR] = note


def free_hours_going_unused(sim, active):
    """The `state` field naming founder-hours going unused: the hours each active project still wants of the founder, against the
    director pool left uncommitted."""
    return free_hours_note([value["founder_hours_left"] for value in active.values()],
                           max(0.0, sim.view("hours_available")["director_pool"] - sim.view("hours_available")["director_committed"]))
