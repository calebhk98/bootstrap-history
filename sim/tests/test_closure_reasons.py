"""closure_reasons: a closed work records why and since when, and only its own cause clears it."""
from .harness import *  # noqa: F401,F403

NODE_ID = "cementation_steel"


def staffed_sim():
	# A running concern that needs a craftsman to supervise it.
	test_sim = sim(capital=1_000_000.0)
	test_sim.done.update(NODES[NODE_ID]["pre"])
	test_sim.done.add(NODE_ID)
	test_sim._done_changed()
	test_sim.employees["artisan"] = 6.0
	test_sim._resync_pools()
	test_sim.open_venture(NODE_ID)
	return test_sim


def staff_close(test_sim):
	test_sim.employees["artisan"] = 0.0
	test_sim._resync_pools()
	closed = test_sim.close_unstaffed_ventures(test_sim.year)
	test_sim.employees["artisan"] = 6.0
	test_sim._resync_pools()
	return closed


def restore_price(test_sim):
	before = test_sim.capital
	ok, message = test_sim.restore_work(NODE_ID)
	return ok, message, before - test_sim.capital


def age_years(test_sim, years):
	test_sim.state.scenario.year += years


# --- restoring after a staffing closure clears it, so a later manual
# mothball does not inherit the old staffing age
s_stale = staffed_sim()
check("set-up: losing the keeper closes the concern for staffing",
      staff_close(s_stale) == [NODE_ID])
check("the staffing closure names its reason",
      (s_stale.closure_of(NODE_ID) or {}).get("reason") == "staff", s_stale.closure_of(NODE_ID))
ok_first, _, first_price = restore_price(s_stale)
check("restoring it works", ok_first)
check("restoring clears the staffing closure", s_stale.closure_of(NODE_ID) is None
      and NODE_ID not in s_stale.shut_for_staff, s_stale.shut_for_staff)
age_years(s_stale, 30)
s_stale.mothball_work(NODE_ID)
check("a manual mothball records a manual closure with its own year",
      s_stale.closure_of(NODE_ID) == {"reason": "manual", "year": s_stale.year},
      s_stale.closure_of(NODE_ID))
ok_again, message_again, _ = restore_price(s_stale)
check("restoring a manual mothball does not blame an old staffing closure",
      ok_again and "staffing" not in message_again and "years" not in message_again,
      message_again)

# --- a manual mothball right after a staffing restore gets no staffing discount
s_fresh = staffed_sim()
s_fresh.mothball_work(NODE_ID)
_, _, manual_price = restore_price(s_fresh)
s_quick = staffed_sim()
staff_close(s_quick)
restore_price(s_quick)
s_quick.mothball_work(NODE_ID)
_, _, quick_price = restore_price(s_quick)
check("a manual mothball right after a staffing restore pays the same as any manual one",
      abs(quick_price - manual_price) < 1e-6, (quick_price, manual_price))
check("...while a real staffing closure is discounted against it",
      first_price < manual_price, (first_price, manual_price))

# --- the automatic reopen only answers staffing closures
s_manual = staffed_sim()
staff_close(s_manual)
restore_price(s_manual)
s_manual.mothball_work(NODE_ID)
check("restaffing does not reopen a work the player shut on purpose",
      s_manual.reopen_restaffed_ventures(s_manual.year) == []
      and NODE_ID in s_manual.mothballed, s_manual.closure_of(NODE_ID))

# --- a closure is only cleared by the reason that resolves it
check("clearing a staffing closure leaves a manual closure alone",
      s_manual.clear_closure(NODE_ID, "staff") is False
      and s_manual.closure_of(NODE_ID)["reason"] == "manual")
check("clearing with no reason removes whatever closure there is",
      s_manual.clear_closure(NODE_ID) is True and s_manual.closure_of(NODE_ID) is None)

# --- opening it directly also clears the closure
s_open = staffed_sim()
staff_close(s_open)
ok_open, _ = s_open.open_venture(NODE_ID)
check("opening a staffing-closed concern clears its closure",
      ok_open and s_open.closure_of(NODE_ID) is None)

# --- a record with no closed work behind it does not count
s_orphan = staffed_sim()
s_orphan.state.projects.closures[NODE_ID] = {"reason": "staff", "year": s_orphan.year}
check("a closure record for a work that is running is ignored",
      s_orphan.closure_of(NODE_ID) is None)

# --- save/load round-trips the closure
s_save = staffed_sim()
staff_close(s_save)
save_path = os.path.join(HERE, "_test_closure_reasons_save.json")
S.save_state(s_save, save_path)
s_loaded = S.Sim(NODES, ORDER, random.Random(1), events=False, manual=True,
                 civ=S.load_civ("rome_100ad"))
s_loaded.goal, s_loaded.done_year = GOAL, {}
S.load_state(s_loaded, save_path)
os.remove(save_path)
check("a closure's reason and year survive save and load",
      s_loaded.closure_of(NODE_ID) == s_save.closure_of(NODE_ID)
      and s_loaded.closure_of(NODE_ID)["reason"] == "staff", s_loaded.closure_of(NODE_ID))
