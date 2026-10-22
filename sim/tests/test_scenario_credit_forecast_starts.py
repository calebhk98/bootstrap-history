"""SCENARIO (Complaint 640): Complaint 640, audit batch 3, scenario: a household that borrows to start work is told the credit forecast in full
once in a year, and `full` asks for it again. The rules are plain functions with tests of their own:
test_complaint_173_credit_forecast_once."""
from .harness import *  # noqa: F401,F403
from sim.ui.proto.render_typed import render_pretty
from sim.ui.proto.typed import parse_typed


def _run(sim_state, text):
    parsed, error = parse_typed(text)
    if error:
        return {"ok": False, "error": error}
    return S._agent_dispatch(sim_state, NODES, parsed)


# enough cash for the first start only: what it pays at once plus its bill, read off a household with cash to spare.
# What is left after it is less than either later bill, so both draw on credit.
FIRST_START = "tr_lateen_sail"
SECOND_START = "prc_straightedge"
THIRD_START = "lnd_wheelbarrow"


def cash_for_one_start():
    rich = sim(capital=1.0e9)
    before = rich.capital
    reply = _run(rich, "start " + FIRST_START)
    return before - rich.capital + reply["of_which_instalments_still_owed"] + 1.0


CASH_FOR_ONE_START = cash_for_one_start()


def borrower_after_two_starts():
    """A household whose cash covered the first start and nothing after it, with the first two starts made."""
    household = sim(capital=1.0e6)
    household.market_credit_room = lambda actor_id: None     # the forecast is under test, not the opening's loan book (fully lent to others): the household's own standing sets the line
    household.state.household.capital = CASH_FOR_ONE_START
    first = _run(household, "start " + FIRST_START)
    household.state.household.capital = 0.0      # no cash after the first start, so every later start's materials are borrowed
    return household, first, _run(household, "start " + SECOND_START)


_borrower, _first, _second = borrower_after_two_starts()
_third = _run(_borrower, "start " + THIRD_START)
check("scenario credit forecast: the second and third starts draw on credit",
      all(reply.get("ok") and "on_credit" in reply for reply in (_second, _third)), (_second, _third))
check("scenario credit forecast: the first credit start explains the forecast in full",
      _second["credit_forecast_in_full"] and "what_happens_there" in _second["on_credit"]
      and "past that limit" in render_pretty("start", _second), _second)
check("scenario credit forecast: a later start the same year keeps its figures and prints a one-line summary",
      _third["credit_forecast_in_full"] is False and _third["on_credit"]["you_would_borrow"] > 0
      and _third["total_committed_across_active_work"]["you_have_promised"] > 0
      and "what_happens_there" not in _third["on_credit"]
      and "past that limit" not in render_pretty("start", _third), _third)

_forced, _, _ = borrower_after_two_starts()
_again = S._agent_dispatch(_forced, NODES, {"cmd": "start", "id": THIRD_START, "full": True})
check("scenario credit forecast: 'full' asks for the whole block again",
      _again.get("ok") and "what_happens_there" in _again.get("on_credit", {}), _again)
