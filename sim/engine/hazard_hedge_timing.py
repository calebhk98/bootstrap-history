"""Whether each hedge against a hazard could be finished before its window opens."""
import math


def hedge_timing(years_to_finish, current_year, window_start, in_progress):
    """The timing of one hedge against one hazard window.

    `years_to_finish` is the calendar floor the hedge needs even if started today. The hedge is
    in time only when it finishes in a year before the window opens; a window already open
    cannot be beaten.
    """
    earliest_finish = current_year + int(math.ceil(years_to_finish))
    in_time = (not in_progress) and earliest_finish < window_start
    if in_progress:
        words = ("the window is open now; earliest finish %d, so it cannot help this one"
                 % earliest_finish)
    elif in_time:
        words = ("earliest finish %d, window opens %d: %d years to spare"
                 % (earliest_finish, window_start, window_start - earliest_finish))
    else:
        words = ("earliest finish %d, window opens %d: too late unless it is already under way"
                 % (earliest_finish, window_start))
    return {"earliest_finish_year": earliest_finish, "window_opens_year": window_start,
            "in_time_if_started_today": in_time, "in_words": words}


def add_timing_to_steps(advice_by_kind, current_year, window_start, in_progress):
    """Put `hedge_timing` on every step that carries a calendar floor."""
    for advice in advice_by_kind.values():
        if not isinstance(advice, dict):
            continue
        for step in advice.get("you_could_begin_now_toward_it") or []:
            floor = step.get("years_even_if_you_start_today")
            if floor is not None:
                step["timing"] = hedge_timing(floor, current_year, window_start, in_progress)
