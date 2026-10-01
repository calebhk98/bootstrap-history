"""A hook a front end sets so a multi-year step commits each simulated year as it goes."""

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
    from .saveload import save_state

    def commit(sim, summary):
        if session:
            save_state(sim, session)
        if summary.get("years_asked", 1) < 2:
            return
        try:
            stream.write("  year %s: %s den, %d completed, %d closed, population %+.1f%%\n"
                         % (summary["year"], format(summary["capital"], ",.0f"), summary["completed"],
                            summary["closed"], 100 * summary["population_change"]))
            stream.flush()
        except (OSError, ValueError):
            pass
    return commit
