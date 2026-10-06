"""start_explain_once: regression checks, run individually with `--only start_explain_once`."""
from .harness import *  # noqa: F401,F403

from sim.ui.proto.render_screens_start import render_start

# Complaint 76: `start` explains the fixed price and the untrained-trade warning once, then points back.

test_sim = sim(capital=1_000_000)
first = S._agent_dispatch(test_sim, NODES, {"cmd": "start", "id": "tx2_shed"})
second = S._agent_dispatch(test_sim, NODES, {"cmd": "start", "id": "tx2_retting"})
third = S._agent_dispatch(test_sim, NODES, {"cmd": "start", "id": "tx2_count_standard"})

check("the first start explains the fixed price in full", "fixed for this project" in first.get("note", ""), first.get("note"))
for label, reply in (("second", second), ("third", third)):
    check("the %s start keeps the bill as a number" % label,
          isinstance(reply.get("the_bill_you_have_taken_on"), (int, float)), reply)
    check("the %s start drops the fixed-price paragraph" % label,
          "Quotes move with prices" not in reply.get("note", ""), reply.get("note"))
    check("...but still says the price is fixed", "fixed" in reply.get("note", ""), reply.get("note"))
    check("the %s start's text screen does not repeat the paragraph" % label,
          "Quotes move with prices" not in render_start(reply), render_start(reply))

again = S._agent_dispatch(test_sim, NODES, {"cmd": "start", "id": "tx2_bleaching_sun", "full": True})
check("`full` shows the fixed-price paragraph again", "Quotes move with prices" in again.get("note", ""), again.get("note"))

# The untrained-trade warning keeps its trade names but loses its instructions after the first showing.
untrained_sim = sim(capital=1_000_000)
untrained_sim.labour.market_supply = lambda trade: 0.0
untrained_sim.start_project = lambda node_id, precaution=False: (True, "")
one = S._agent_dispatch(untrained_sim, NODES, {"cmd": "start", "id": "ag2_composting"})
two = S._agent_dispatch(untrained_sim, NODES, {"cmd": "start", "id": "ag2_grafting"})
trades = sorted(NODES["ag2_grafting"]["lab"])
check("the first untrained-trade warning gives the full instructions", "four years" in one.get("warning", ""), one.get("warning"))
check("a later one still names the trades", bool(trades) and all(trade in two.get("warning", "") for trade in trades),
      two.get("warning"))
check("...without repeating the instructions", "four years" not in two.get("warning", ""), two.get("warning"))
