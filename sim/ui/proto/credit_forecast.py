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


def borrowing_forecast(instalments, materials_paid_now, capital, credit_limit_of, interest_rate_of, service_forecast_of):
    """What starting a project would borrow, as a forecast and not a receipt: the instalments it still owes against the
    cash held, the interest at the going rate, the debt it would leave, and the limit past which nobody lends. None
    when the cash covers the instalments. The limit, rate and service forecast are asked only when there is a gap."""
    gap = instalments - max(0.0, capital)
    if gap <= 0:
        return None
    rate = interest_rate_of()
    after = -(min(0.0, capital) - gap)
    return {
        "nothing_is_borrowed_yet": (
            "this is a forecast, not a receipt: credit only actually "
            "draws down at step resolution, if cash runs short paying "
            "this year's share. These figures are what happens if it "
            "does, on today's numbers."),
        "instalments_still_owed": instalments,
        "materials_already_paid_from_cash": materials_paid_now,
        "you_would_borrow": round(gap, 1),
        "interest_rate_percent": round(rate * 100, 1),
        "estimated_annual_interest": round(gap * rate, 1),
        "you_would_then_owe": round(after, 1),
        **service_forecast_of(after),
        "no_one_advances_past": round(credit_limit_of(), 1),
        "what_happens_there":
            "past that limit every project in hand halts unfinished, "
            "nobody funds new work for some years, and your creditors "
            "take and sell what you are running - including things you "
            "built long ago and had no debt against.",
    }


def start_credit_forecast(sim, instalments, materials_paid_now):
    """`borrowing_forecast` for a `start` on `sim`: its cash, credit line, going rate and the forecast of servicing a debt."""
    return borrowing_forecast(instalments, materials_paid_now, sim.view("acting_balance")(), sim.view("credit_limit"), sim.view("debt_interest_rate"),
                              sim.view("debt_service_forecast"))
