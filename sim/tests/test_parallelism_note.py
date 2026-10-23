"""Parallelism is the central mechanic and nothing taught it: an external blind playthrough treated a long
calendar-floor project as exclusive research time. Two notes teach it: a one-time note on the first long-calendar-floor
project, and the free founder-hours shouted when everything in hand waits on the calendar. The rules are called on the
numbers the test states; the replies that carry them are called on stand-ins below."""
from .harness import *  # noqa: F401,F403

from sim.ui.proto.parallelism_notes import calendar_floor_note, free_hours_note

QUICK_TOPIC = True

# --- the one-time note
note = calendar_floor_note("A long project", 3, None)
check("the first long-calendar-floor project gets a note that says to spend the spare hours on something else",
      note is not None and "else" in note and "3 years" in note,   # presentation: the note's wording
      note)
check("...but only once", calendar_floor_note("A second long project", 3, True) is None)
check("a project whose floor is under two years gets none", calendar_floor_note("A short one", 1, None) is None)
check("a floor of exactly two years is long enough", calendar_floor_note("Two years", 2, None) is not None)

# --- free hours, shouted, when everything running is calendar-bound
check("every project in hand has spent its hours and real founder-hours sit unused: the warning is given",
      free_hours_note([0.0, 0.0], 5000.0) is not None)
check("one project still wants the founder's hours: no warning", free_hours_note([0.0, 10.0], 5000.0) is None)
check("nothing in hand and hours to spare: the warning says there is no work", free_hours_note([], 5000.0) is not None)
check("spare hours at or under the floor are not shouted about",
      free_hours_note([0.0], 200.0) is None and free_hours_note([], 100.0) is None)
check("the two warnings differ: one names a calendar wait, the other no work in hand",
      free_hours_note([0.0], 5000.0) != free_hours_note([], 5000.0))

# --- the notes reach the replies
from types import SimpleNamespace

from sim.ui.proto.parallelism_notes import KEY_CALENDAR_FLOOR, add_calendar_floor_note, free_hours_going_unused

game = SimpleNamespace(_said_parallelism=None)
first, second = {}, {}
add_calendar_floor_note(first, game, "A long project", 3)
add_calendar_floor_note(second, game, "Another long project", 3)
check("starting the first long project carries the note", KEY_CALENDAR_FLOOR in first, first)
check("...and a second in the same game does not repeat it", second == {} and game._said_parallelism is True, second)
short_game, short = SimpleNamespace(_said_parallelism=None), {}
add_calendar_floor_note(short, short_game, "A short one", 1)
check("a short project adds nothing and does not spend the note", short == {} and short_game._said_parallelism is None)


def world(pool, committed):
    return SimpleNamespace(labour=SimpleNamespace(director_pool=lambda: pool, director_hours_committed=lambda: committed))


check("when every active project only waits on the calendar and real founder-hours sit unused, state says so",
      free_hours_going_unused(world(6000.0, 500.0), {"a": {"founder_hours_left": 0.0}}) is not None)
check("a project that still wants the founder's hours keeps state quiet",
      free_hours_going_unused(world(6000.0, 500.0), {"a": {"founder_hours_left": 40.0}}) is None)
check("hours already committed are not spare",
      free_hours_going_unused(world(6000.0, 5900.0), {"a": {"founder_hours_left": 0.0}}) is None)
