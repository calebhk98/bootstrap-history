"""Complaint 177: the credit forecast block that `start` prints is shown in
full once per game year; later starts that year show a one-line summary on
screen, and the figures stay in the JSON reply."""
from .harness import *  # noqa: F401,F403
from sim.engine.proto.render_typed import render_pretty
from sim.engine.proto.typed import parse_typed


def _run(sim_state, text):
    parsed, error = parse_typed(text)
    if error:
        return {"ok": False, "error": error}
    return S._agent_dispatch(sim_state, NODES, parsed)


def _credit_lines(text):
    """Lines of the rendered reply that belong to the two credit blocks."""
    lines = text.splitlines()
    kept = []
    inside = False
    for line in lines:
        if line.startswith("on credit") or line.startswith("total committed") or line.startswith("credit:"):
            inside = True
            kept.append(line)
        elif inside and line.startswith("  "):
            kept.append(line)
        else:
            inside = False
    return kept


# enough cash for the first start only, so the second and third both draw on credit
# stated in labour hours so it does not move with what the coin metal costs
LABOUR_HOURS_FOR_ONE_START = 6900.0
CASH_FOR_ONE_START = LABOUR_HOURS_FOR_ONE_START * sim().money_per_labour_hour()
borrower = sim(capital=CASH_FOR_ONE_START)
first = _run(borrower, "start units_standards")
second = _run(borrower, "start cn_damp_proof_course")
third = _run(borrower, "start tr_lateen_sail")
check("set-up: the second and third starts draw on credit",
      all(reply.get("ok") and "on_credit" in reply for reply in (second, third)), (second, third))

second_text = render_pretty("start", second)
third_text = render_pretty("start", third)
check("the first credit start prints the full forecast prose",
      "what_happens_there" in second["on_credit"] and "past that limit" in second_text, second_text)
check("a later start the same year keeps the figures in its JSON",
      third["on_credit"]["you_would_borrow"] > 0
      and third["total_committed_across_active_work"]["you_have_promised"] > 0
      and "what_happens_there" not in third["on_credit"]
      and "what_this_means" not in third["total_committed_across_active_work"], third)
check("...and prints only a one-line summary of the block on screen",
      len(_credit_lines(third_text)) <= 1 and "past that limit" not in third_text
      and "borrow" in third_text, third_text)

forced = sim(capital=CASH_FOR_ONE_START)
_run(forced, "start units_standards")
_run(forced, "start cn_damp_proof_course")
again = S._agent_dispatch(forced, NODES, {"cmd": "start", "id": "tr_lateen_sail", "full": True})
check("'full' asks for the whole block again",
      again.get("ok") and "what_happens_there" in again.get("on_credit", {}), again)

next_year = sim(capital=CASH_FOR_ONE_START)
_run(next_year, "start units_standards")
_run(next_year, "start cn_damp_proof_course")
next_year.year += 1
later = _run(next_year, "start tr_lateen_sail")
check("a new year shows the full block again",
      later.get("ok") and "what_happens_there" in later.get("on_credit", {}), later)
