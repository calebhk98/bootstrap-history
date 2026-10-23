"""A year either completes or leaves the game as it was: snapshot before, restore on an exception."""
from sim.engine.saveload import restore_state_text, state_text
from sim.refusal import Refusal


def snapshot(sim):
    """The game as text, to hand back to `failed_year` if the year raises."""
    return state_text(sim)


def failed_year(sim, held, error, year, years_ran):
    """Restore the game from `held` and describe the year that did not run."""
    restore_state_text(sim, held)
    kind = type(error).__name__
    return {"cause": "year_failed", "exception_kind": kind, "year": year, "years_ran": years_ran,
            "text": Refusal("year_failed", "year %s did not run (%s: %s); the game is as it was before that year. "
                            "Step again to retry it." % (year, kind, error), exception_kind=kind, year=year)}


def run_year_or_undo(sim, held, run_year, years_ran):
    """Call `run_year()`. None when it returned; when it raised, the game restored from `held` and the failure's description."""
    try:
        run_year()
    except Exception as error:  # the year is undone whole; the years before it stand
        return failed_year(sim, held, error, sim.year, years_ran)
    return None


def whole_step_failed_reply(failure):
    """The reply to a step whose very first year failed: not ok, with the failure's text, kind and year."""
    return {"ok": False, "error": failure["text"], "exception_kind": failure["exception_kind"], "year": failure["year"]}


def partial_step_failure(failure, years_ran, years_asked):
    """(stopped_early text, stopped_kind, year_failed fields) for a step that kept `years_ran` years and then failed."""
    text = "stopped after %d of the %d years you asked for: %s" % (years_ran, years_asked, failure["text"])
    fields = {key: failure[key] for key in ("cause", "exception_kind", "year", "years_ran")}
    return text, "year_failed", fields
