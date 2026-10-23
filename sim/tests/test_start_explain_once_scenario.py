"""Scenario for Complaint 76 in a whole game: `start` explains the fixed price and the untrained-trade warning once, then points
back. The once-only rule is test_start_explain_once; the wording checks here are presentation."""
from .harness import *  # noqa: F401,F403

from sim.ui.proto.render_screens_start import render_start

test_sim = unopened_sim(capital=1_000_000)
first = S._agent_dispatch(test_sim, NODES, {"cmd": "start", "id": "tx2_shed"})
second = S._agent_dispatch(test_sim, NODES, {"cmd": "start", "id": "tx2_retting"})
third = S._agent_dispatch(test_sim, NODES, {"cmd": "start", "id": "tx2_count_standard"})

check("the first start explains the fixed price in full", "fixed for this project" in first.get("note", ""), first.get("note"))
# presentation: the paragraph is dropped from the reply and its text screen, the bill stays a number
check("a later start keeps the bill as a number, drops the fixed-price paragraph and still says the price is fixed",
      all(isinstance(reply.get("the_bill_you_have_taken_on"), (int, float))
          and "Quotes move with prices" not in reply.get("note", "") and "fixed" in reply.get("note", "")
          and "Quotes move with prices" not in render_start(reply) for reply in (second, third)), (second, third))

again = S._agent_dispatch(test_sim, NODES, {"cmd": "start", "id": "tx2_bleaching_sun", "full": True})
check("`full` shows the fixed-price paragraph again", "Quotes move with prices" in again.get("note", ""), again.get("note"))

# The untrained-trade warning keeps its trade names but loses its instructions after the first showing.
untrained_sim = unopened_sim(capital=1_000_000)
untrained_sim.labour.market_supply = lambda trade: 0.0
untrained_sim.start_project = lambda node_id, precaution=False: (True, "")
one = S._agent_dispatch(untrained_sim, NODES, {"cmd": "start", "id": "ag2_composting"})
two = S._agent_dispatch(untrained_sim, NODES, {"cmd": "start", "id": "ag2_grafting"})
trades = sorted(NODES["ag2_grafting"]["lab"])
check("the first untrained-trade warning gives the full instructions", "four years" in one.get("warning", ""), one.get("warning"))
check("a later one still names the trades", bool(trades) and all(trade in two.get("warning", "") for trade in trades),
      two.get("warning"))
check("...without repeating the instructions", "four years" not in two.get("warning", ""), two.get("warning"))
