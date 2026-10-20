"""allocate: a standing instruction for the player's own year of hours.

The rules are tested on built inputs: the queue the hours are drawn in (`hour_offer.priority_queue`), what one
project is offered and why a directive can go unmet (`hour_offer`), and the `allocate` command on a stand-in
for the household. Three named scenarios run the real allocator (`_run_seat_work`), a save and load, and the
standing work order on a game."""
from types import SimpleNamespace

from .harness import *  # noqa: F401,F403
from sim.engine import hour_offer
from sim.refusal import cause_of
from sim.ui.proto.dispatch_labour import _cmd_allocate

# --- the queue: a directed project jumps the queue, ahead of higher-`order` work never given a directive.
queue_order = ["alpha", "beta", "gamma"]
check("a project with a standing allocation draws before higher-ranked undirected ones",
      hour_offer.priority_queue(["alpha", "beta", "gamma"], queue_order, {"beta": 500.0}) == ["beta", "alpha", "gamma"])
check("with nothing ever directed, projects draw strictly by `order` rank",
      hour_offer.priority_queue(["gamma", "alpha", "beta"], queue_order, {}) == ["alpha", "beta", "gamma"])
check("a zero allocation directs nothing",
      hour_offer.priority_queue(["alpha", "beta"], queue_order, {"beta": 0.0}) == ["alpha", "beta"])
check("directed projects keep `order` rank among themselves, and a project missing from `order` draws last",
      hour_offer.priority_queue(["stranger", "gamma", "alpha"], queue_order, {"gamma": 1.0, "alpha": 1.0}) == ["alpha", "gamma", "stranger"]
      and hour_offer.priority_queue(["stranger", "alpha"], queue_order, {}) == ["alpha", "stranger"])

# --- what one project is offered: a directive is a ceiling, never a floor.
check("a standing allocation gets the hours it asked for when pool and pace allow",
      hour_offer.hours_offered(1900.0, 3000.0, 500.0, 1.0) == 500.0)
check("an undirected project is offered the lesser of the pool left and its own pace",
      hour_offer.hours_offered(1900.0, 700.0, None, 1.0) == 700.0 and hour_offer.hours_offered(300.0, 700.0, 0.0, 1.0) == 300.0)
check("a directive bigger than the project's own pace only offers it that pace",
      hour_offer.hours_offered(1900.0, 30.0, 1400.0, 1.0) == 30.0)
check("a directive bigger than what is left of the pool offers what is left",
      hour_offer.hours_offered(600.0, 3000.0, 1000.0, 1.0) == 600.0)
check("a shortage throttle scales the offer", hour_offer.hours_offered(1900.0, 3000.0, 1000.0, 0.5) == 500.0)

# two standing orders asking for more than the whole pool, drawn in queue order
pool = 1900.0
first = hour_offer.hours_offered(pool, 3000.0, 1400.0, 1.0)
second = hour_offer.hours_offered(pool - first, 3000.0, 1000.0, 1.0)
check("of two over-committed standing orders the first gets its directive in full and the second what the pool had left",
      first == 1400.0 and second == pool - 1400.0, (first, second))
check("the second is told the pool ran out, not that anything is wrong with that project",
      hour_offer.unmet_directive_cause(1000.0, second, 3000.0, 1.0, None) == "pool_claimed")

# --- why a directive goes unmet
check("a directive met in full, or within an hour of it, has no cause",
      hour_offer.unmet_directive_cause(500.0, 500.0, 3000.0, 1.0, None) is None
      and hour_offer.unmet_directive_cause(500.0, 499.5, 3000.0, 1.0, None) is None)
check("no directive has no cause", hour_offer.unmet_directive_cause(None, 0.0, 30.0, 1.0, None) is None
      and hour_offer.unmet_directive_cause(0.0, 0.0, 30.0, 1.0, None) is None)
check("a directive past the project's own pace is named as its own pace",
      hour_offer.unmet_directive_cause(1400.0, 30.0, 30.0, 1.0, None) == "own_pace")
check("a directive the pace could carry, cut by a binding shortage, is named as the shortage",
      hour_offer.unmet_directive_cause(1000.0, 500.0, 3000.0, 0.5, "grain") == "shortage_throttle")
check("a throttle with no binding shortage named is not called a shortage",
      hour_offer.unmet_directive_cause(1000.0, 500.0, 3000.0, 0.5, None) == "pool_claimed")
check("a throttle within two percent is not called a shortage",
      hour_offer.unmet_directive_cause(1000.0, 500.0, 3000.0, 0.99, "grain") == "pool_claimed")

# --- the `allocate` command: refuses a project not active, refuses an unknown id, sets, reports, clears.
known_nodes = {"academy_network": {"name": "Academy Network"}}


def standing(household_allocations=None, active=None):
    return SimpleNamespace(hour_allocations=household_allocations if household_allocations is not None else {},
                           active=active if active is not None else {}, work_trade=None)


household = standing()
reply = _cmd_allocate(household, known_nodes, {"cmd": "allocate", "id": "academy_network", "hours": 300}, None)
check("allocate refuses a directive on a project that has not been started",
      not reply["ok"] and cause_of(reply["error"]) == "project_not_active", reply)
