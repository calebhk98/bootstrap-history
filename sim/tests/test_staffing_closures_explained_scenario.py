"""Scenarios in a whole game for the staffing closures explained: the staffing rule closes and reopens a concern and says so
(233), `stuck` recommends only what `open` would accept (219), and a project starved of directed hours is told the command
that reserves them (205). The tally, the summary, the lines and the sentences are in test_staffing_closures_explained."""
import re

from .harness import *  # noqa: F401,F403

CLOSING_NODE = concern_needing_craftsmen_to_supervise()


def staffed_sim():
    test_sim = sim(capital=1_000_000.0)
    test_sim.done.update(NODES[CLOSING_NODE]["pre"])
    test_sim.done.add(CLOSING_NODE)
    test_sim._done_changed()
    test_sim.employees["artisan"] = 6.0
    test_sim.labour._resync_pools()
    test_sim.open_venture(CLOSING_NODE)
    return test_sim


def new_messages(test_sim, start):
    return [message for _year, message in test_sim.log[start:]]


# --- 233: no craftsmen left closes the concern, with the line and the summary; the people back reopen it
closing_sim = staffed_sim()
closing_sim.employees["artisan"] = 0.0
closing_sim.labour._resync_pools()
log_start = len(closing_sim.log)
closed = closing_sim.close_unstaffed_ventures(closing_sim.year)
closure_text = " ".join(new_messages(closing_sim, log_start))
summary = closing_sim.staffing_closure_summary()
check("the staffing rule closes the concern, the line names the craftsmen short and the remedies, and the summary counts it",
      closed == [CLOSING_NODE] and "craftsm" in closure_text and all(remedy in closure_text for remedy in ("keep", "reserve", "auto_replace_foreman"))
      and summary is not None and re.search(r"closed 1\b", summary) and re.search(r"still shut 1\b", summary), (closed, closure_text, summary))
closing_sim.employees["artisan"] = 6.0
closing_sim.labour._resync_pools()
log_start = len(closing_sim.log)
closing_sim.reopen_restaffed_ventures(closing_sim.year)
check("with the people back the concern reopens, the line says how many are still shut and the summary reflects it",
      "still shut" in " ".join(new_messages(closing_sim, log_start))
      and re.search(r"reopened 1\b", closing_sim.staffing_closure_summary() or ""), closing_sim.staffing_closure_summary())

# --- 219: stuck recommends only what open accepts
recommend_sim = sim(capital=1e7)
for node_id in ("en_undershot_wheel", "mirror_amalgam"):
    recommend_sim.done.update(NODES[node_id]["pre"])
    recommend_sim.done.add(node_id)
recommend_sim._done_changed()
stuck_text = json.dumps(S._agent_dispatch(recommend_sim, NODES, {"cmd": "stuck"}))
recommended = re.findall(r"'open ([a-z0-9_]+)'", stuck_text)
foreman_node = "mirror_amalgam"
check("stuck makes an open recommendation, only of what open would accept, and never of a concern needing a foreman while none is free",
      bool(recommended) and all(recommend_sim.open_venture(node_id, pay=False)[0] for node_id in recommended)
      and foreman_node not in recommended
      and recommend_sim.staffing_open_refusal(foreman_node) == recommend_sim.open_venture(foreman_node)[1],
      (recommended, stuck_text[:300]))

# --- 205: a project starved of directed hours is told the command that reserves them
starve_sim = sim(capital=1e7)
first_id, second_id = "academy_network", "school_founded"   # no scarce material limits their pace
starve_sim.order = [first_id, second_id]
for node_id in (first_id, second_id):
    node = NODES[node_id]
    starve_sim.active[node_id] = dict(ph_left=float(node["ph"]), yrs=0.0, spent=0.0, cost_left=0.0,
                                      lab_left={trade: 0.0 for trade in node.get("lab", {})})
starve_sim.hour_allocations[first_id] = 1400.0
starve_sim.hour_allocations[second_id] = 1000.0
log_start = len(starve_sim.log)
starve_sim.step()
starved_lines = [message for message in new_messages(starve_sim, log_start)
                 if "DIRECTED HOURS UNUSED" in message and "before this one's turn came" in message]
check("the pool-ran-out reason names `allocate <project> <hours>`", starved_lines and "allocate %s" % second_id in starved_lines[0], starved_lines)
