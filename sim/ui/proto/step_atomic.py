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