reply = _cmd_allocate(household, known_nodes, {"cmd": "allocate", "id": "not_a_real_node", "hours": 300}, None)
check("allocate refuses an id that does not exist at all",
      not reply["ok"] and cause_of(reply["error"]) == "unknown_node", reply)
household.active["academy_network"] = {}
reply = _cmd_allocate(household, known_nodes, {"cmd": "allocate", "id": "academy_network", "hours": 300}, None)
check("allocate accepts a directive on an active project, echoes it back and keeps it",
      reply["ok"] and reply.get("hours_a_year") == 300.0 and household.hour_allocations == {"academy_network": 300.0}, reply)
reply = _cmd_allocate(household, known_nodes, {"cmd": "allocate"}, None)
check("bare allocate lists every standing order currently in hand",
      reply["ok"] and reply["allocations"] == [{"id": "academy_network", "hours_a_year": 300.0}], reply)
reply = _cmd_allocate(household, known_nodes, {"cmd": "allocate", "id": "academy_network", "hours": 0}, None)
check("hours 0 clears a standing order rather than setting it to zero forever",
      reply["ok"] and reply.get("cleared") == "academy_network" and "academy_network" not in household.hour_allocations, reply)
reply = _cmd_allocate(household, known_nodes, {"cmd": "allocate"}, None)
check("...and it is gone from the list, not zeroed in place", reply["ok"] and reply["allocations"] == "none", reply)
reply = _cmd_allocate(household, known_nodes, {"cmd": "allocate", "id": "academy_network", "hours": -5}, None)
check("a negative or non-numeric number of hours is refused", not reply["ok"]
      and not _cmd_allocate(household, known_nodes, {"cmd": "allocate", "id": "academy_network", "hours": "lots"}, None)["ok"], reply)


def _zero_lab(node):
    return {trade: 0.0 for trade in node.get("lab", {})}


# --- scenario: the real allocator gives a directed project its hours first, and `portfolio` reads them back
s = sim(capital=1e7)
_kA, _kB = "academy_network", "corpus_written"
s.order = [_kA, _kB]
s.project_resource_throttle = lambda node_id: 1.0   # the order of hours is under test, not what the market has in stock
for _k in (_kA, _kB):
    _n = NODES[_k]
    s.active[_k] = dict(ph_left=float(_n["ph"]), yrs=0.0, spent=0.0, cost_left=0.0, lab_left=_zero_lab(_n))
s.hour_allocations[_kB] = 500.0
s._run_seat_work()
check("scenario: the allocator offers a directed project its hours first, the higher-ranked one what is left of the "
      "pool, and the state reads the directive back from the field step wrote",
      s.active[_kB]["hours_offered_this_year"] == 500.0
      and s.active[_kA]["hours_offered_this_year"] == s.labour.director_pool() - 500.0
      and s.active[_kB].get("hours_directed_this_year") == 500.0 and s.active[_kA].get("hours_directed_this_year") is None,
      (s.active[_kB]["hours_offered_this_year"], s.active[_kA]["hours_offered_this_year"]))

# --- scenario: a standing order persists across a save and a load, the same as `policy` does
s = unopened_sim(capital=1e7)
s.hour_allocations["academy_network"] = 321.0
s.hour_allocations["work"] = 77.0
s.work_trade = "scribe"
_save_path = os.path.join(tempfile.gettempdir(), "rome_allocate_save_test.json")
_protocol.save_state(s, _save_path)
s2 = unopened_sim(capital=1e7)
_protocol.load_state(s2, _save_path)
os.remove(_save_path)
check("scenario: standing project and work-for-wages directives, and the work trade, survive a save and a load",
      s2.hour_allocations.get("academy_network") == 321.0 and s2.hour_allocations.get("work") == 77.0
      and s2.work_trade == "scribe", (s2.hour_allocations, s2.work_trade))

# --- scenario: the standing "work" directive tops up hours already sold by hand, then resets for the next year
s = unopened_sim(capital=1e7)   # legacy: the earnings are compared with the engine's own wage-table rate
# Fed by its own farm, so no hunger reprices wages during the step.
s.farm_land.quality, s.farm_land.hectares = 1.3, s.farm_land.hectares * 2.0
_r = S._agent_dispatch(s, NODES, {"cmd": "allocate", "id": "work", "hours": 100, "trade": "labourer"})
_rate_per_hour = (S.ANNUAL_WAGE.get("labourer", 375.0) / s.HOURS_PER_PERSON_YEAR
                  * s.price_index * s.wage_index
                  * (1.0 + min(0.5, s.reputation / 200.0)))
_pay_by_hand, _err = s.labour.work_for_wages("labourer", 40.0)
s.step()
check("scenario: a standing work order naming a trade tops up to the full directive rather than selling it twice, "
      "and its hour tally resets for the next year",
      _r["ok"] and _r.get("trade") == "labourer"
      and abs(s.wages_earned - 100.0 * _rate_per_hour) < 0.01 * 100.0 * _rate_per_hour and s.wage_hours_this_year == 0.0,
      (_r, s.wages_earned, 100.0 * _rate_per_hour, s.wage_hours_this_year))
