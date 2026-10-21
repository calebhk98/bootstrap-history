"""The credit forecast of a `start` reply is explained in full once per game year; later starts keep the figures."""

CREDIT_PROSE = {"on_credit": ("nothing_is_borrowed_yet", "what_happens_there"),
                "total_committed_across_active_work": ("what_this_means",)}
SAID_KEY = "credit_forecast"


def shorten(out, said, year, full_asked):
    """Take the explanatory prose out of the reply's credit blocks unless this is the first showing in `year` or the
    player asked for `full`. `said` is {block: year last explained}; it is updated in place when the reply is in full.
    Returns whether the reply is in full (None when it has no credit block)."""
    blocks = [key for key in CREDIT_PROSE if key in out]
    if not blocks:
        return None
    in_full = bool(full_asked) or said.get(SAID_KEY) != year
    if in_full:
        said[SAID_KEY] = year
    else:
        for key in blocks:
            for prose_key in CREDIT_PROSE[key]:
                out[key].pop(prose_key, None)
    out["credit_forecast_in_full"] = in_full
    return in_full
