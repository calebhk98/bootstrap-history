"""Hiring, training and commissioning a trade; wage pricing and its
forecast; the founder's own practice income; and a dead founder's effect on
all of it.

Regrouped from test_round8_fixes.py, test_round9.py and test_round10.py -
see CLAUDE.md's test-file reorganisation note. Checks moved verbatim; each
one's own comment explains the break it guards.
"""
from .harness import *  # noqa: F401,F403


# --- BREAK: the practice paid a third of the quoted figure with nothing
# anywhere saying so, because a granted node has no done_year and the revenue
# ramp pinned it at step one of three for ever. It is now a named constant,
# and the arithmetic is unchanged.
s_pr = sim()
_prac = sorted(s_pr._practice_set())
_expect = sum(NODES[node_id]["rev"] for node_id in _prac) * s_pr.PRACTICE_SHARE
check("the practice pays its share of the quoted figure, not a ramp step",
      abs(s_pr.revenue() - _expect) < 0.5, (s_pr.revenue(), _expect))
s_pr5 = sim()
for _ in range(6):
    s_pr5.step()
check("...and it does not grow into the full figure over the ramp years",
      abs(s_pr5.revenue() - _expect) < 0.5, (s_pr5.revenue(), _expect))
check("the ledger says why the practice pays less than the tree quotes",
      s_pr.practice_note() and "a third" in s_pr.practice_note(),
      s_pr.practice_note())
check("a concern you opened is NOT described as your practice",
      all(node_id in s_pr.granted for node_id in _prac), _prac[:3])

# --- BREAK: auto_train started engineers, chemists AND machinists against a
# thinner revenue than their wages, and turning the policy off did not stop
# what was in flight. No command anywhere could.
s_tr = sim(capital=200000.0)
ok_t, _ = s_tr.train("machinist", 3)
check("teaching a trade puts people in training", ok_t and s_tr.training, s_tr.training)
ok_f, note_f = s_tr.fire("machinist", 3)
check("dismissing a trade you are teaching cancels the apprenticeship",
      ok_f and not [record for record in s_tr.training if len(record) > 3 and record[2] == "machinist"],
      (note_f, s_tr.training))
check("...and says so, because what you paid to feed them is spent",
      note_f and "stopped teaching" in note_f, note_f)
s_tr2 = sim(capital=200000.0)
check("firing a trade you neither employ nor teach is still refused",
      s_tr2.fire("machinist", 1)[0] is False, s_tr2.fire("machinist", 1)[1])

# --- BREAK: `work` silently took the hours out of the practice. 500 hours as
# a scribe paid 80.1 and cost 58.3 of practice income the same instant.
_rw, _, _ = proto([{"cmd": "work", "trade": "scribe", "hours": 500}])
check("selling your hours says what it cost your own practice",
      _rw[0].get("it_cost_your_own_practice", 0) > 0.5, _rw[0])
check("...and says what you are actually up on the trade",
      abs((_rw[0]["earned"] - _rw[0]["it_cost_your_own_practice"])
          - _rw[0]["so_you_are_up"]) < 0.11, _rw[0])

# --- BREAK: engineers went from 781 a year to 1,094 and the premium appeared
# in the bill and nowhere else.
#
# MILLWRIGHT, NOT SMITH. This used to hire six smiths and call that "leaning
# hard" on the trade - true only because the old market_supply gave smith a
# pool of 11.25 people for the whole of Rome. The demographics fix (see
# labour.py's TOWN_POPULATION_REFERENCE/TRADE_DENSITY) gave smith, a "common"
# trade by its own wage-table note, a real town's worth instead - roughly
# 350 at full population scale, anchored on the Ostia fabri tignuarii album
# (CIL XIV 4569) - so six more smiths against that pool is correctly
# imperceptible now, which is the fix working, not a regression. Millwright
# ("the scarcest useful trade you can hire", per its own note) was
# deliberately left alone by that fix and still demonstrates the same
# mechanism this check is actually about.
s_wg = sim(capital=2000000.0)
_r0, _, _ = proto([{"cmd": "labour", "trade": "millwright"}])
_base = _r0[0]["trade"]["a_year_of_one"]
for _ in range(6):
    s_wg.hire("millwright", 3)
_dear = S._agent_dispatch(s_wg, NODES, {"cmd": "labour", "trade": "millwright"})["trade"]
check("leaning on a trade shows up in its quoted price, not only in the bill",
      _dear["a_year_of_one"] > _base, (_base, _dear["a_year_of_one"]))
check("...and says why, and what brings it back down",
      _dear.get("dearer_than_usual_by") and "supply" in (_dear.get("because") or ""),
      _dear.get("because"))

