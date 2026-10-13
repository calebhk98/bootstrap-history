"""A hook a front end sets so a multi-year step commits each simulated year as it goes."""

import time

from sim.constants import declare

SAVE_INTERVAL_SECONDS = declare(
    "SAVE_INTERVAL_SECONDS", 30.0, kind="temporary_heuristic", unit="seconds",
    why="A multi-year step saves the game between years only when this long has passed since the last save, "
        "so a fast year costs no write and a killed command still loses at most about this much play; "
        "the right figure is what a player would accept to lose, which nobody has measured.")

_after_year = [None]


def set_after_year(callback):
    """callback(sim, summary) runs after every simulated year of a step; None removes it."""
    _after_year[0] = callback


def after_year(sim, summary):
    callback = _after_year[0]
    if callback is not None:
        callback(sim, summary)


def commit_and_report(session, stream):
    """A callback that saves the game to `session` (when there is one) and prints one line per year to `stream`."""
    from sim.engine.ui_port import money_text
    from sim.ui.memory import save_session

    last_saved = [time.monotonic()]   # the game on disk is the one the command started from

    def commit(sim, summary):
        # a one-year step is saved once by the caller after the command
        if summary.get("years_asked", 1) < 2:
            return
        # the last year asked for is saved by the caller right after the command
        if (session and not summary.get("last_asked_year")
                and time.monotonic() - last_saved[0] >= SAVE_INTERVAL_SECONDS):
            save_session(sim, session)
            last_saved[0] = time.monotonic()
        try:
            stream.write("  year %s: %s, %d completed, %d closed, population %+.1f%%\n"
                         % (summary["year"], money_text(summary["capital"], sim, grouped=True, short=True), summary["completed"],
                            summary["closed"], 100 * summary["population_change"]))
            stream.flush()
        except (OSError, ValueError):
            pass
    return commit
