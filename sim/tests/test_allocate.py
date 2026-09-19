"""allocate: regression checks, run individually with `--only allocate`."""
from .harness import *  # noqa: F401,F403

# ===========================================================================
# `allocate` - a standing instruction for the player's own year of hours.
# ===========================================================================
# The player's own words: "if I only wanted to do manual work for 100 hours,
# research item A for 500 and item B for 1400, I should be able to do that" -
# set once, not retyped every turn, in a game played over hundreds of them.
# Every check below drives the real allocator (core.py step()) directly,
# the same one `portfolio` reads back from - never a second formula that
# could disagree with what actually happened.

def _zero_lab(n):
    return {trade: 0.0 for trade in n.get("lab", {})}


# --- a directed project jumps the queue, ahead of higher-`order` work that
# was never given a standing instruction.
s = sim(capital=1e7)
_kA, _kB = "academy_network", "corpus_written"
s.order = [_kA, _kB]
for _k in (_kA, _kB):
    _n = NODES[_k]
    s.active[_k] = dict(ph_left=float(_n["ph"]), yrs=0.0, spent=0.0,
                        cost_left=0.0, lab_left=_zero_lab(_n))
s.hour_allocations[_kB] = 500.0
s.step()
check("a standing allocation gets its project the hours it asked for, even "
      "though an undirected project ranks ahead of it in `order`",
      s.active[_kB]["hours_offered_this_year"] == 500.0,
      s.active[_kB]["hours_offered_this_year"])
check("...and the higher-`order` project gets only what is left of the "
      "pool once the standing order has taken its share, not the whole "
      "pool first",
      s.active[_kA]["hours_offered_this_year"] == s.director_pool() - 500.0,
      s.active[_kA]["hours_offered_this_year"])
check("`portfolio`/`state` read the standing order back from the exact "
      "field step() wrote, never a second guess at it",
      s.active[_kB].get("hours_directed_this_year") == 500.0
      and s.active[_kA].get("hours_directed_this_year") is None,
      (s.active[_kB].get("hours_directed_this_year"),
       s.active[_kA].get("hours_directed_this_year")))

# --- a directive bigger than the project's own pace is not silently
# dropped: the rest flows to other active work, and the player is told, by
# name, that it happened and why - a calendar floor, not "your hours".
s = sim(capital=1e7)
_kC, _kD = "school_founded", "academy_network"
s.order = [_kC, _kD]
_nC, _nD = NODES[_kC], NODES[_kD]
# almost done: its own pace this year is small whatever the pool can spare.
s.active[_kC] = dict(ph_left=30.0, yrs=0.0, spent=0.0, cost_left=0.0,
                     lab_left=_zero_lab(_nC))
s.active[_kD] = dict(ph_left=float(_nD["ph"]), yrs=0.0, spent=0.0,
                     cost_left=0.0, lab_left=_zero_lab(_nD))
s.hour_allocations[_kC] = 1400.0
_before = len(s.log)
s.step()
_pace_cap = max(30.0, _nC["ph"] / max(_nC["yrs"], 1.0))
check("a directive bigger than a project's own calendar-floor pace only "
      "offers it that pace, not the whole directive",
      s.active[_kC]["hours_offered_this_year"] == round(_pace_cap, 1),
      s.active[_kC]["hours_offered_this_year"])
check("...and the hours the directive could not place there are not lost: "
      "the other active project actually received them this same year",
      s.active[_kD]["hours_offered_this_year"]
      == s.director_pool() - s.active[_kC]["hours_offered_this_year"],
      s.active[_kD]["hours_offered_this_year"])
_new = [message for _, message in s.log[_before:]]
check("...and the player is told BY NAME that the directive could not be "
      "fully honoured, and that the reason is a pace/calendar floor, not "
      "a refusal to give it hours",
      any("DIRECTED HOURS UNUSED" in message and _nC["name"] in message
          and "calendar floor" in message for message in _new),
      _new)

# --- two standing orders together asking for more than the whole pool: the
# one that comes up short is told the real reason is the pool, not itself.
s = sim(capital=1e7)
_kE, _kF = "academy_network", "corpus_written"
s.order = [_kE, _kF]
_nE, _nF = NODES[_kE], NODES[_kF]
s.active[_kE] = dict(ph_left=float(_nE["ph"]), yrs=0.0, spent=0.0,
                     cost_left=0.0, lab_left=_zero_lab(_nE))
s.active[_kF] = dict(ph_left=float(_nF["ph"]), yrs=0.0, spent=0.0,
                     cost_left=0.0, lab_left=_zero_lab(_nF))
s.hour_allocations[_kE] = 1400.0
s.hour_allocations[_kF] = 1000.0
_before = len(s.log)
s.step()
check("the first of two over-committed standing orders gets its directive "
      "in full",
      s.active[_kE]["hours_offered_this_year"] == 1400.0,
      s.active[_kE]["hours_offered_this_year"])
check("...and the second gets only what the pool had left, named as the "
      "pool running out, not as anything wrong with that project",
      any("DIRECTED HOURS UNUSED" in message and "before this one's turn came" in message
          for _, message in s.log[_before:]),
      [message for _, message in s.log[_before:]])

