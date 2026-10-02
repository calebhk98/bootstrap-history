"""staffing closures explained: Complaints/229, 215, 201, 202, 231, 242."""
import re

from .harness import *  # noqa: F401,F403

from sim.engine.data import TRADE_FAMILY
from sim.engine.proto.render_screens_big import _staffing_warning_sentences

CLOSING_NODE = concern_needing_craftsmen_to_supervise()


def staffed_sim():
	test_sim = sim(capital=1_000_000.0)
	test_sim.done.update(NODES[CLOSING_NODE]["pre"])
	test_sim.done.add(CLOSING_NODE)
	test_sim._done_changed()
	test_sim.employees["artisan"] = 6.0
	test_sim._resync_pools()
	test_sim.open_venture(CLOSING_NODE)
	return test_sim


def new_messages(test_sim, start):
	return [message for _year, message in test_sim.log[start:]]


# --- 233: the closure line says why, how many are still shut, and names the remedies
closing_sim = staffed_sim()
closing_sim.employees["artisan"] = 0.0
closing_sim._resync_pools()
log_start = len(closing_sim.log)
closed = closing_sim.close_unstaffed_ventures(closing_sim.year)
closure_text = " ".join(new_messages(closing_sim, log_start))
check("set-up: the staffing rule closed the concern", closed == [CLOSING_NODE], closed)
for remedy in ("keep", "reserve", "auto_replace_foreman"):
	check("the closure line names '%s' as a remedy" % remedy, remedy in closure_text, closure_text)
check("the closure line names the resource that ran short", "craftsm" in closure_text, closure_text)
summary = closing_sim.staffing_closure_summary()
check("the closure summary counts closed, reopened and still shut",
      summary is not None and re.search(r"closed 1\b", summary) and re.search(r"reopened 0\b", summary)
      and re.search(r"still shut 1\b", summary), summary)
closing_sim.employees["artisan"] = 6.0
closing_sim._resync_pools()
log_start = len(closing_sim.log)
closing_sim.reopen_restaffed_ventures(closing_sim.year)
reopen_text = " ".join(new_messages(closing_sim, log_start))
check("the reopening line says how many are still shut, so the two counts reconcile",
      "still shut" in reopen_text, reopen_text)
check("the summary reflects the reopening",
      re.search(r"reopened 1\b", closing_sim.staffing_closure_summary() or ""),
      closing_sim.staffing_closure_summary())
check("no summary when nothing has closed", sim(capital=1e6).staffing_closure_summary() is None)

# --- 219: stuck recommends only what open accepts
recommend_sim = sim(capital=1e7)
for node_id in ("tex_spinning_wheel",):
	recommend_sim.done.update(NODES[node_id]["pre"])
	recommend_sim.done.add(node_id)
recommend_sim._done_changed()
stuck_reply = S._agent_dispatch(recommend_sim, NODES, {"cmd": "stuck"})
stuck_text = json.dumps(stuck_reply)
recommended = re.findall(r"'open ([a-z0-9_]+)'", stuck_text)
check("set-up: stuck makes an open recommendation", recommended, stuck_text)
for node_id in recommended:
	check("stuck recommends %s only if open would accept it" % node_id,
	      recommend_sim.open_venture(node_id, pay=False)[0], recommend_sim.open_venture(node_id, pay=False))
foreman_node = "tex_spinning_wheel"
foreman_trade, _fte = recommend_sim.venture_foreman(foreman_node)
check("one function states the staffing refusal open applies",
      recommend_sim.staffing_open_refusal(foreman_node) == recommend_sim.open_venture(foreman_node)[1],
      recommend_sim.staffing_open_refusal(foreman_node))
check("a shut concern that needs a foreman is never recommended while no foreman is free",
      foreman_node not in recommended, recommended)

# --- 205: a project starved of directed hours is told the command that reserves them
starve_sim = sim(capital=1e7)
first_id, second_id = "academy_network", "corpus_written"
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
check("the pool-ran-out reason names `allocate <project> <hours>`",
      starved_lines and "allocate %s" % second_id in starved_lines[0], starved_lines)

# --- 206: a standing order that keeps falling short is reported once until it changes
second_name = NODES[second_id]["name"]


def unused_lines_about(test_sim, start, name):
	return [message for message in new_messages(test_sim, start)
	        if "DIRECTED HOURS UNUSED" in message and name in message]


repeat_sim = sim(capital=1e7)
repeat_sim.active[second_id] = dict(ph_left=1000.0, yrs=0.0, spent=0.0, cost_left=0.0, lab_left={})
repeat_sim.hour_allocations[second_id] = 1000.0
pace_reason = "its own pace this year - at most 300 hours could not use the rest"
for year_number in range(3):
	log_start = len(repeat_sim.log)
	repeat_sim.report_unused_directed_hours([(second_id, 700.0, pace_reason.replace("300", str(300 - year_number)))])
	said = len(unused_lines_about(repeat_sim, log_start, second_name))
	check("year %d: a shortfall that falls short the same way is reported once, not yearly" % year_number,
	      said == (1 if year_number == 0 else 0), said)
repeat_sim.hour_allocations[second_id] = 600.0
log_start = len(repeat_sim.log)
repeat_sim.report_unused_directed_hours([(second_id, 300.0, pace_reason)])
check("a changed standing order is reported afresh",
      len(unused_lines_about(repeat_sim, log_start, second_name)) == 1, new_messages(repeat_sim, log_start))
repeat_sim.report_unused_directed_hours([])
log_start = len(repeat_sim.log)
repeat_sim.report_unused_directed_hours([(second_id, 300.0, pace_reason)])
check("a shortfall that recovered and returned is reported afresh",
      len(unused_lines_about(repeat_sim, log_start, second_name)) == 1, new_messages(repeat_sim, log_start))
check("the first report says it will not repeat and how to lower the order",
      "once" in starved_lines[0] or "not repeat" in starved_lines[0], starved_lines)

# --- 235: the spare number is explained in full-time equivalents
spare_sim = sim(capital=1e6)
spare_sim.done.add("ag2_canning")
spare_sim._done_changed()
spare_sim.open_venture("ag2_canning")
spare_sim.state.household.artisans += 1.0
spare_sim.cfg["immortal"] = False  # an immortal founder's own share is never at risk
spare_warnings = spare_sim.staffing_closure_warnings()
check("set-up: the concern is on the staffing warning list", spare_warnings, spare_warnings)
if spare_warnings:
	warning = spare_warnings[0]
	check("the warning carries held, in use and allowance behind its spare number",
	      all(key in warning for key in ("held", "in_use", "allowance")), warning)
	check("the spare number is held plus allowance minus in use",
	      abs(warning["within"] - (warning["held"] + warning["allowance"] - warning["in_use"])) < 0.06, warning)
	spare_screen = " ".join(_staffing_warning_sentences(spare_warnings))
	check("the state screen explains the arithmetic once, in full-time equivalents",
	      "full-time" in spare_screen and "in use" in spare_screen, spare_screen)

# --- 246: the interchangeability sentence comes from the trade table
ventures_reply = S._agent_dispatch(sim(capital=1e6), NODES, {"cmd": "ventures"})
sentence = ventures_reply.get("these_are_not_interchangeable", "")
scholar_trades = sorted(trade for trade, family in TRADE_FAMILY.items() if family == "scholar")
check("every scholar-family trade is named in the sentence",
      all(trade in sentence for trade in scholar_trades), sentence)
check("no craft trade is called a scholar in the sentence",
      "machinist" not in sentence and "smith" not in sentence, sentence)