# --- BREAK (naive15/norse): "labour scholar" quoted 525 for a year of one
# scholar, the player hired one, and the standing wage bill came to 847.92 -
# 61% more - because that one hire bid labour_price_factor up for every
# scholar they then had, not only the new one. The quote and the bill were
# never inconsistent (both compute the same formula at the instant each is
# read); what was missing is a FORECAST: what hiring is about to do to the
# price, shown before the player commits, not just the market as it stands.
s_fc = sim(civ="norse_900ad", capital=None)
s_fc.capital = 560.0
_fc0 = S._agent_dispatch(s_fc, NODES, {"cmd": "labour", "trade": "scholar"})["trade"]
check("the quote for a scarce trade forecasts what hiring one now would "
      "make EVERY one of that trade cost - not just today's market price",
      _fc0.get("hiring_moves_the_price") is True
      and _fc0["a_year_of_one_after_you_hire_one"] > _fc0["a_year_of_one"],
      (_fc0.get("a_year_of_one"), _fc0.get("a_year_of_one_after_you_hire_one")))
check("...and it is the real forecast, not a guess: hiring one for real "
      "lands within a rounding error of the number just quoted",
      abs(S._agent_dispatch(s_fc, NODES,
          {"cmd": "hire", "trade": "scholar", "n": 1})["annual_wage_bill"]
          - _fc0["a_year_of_one_after_you_hire_one"]) < 1.0,
      (_fc0["a_year_of_one_after_you_hire_one"],))
_fc_txt = _protocol.render_pretty(
    "labour", S._agent_dispatch(s_fc, NODES, {"cmd": "labour", "trade": "scholar"}))
check("...and the readable screen states the forecast plainly, not just in "
      "the JSON",
      "MOVES THE PRICE" in _fc_txt and "not just the new hire" in _fc_txt,
      _fc_txt)
# An abundant trade is not put on notice by one hire - the forecast has to
# be selective, not a blanket disclaimer on every quote.
s_fc2 = sim(capital=2000000.0)
_fc_ab = S._agent_dispatch(s_fc2, NODES, {"cmd": "labour", "trade": "labourer"})["trade"]
check("an abundant trade's quote is not flagged as price-moving from one hire",
      not _fc_ab.get("hiring_moves_the_price"), _fc_ab)

# --- BREAK: engineers count as SCHOLARS and cannot supervise a workshop. A
# play tester was poor for thirty years over it; swapping three engineers for
# three artisans took their net from -155 a year to +4,164.
_rv, _, _ = proto([{"cmd": "ventures"}])
check("the concerns screen says scholars and craftsmen are not interchangeable",
      "scholar cannot watch a workshop"
      in str(_rv[0].get("these_are_not_interchangeable")),
      _rv[0].get("these_are_not_interchangeable"))
_re, _, _ = proto([{"cmd": "labour", "trade": "engineer"}])
check("...and a trade says which of the two it is",
      _re[0]["trade"].get("kind") == "scholar", _re[0]["trade"].get("kind"))

# --- BREAK (naive15/rome): "`train <trade> <n>` creates the trade and starts
# teaching specific people, but does NOT put them on your payroll ... the
# confirmation message after `train` says 'training: 2 machinists will be
# ready in 141' which reads like they'll just show up working." Verified
# against the engine itself (core.py step(), section 0): trained people in a
# real trade ARE added to self.employees automatically the year they mature
# - no separate `hire` is needed for THEM - but nothing said so, and nothing
# said they cannot work a day before that year either.
s_tr = sim(capital=100000.0)
_ok_tr, _msg_tr = s_tr.train("machinist", 2, None)
check("the training confirmation says what is STILL needed: nothing, for "
      "these apprentices - they join staff on their own, no 'hire' required",
      _ok_tr and "join your staff automatically" in _msg_tr
      and "no 'hire' needed" in _msg_tr, _msg_tr)
check("the completion year is described as an annual-resolution boundary, "
      "not ambiguously as 'ready in' that year",
      "finish training during" in _msg_tr and "annual resolution" in _msg_tr
      and "ready in" not in _msg_tr, _msg_tr)
check("...and says what they cannot do yet: a day of the work, before the "
      "year named",
      _ok_tr and "cannot do a day of the work" in _msg_tr, _msg_tr)
_ready_year = s_tr.year + 2
for _ in range(3):
    s_tr.step()
check("...and this is not just a promise: they really are on the books, "
      "unprompted, by the year named",
      s_tr.employees.get("machinist", 0.0) >= 1.999, s_tr.employees.get("machinist"))

# --- BREAK: three places said the town could field 8,750 scribe-hours a year,
# and commissioning the full 8,750 ON TOP of the standing pool let a
# 10,000-hour project finish. Real ceiling 17,500; every one of the three
# statements false.
# TWO CHANNELS, each bounded and each named. Hiring draws on the people who
# live here; a commission is a job placed with an outside shop, which
# subcontracts - dearer per hour, and bounded in turn by what the local trade
# can spare. Stated as ONE ceiling of 8,750 it was false (the real one was
# 17,500); collapsed into one it made commissioning buy byte-identical
# progress and be pointless. Both statements have to be on the screen.
s_cm = sim(capital=5000000.0)
_ceiling = s_cm.market_supply("scribe")
s_cm.commission("scribe", _ceiling * 0.9)
check("commissioning does not raise how many of a trade LIVE here",
      abs(s_cm.market_supply_split("scribe")[0]
          - sim(capital=5000000.0).market_supply_split("scribe")[0]) < 1e-6,
      s_cm.market_supply_split("scribe")[0])