# --- a player who never calls `allocate` sees the ordinary priority order
# and nothing else: with an empty hour_allocations, the sort key collapses
# to the same single bucket every project has always sorted into.
s = sim(capital=1e7)
_order3 = ["academy_network", "corpus_written", "school_founded"]
s.order = list(_order3)
for _k in _order3:
    _n = NODES[_k]
    s.active[_k] = dict(ph_left=float(_n["ph"]), yrs=0.0, spent=0.0,
                        cost_left=0.0, lab_left=_zero_lab(_n))
s.step()
check("with nothing ever directed, hours still go out strictly by `order` "
      "rank, exactly as before `allocate` existed",
      [s.active[node_id]["pool_rank_this_year"] for node_id in _order3] == [1, 2, 3],
      [s.active[node_id]["pool_rank_this_year"] for node_id in _order3])

# --- `allocate` itself: refuses a project that is not active yet, refuses
# an id that does not exist, sets, reports back, and clears.
s = sim(capital=1e7)
_r = S._agent_dispatch(s, NODES, {"cmd": "allocate", "id": "academy_network",
                                  "hours": 300})
check("allocate refuses a directive on a project that has not been "
      "started - there is nothing active for it to apply to yet",
      not _r["ok"] and "academy_network" in _r["error"]
      and "not active" in _r["error"], _r)
_r = S._agent_dispatch(s, NODES, {"cmd": "allocate", "id": "not_a_real_node",
                                  "hours": 300})
check("allocate refuses an id that does not exist at all",
      not _r["ok"] and "unknown node id" in _r["error"], _r)
s.active["academy_network"] = dict(ph_left=2500.0, yrs=0.0, spent=0.0,
                                   cost_left=0.0, lab_left={})
_r = S._agent_dispatch(s, NODES, {"cmd": "allocate", "id": "academy_network",
                                  "hours": 300})
check("allocate accepts a directive on an active project and echoes it back",
      _r["ok"] and _r.get("hours_a_year") == 300.0, _r)
_r = S._agent_dispatch(s, NODES, {"cmd": "allocate"})
check("bare allocate lists every standing order currently in hand",
      _r["ok"] and _r["allocations"] == [{"id": "academy_network",
                                          "hours_a_year": 300.0}], _r)
_r = S._agent_dispatch(s, NODES, {"cmd": "allocate", "id": "academy_network",
                                  "hours": 0})
check("hours 0 clears a standing order rather than setting it to zero "
      "forever",
      _r["ok"] and _r.get("cleared") == "academy_network"
      and "academy_network" not in s.hour_allocations, _r)
_r = S._agent_dispatch(s, NODES, {"cmd": "allocate"})
check("...and it is actually gone from the list, not just zeroed in place",
      _r["ok"] and _r["allocations"] == "none", _r)

# --- the standing "work" directive: sells hours for wages every year on
# its own, reusing work_for_wages (labour.py) rather than a second way to
# pay the founder, and tops up a turn where some of it was already sold by
# hand instead of selling the whole directive again on top.
s = sim(capital=1e7)
_r = S._agent_dispatch(s, NODES, {"cmd": "allocate", "id": "work",
                                  "hours": 100, "trade": "labourer"})
check("allocate accepts a standing work-for-wages order naming a trade",
      _r["ok"] and _r.get("trade") == "labourer", _r)
# The rate work_for_wages itself charges for a labourer-hour (labour.py),
# read back BEFORE either call moves reputation or the indices, rather
# than re-derived: 100 hours total at that rate is what a topped-up
# directive should earn, whether 40 of them were sold by hand first or
# the whole 100 were left to the standing order.
_rate_per_hour = (S.ANNUAL_WAGE.get("labourer", 375.0) / s.HOURS_PER_PERSON_YEAR
                 * s.price_index * s.wage_index
                 * (1.0 + min(0.5, s.reputation / 200.0)))
_pay_by_hand, _err = s.work_for_wages("labourer", 40.0)
s.step()
check("a standing work order tops up to the full directive rather than "
      "selling it twice on top of hours already sold by hand this year",
      abs(s.wages_earned - 100.0 * _rate_per_hour) < 0.05,
      (s.wages_earned, 100.0 * _rate_per_hour))
check("...and the standing order's own hour tally resets for the next "
      "year exactly like an ordinary `work` call does",
      s.wage_hours_this_year == 0.0, s.wage_hours_this_year)

# --- a standing order persists across a save and a load, the same as
# `policy` does, rather than silently reverting to "let the allocator "
# decide" on every resume.
s = sim(capital=1e7)
s.hour_allocations["academy_network"] = 321.0
s.hour_allocations["work"] = 77.0
s.work_trade = "scribe"
_save_path = os.path.join(tempfile.gettempdir(), "rome_allocate_save_test.json")
_protocol.save_state(s, _save_path)
s2 = sim(capital=1e7)
_protocol.load_state(s2, _save_path)
os.remove(_save_path)
check("a standing project directive survives a save and a load",
      s2.hour_allocations.get("academy_network") == 321.0,
      s2.hour_allocations)
check("...and so does a standing work-for-wages directive and its trade",
      s2.hour_allocations.get("work") == 77.0 and s2.work_trade == "scribe",
      (s2.hour_allocations.get("work"), s2.work_trade))

