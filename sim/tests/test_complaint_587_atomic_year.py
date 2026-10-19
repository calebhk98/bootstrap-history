"""Complaint 587: a year that raises leaves the game as it was, the reply says so with a cause, and the retry runs
the year once; a multi-year step that fails in its third year keeps the two before it."""
from .harness import *  # noqa: F401,F403
from sim.engine.saveload import save_state, state_text

EFFECT = "atomic-year-effect"


def _game(failing_calls):
    """A game whose market raises on the listed call numbers, and whose first phase leaves one log line a year."""
    test_sim = sim(events=False, surveyed=())
    test_sim.end_year = test_sim.cfg["start_year"] + 200
    calls = {"market": 0}
    real_market = test_sim._step_market
    real_first = test_sim._step_apprenticeships

    def market():
        calls["market"] += 1
        if calls["market"] in failing_calls:
            raise RuntimeError("forced failure")
        real_market()

    def first_phase():
        test_sim.log.append((test_sim.year, EFFECT))
        real_first()

    test_sim._step_market = market
    test_sim._step_apprenticeships = first_phase
    return test_sim


def _effects(test_sim):
    return [row for row in test_sim.log if row[1] == EFFECT]


one = _game({1})
start_year = one.year
saved = os.path.join(tempfile.mkdtemp(), "session.json")
save_state(one, saved)
on_disk = open(saved, "rb").read()
before_text = state_text(one)
failed = S._agent_dispatch(one, NODES, {"cmd": "step"})
check("a failed year replies not ok with the cause year_failed",
      failed.get("ok") is False and failed.get("cause") == "year_failed", failed.get("cause"))
check("the reply names the exception's kind", failed.get("exception_kind") == "RuntimeError", failed.get("exception_kind"))
check("a failed year does not advance the calendar", one.year == start_year, one.year)
check("a failed year leaves the whole game as it was", state_text(one) == before_text)
save_state(one, saved)
check("saving after a failed year leaves the saved game as it was", open(saved, "rb").read() == on_disk)
retry = S._agent_dispatch(one, NODES, {"cmd": "step"})
check("the next step runs the year", retry.get("ok") is True and one.year == start_year + 1, (retry.get("ok"), one.year))
check("the year's phases took effect once", len(_effects(one)) == 1, _effects(one))

three = _game({3})
first_year = three.year
reply = S._agent_dispatch(three, NODES, {"cmd": "step", "years": 5})
check("a multi-year step failing in its third year keeps two years", three.year == first_year + 2, three.year)
check("the reply says where it stopped",
      reply.get("ok") is True and reply.get("stopped_kind") == "year_failed"
      and reply["year_failed"]["years_ran"] == 2 and reply["year_failed"]["cause"] == "year_failed"
      and reply["year_failed"]["exception_kind"] == "RuntimeError", reply.get("year_failed"))
check("the two kept years' phases took effect once each", len(_effects(three)) == 2, _effects(three))
