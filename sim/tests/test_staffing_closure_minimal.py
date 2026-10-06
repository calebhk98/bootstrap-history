"""staffing_closure_minimal: the yearly staff check closes only what a real shortfall requires,
and never a concern that `open` would accept with the same staff."""
from .harness import *  # noqa: F401,F403


def concerns_with_foreman(test_sim, trade, count):
	# Cheapest-to-hold concerns whose supervision needs a foreman of this trade.
	if not hasattr(concerns_with_foreman, "foremen"):
		concerns_with_foreman.foremen = {
			node_id: test_sim.venture_foreman(node_id)[0] for node_id in sorted(NODES)
			if test_sim.is_venture(node_id) and NODES[node_id]["rev"] > NODES[node_id]["up"]
			and node_id not in test_sim.CAPABILITY_INSTITUTIONS}
	found = [node_id for node_id, foreman in concerns_with_foreman.foremen.items() if foreman == trade]
	return found[:count]


def crowded_sim(smith_concerns, other_concerns):
	test_sim = sim(capital=10_000_000.0)
	for node_id in smith_concerns + other_concerns:
		test_sim.done.update(NODES[node_id]["pre"])
	test_sim._done_changed()
	test_sim.employees["artisan"] = 500.0
	test_sim.employees["smith"] = len(smith_concerns) * test_sim.VENTURE_FOREMAN_SHARE
	test_sim.employees["scholar"] = 50.0
	test_sim.employees["carpenter"] = 50.0
	test_sim.employees["machinist"] = 50.0
	test_sim.labour._resync_pools()
	run_it(test_sim, *(smith_concerns + other_concerns))
	return test_sim


probe = sim()
smiths = concerns_with_foreman(probe, "smith", 6)
others = concerns_with_foreman(probe, "carpenter", 3) + concerns_with_foreman(probe, "machinist", 3)

# --- losing part of the smiths closes only smith concerns, only as many as needed
crowded = crowded_sim(smiths, others)
check("set-up: everything is covered, nothing closes",
      crowded.close_unstaffed_ventures(crowded.year) == [])
crowded.employees["smith"] -= 2 * crowded.VENTURE_FOREMAN_SHARE
crowded.labour._resync_pools()
closed = crowded.close_unstaffed_ventures(crowded.year)
check("a smith shortfall of two concerns' worth closes exactly two concerns",
      len(closed) == 2, closed)
check("only concerns drawing on smiths close",
      all(crowded.venture_foreman(node_id)[0] == "smith" for node_id in closed), closed)
check("the lowest net value goes first",
      sorted(closed, key=lambda k: NODES[k]["rev"] - NODES[k]["up"])
      == sorted(sorted(smiths, key=lambda k: NODES[k]["rev"] - NODES[k]["up"])[:2],
                key=lambda k: NODES[k]["rev"] - NODES[k]["up"]), closed)
check("concerns needing other trades stay open",
      all(node_id in crowded.operating for node_id in others))
check("open is refused for what the check closed, with the same staff",
      all(not crowded.open_venture(node_id, pay=False)[0] for node_id in closed))
check("the closure is recorded as a staffing closure",
      all(crowded.staff_closure_age(node_id) == 0 for node_id in closed))

# --- a generic craftsmen shortage closes the minimum, and nothing closed would fit
generic = crowded_sim(smiths, others)
used_art = generic.venture_staff_used()[1]
generic.employees["artisan"] = 0.0
generic.state.household.artisans = used_art - 1.0 - generic.FOUNDER_IS_WORTH
generic_closed = generic.close_unstaffed_ventures(generic.year)
artisans_after = generic.venture_staff_used()[1]
allowance = generic.state.household.artisans + generic.FOUNDER_IS_WORTH + generic.STAFFING_CLOSURE_SLACK
check("a generic shortage is covered", artisans_after <= allowance + 1e-9, (artisans_after, allowance))
check("a generic shortage does not close everything",
      len(generic.operating) > 0 and len(generic_closed) < len(smiths + others), generic_closed)
check("nothing closed for craftsmen would be accepted by open with the same staff",
      all(not generic.open_venture(node_id, pay=False)[0] for node_id in generic_closed),
      [node_id for node_id in generic_closed if generic.open_venture(node_id, pay=False)[0]])

# --- a shortage of one trade does not close concerns that hold nothing of it
lone = crowded_sim(smiths, others)
lone.employees["smith"] = 0.0
lone.labour._resync_pools()
lone_closed = lone.close_unstaffed_ventures(lone.year)
check("losing every smith closes the smith concerns and only those",
      sorted(lone_closed) == sorted(smiths) and all(node_id in lone.operating for node_id in others),
      lone_closed)

# --- reopening after a closure does not restart the revenue ramp
ramp = crowded_sim(smiths, others)
ramp.state.scenario.year += 10
first = smiths[0]
ramp.state.projects.opened_year[first] = ramp.year - 5
before_ramp = ramp.venture_ramp(first)
ramp.close_work(first, ramp.CLOSED_FOR_STAFF)
ramp.open_venture(first, pay=False)
check("reopening keeps the original opening year for the ramp",
      ramp.venture_ramp(first) == before_ramp, (before_ramp, ramp.venture_ramp(first)))
_, reopen_message = (ramp.close_work(first, ramp.CLOSED_FOR_STAFF), ramp.open_venture(first, pay=False))[1]
check("a reopen reply does not promise a ramp it will not get",
      "over the first" not in reopen_message, reopen_message)

# --- one earnings figure: open and mothball quote what `ventures` shows
def figure_in(message, phrase):
	match = re.search(phrase + r" ([\d,]+)", message)
	return float(match.group(1).replace(",", "")) if match else None


quoted = crowded_sim([], others)
quoted.state.economy.output_factor *= 1.4
quoted.price_index *= 1.3
node_id = others[0]
quoted.operating.add(node_id)
quoted.state.scenario.year += 10
quoted.state.projects.opened_year[node_id] = quoted.year - 10
real_earnings = quoted.venture_real_earnings(node_id)
check("the real earnings figure differs from the tree's base figure in this set-up",
      abs(real_earnings - NODES[node_id]["rev"]) > 1.0, (real_earnings, NODES[node_id]["rev"]))
_ok, shut_message = quoted.mothball_work(node_id)
check("mothball quotes the real earnings figure, not the base one",
      figure_in(shut_message, "earning the") == round(real_earnings), (shut_message, real_earnings))
_ok, open_message = quoted.open_venture(node_id, pay=False)
check("open quotes the real fully-ramped earnings and upkeep",
      figure_in(open_message, "it earns") == round(quoted.venture_real_earnings(node_id, fully_ramped=True))
      and figure_in(open_message, "and costs") == round(quoted.venture_real_upkeep(node_id)), open_message)

# --- one reopening price after a deliberate shutdown, stated when shutting
priced = crowded_sim([], others)
priced.state.projects.opened_year[node_id] = priced.year
_ok, priced_message = priced.mothball_work(node_id)
stated = figure_in(priced_message, "for")
before_capital = priced.capital
priced.restore_work(node_id)
restore_paid = before_capital - priced.capital
priced.mothball_work(node_id)
before_capital = priced.capital
priced.open_venture(node_id)
open_paid = before_capital - priced.capital
check("open and restore charge the same after a mothball", abs(restore_paid - open_paid) < 0.01, (restore_paid, open_paid))
check("the mothball reply states that price", stated == round(open_paid), (priced_message, open_paid))