check("...and it does add hours you can actually call on",
      s_cm.hours_you_can_call_on("scribe") > _ceiling, 
      (_ceiling, s_cm.hours_you_can_call_on("scribe")))
check("...and you cannot commission past what the trade here can spare",
      s_cm.commission("scribe", _ceiling)[0] is False,
      s_cm.commission("scribe", _ceiling)[1])
_rc2, _, _ = proto([{"cmd": "labour", "trade": "scribe"}])
check("...and `labour` names both channels, not one ceiling",
      _rc2[0]["trade"].get("hours_you_could_still_commission") is not None
      and _rc2[0]["trade"].get("hours_available_to_you_in_all")
      >= _rc2[0]["trade"].get("hours_the_market_can_supply"),
      _rc2[0]["trade"])

# --- BREAK: a trade you taught counts as existing for ever, so once the last
# machinist had died of old age auto_train skipped every node that needed one
# and nobody was ever taught again. A Rome run built 829 technologies, sat on
# 31.9M denarii, and could not begin precision_three_plate - which gates
# master_screw, the screw lathe and ninety-nine of the hundred and forty-six
# nodes on the road to the goal.
s_rt = sim(capital=2000000.0, manual=False)
s_rt.trades_created.add("machinist")          # taught once, long ago
s_rt.employees.pop("machinist", None)
s_rt._resync_pools()
check("a trade taught and then lost counts as gone, not as available",
      s_rt.trade_available("machinist")
      and s_rt.market_supply("machinist") <= 0.0,
      (s_rt.trade_available("machinist"), s_rt.market_supply("machinist")))
for _ in range(6):
    s_rt.step()
check("...and the engine teaches it again rather than skipping every node "
      "that needs it",
      s_rt.market_supply("machinist") > 0
      or s_rt._trade_headcount_pending("machinist") > 0,
      (s_rt.market_supply("machinist"),
       s_rt._trade_headcount_pending("machinist")))
# But not every year: teaching two costs about 900 of a 2,000-hour year.
# FOUR SECONDS: forty years of an optimizer run to watch a cooldown that only
# has meaning across decades. Per TRADE: teaching four different trades over
# forty years is fine; teaching the same one four times is the treadmill that
# cost three Rome seeds most of what they built.
def _reteaching_is_once_a_generation():
    household = sim(capital=2000000.0, manual=False)
    household.trades_created.add("machinist")
    per_trade = {}
    for _ in range(40):
        before = dict(getattr(household, "last_taught", {}))
        household.step()
        for trade, year_taught in getattr(household, "last_taught", {}).items():
            if before.get(trade) != year_taught:
                per_trade[trade] = per_trade.get(trade, 0) + 1
    return (all(value <= 40 // household.RETEACH_EVERY + 1 for value in per_trade.values()),
            per_trade)

slow_check("...and no more than once a generation FOR THE SAME TRADE",
           _reteaching_is_once_a_generation)

# --- BREAK: `train machinist 4` quietly ate 1,800 of a play tester's 2,000
# founder-hours and, with nothing left to supervise with, closed a dozen
# concerns as a side effect. The reply was six words about two years' time.
_rt3, _, _ = proto([{"cmd": "train", "trade": "machinist", "n": 4}], kit="absurd")
check("teaching says what it took out of your year",
      "of your own hours" in json.dumps(_rt3[0])
      and "left this year" in json.dumps(_rt3[0]), _rt3[0])
check("...and what it cost to keep them while they learn",
      "denarii" in json.dumps(_rt3[0]), _rt3[0])

# --- BREAK: a dead founder kept playing - starting projects, hiring staff,
# and his surgical practice went on taking fees for eleven years.
s_dd = sim(capital=50000.0)
_alive = s_dd.revenue()
s_dd.founder_alive = False
check("a dead physician has no practice",
      _alive > 0 and s_dd.revenue() == 0.0, (_alive, s_dd.revenue()))
check("...and cannot sell hours he does not have",
      s_dd.work_for_wages("scholar", 100)[0] == 0.0,
      s_dd.work_for_wages("scholar", 100)[1])
check("...and cannot take anyone on with no deputy to direct them",
      S._agent_dispatch(s_dd, NODES,
                        {"cmd": "hire", "trade": "smith", "n": 1}).get("ok") is False,
      S._agent_dispatch(s_dd, NODES, {"cmd": "hire", "trade": "smith", "n": 1}))
