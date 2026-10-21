"""SCENARIO (Complaint 640): Complaint 640, audit batch 3, scenario: a year that raises leaves the whole game as it was, the retry runs the year
once, and a multi-year step that fails in its third year keeps the two before it. The description of the failure is a
function with tests of its own: test_complaint_587_atomic_year."""
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
check("scenario atomic year: a failed year replies not ok with its cause and the exception's kind, "
      "and does not advance the calendar",
      failed.get("ok") is False and failed.get("cause") == "year_failed" and failed.get("exception_kind") == "RuntimeError"
      and one.year == start_year, (failed.get("cause"), failed.get("exception_kind"), one.year))
check("scenario atomic year: a failed year leaves the whole game as it was, and saving after it leaves the file as it was",
      state_text(one) == before_text and (save_state(one, saved), open(saved, "rb").read() == on_disk)[1])
retry = S._agent_dispatch(one, NODES, {"cmd": "step"})
check("scenario atomic year: the next step runs the year, once",
      retry.get("ok") is True and one.year == start_year + 1 and len(_effects(one)) == 1, (retry.get("ok"), one.year, _effects(one)))

three = _game({3})
first_year = three.year
reply = S._agent_dispatch(three, NODES, {"cmd": "step", "years": 5})
check("scenario atomic year: a multi-year step failing in its third year keeps two years, says where it stopped, "
      "and the two kept years' phases took effect once each",
      three.year == first_year + 2 and reply.get("ok") is True and reply.get("stopped_kind") == "year_failed"
      and reply["year_failed"]["years_ran"] == 2 and reply["year_failed"]["cause"] == "year_failed"
      and reply["year_failed"]["exception_kind"] == "RuntimeError" and len(_effects(three)) == 2,
      (three.year, reply.get("year_failed"), _effects(three)))
