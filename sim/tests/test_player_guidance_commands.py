"""The commands that tell a player what is going on and what to do
next: `available`, `why` (including its FULL CHAIN figures and its
substitution-group wording), `stuck`, `path`, `help`, the end-of-run report,
and the small refusal-message fixes (a mistyped id, an absurd quantity, a
bribe too small to matter).

Regrouped from test_round8_fixes.py, test_round9.py and test_round10.py -
see CLAUDE.md's test-file reorganisation note. Checks moved verbatim; each
one's own comment explains the break it guards.
"""
from .harness import *  # noqa: F401,F403


# --- BREAK: `available` carried nine numbers and not one of them was the
# staff, so six projects picked on cost and hours all waited on people.
s_av = sim()
_av, _, _ = proto([{"cmd": "available", "find": "flax"}])
_rows = _av[0].get("available") or []
check("available says what standing staff a project needs",
      _rows and any(row.get("needs_staff") for row in _rows),
      [(row["id"], row.get("needs_staff")) for row in _rows][:3])
# The marker uses the SAME measure the gate uses - the founder's own hands and
# anything under contract included - so on turn one, when the founder can do a
# one-craftsman job themselves, nothing is starred. A break tester read "* means
# the work waits" beside projects that built at full speed with nobody hired.
from sim.engine.protocol import _short_of_staff
_s_star = sim()
check("...and marks exactly the ones the start gate would refuse for staff",
      all(bool(row.get("short_of_staff"))
          == (NODES[row["id"]]["art"] > _s_star.craft_hands_available() + 1e-9
              or NODES[row["id"]]["sch"] > _s_star.effective_scholars() + 1e-9)
          for row in _rows),
      [(row["id"], row.get("short_of_staff"), NODES[row["id"]]["art"],
        _s_star.craft_hands_available()) for row in _rows][:3])
_big = [node_id for node_id in sorted(NODES) if NODES[node_id]["art"] > 20][:1]
if _big:
    check("...and a job wanting twenty craftsmen IS starred on turn one",
          _short_of_staff(_s_star, NODES[_big[0]]), _big[0])
_av2, _, _ = proto([{"cmd": "available", "find": "zzzznosuchthing"}])
check("a search that matches nothing says so instead of printing '1-0'",
      _av2[0].get("nothing_matched") and "1-0" not in str(_av2[0].get("showing")),
      _av2[0].get("showing"))
from sim.engine.protocol import render_pretty as _RP
_pretty = _RP("available", _av2[0])
check("...and the empty result prints no column headings over no rows",
      "COST" not in _pretty and "matches" in _pretty, _pretty[:120])

# --- BREAK: with knowing and running split apart, nothing said which one a
# prerequisite wants.
# One node with its prerequisites met, one without: both have to say which
# state a prerequisite wants, since knowing and running became separate.
_wy, _, _ = proto([{"cmd": "why", "id": "horse_collar"},
                   {"cmd": "why", "id": GOAL}])
_wp = "\n".join(_RP("why", x) for x in _wy)
check("why states that a prerequisite must be finished, and stays finished",
      "FINISHED" in _wp or "finished counts for ever" in _wp,
      [line for line in _wp.splitlines() if "PREREQ" in line][:3])

# --- BREAK: the run ended with one sentence and then a queue of identical
# refusals. A play tester started a whole second game with the fog off just to
# learn how far along the road they had died.
s_fin = sim()
s_fin.year = 600
from sim.engine.protocol import final_report as _FRPT, render_final as _RF
_fr = _FRPT(s_fin, NODES)
check("the end of a run reports how far along the road it got",
      _fr.get("the_whole_road_was", 0) > 100
      and _fr.get("still_to_build_when_it_ended") is not None, _fr.get("the_goal"))
check("...and names the steps that would have come next",
      len(_fr.get("the_next_things_would_have_been") or []) > 0,
      _fr.get("the_next_things_would_have_been"))
check("...and renders as a page, not a dict dump",
      "THE RUN IS OVER" in _RF(_fr) and "{" not in _RF(_fr), _RF(_fr)[:80])

# --- BREAK: `help money` and `help economy` printed the same page, and both
# were listed as separate topics.
_hm, _, _ = proto([{"cmd": "help", "topic": "money"},
                   {"cmd": "help", "topic": "economy"}])
check("help money and help economy are not the same page",
      json.dumps(_hm[0]) != json.dumps(_hm[1]),
      list((_hm[0].get("help") or {}).keys())[:3])
check("...and help money explains why the practice pays a third",
      "third" in json.dumps(_hm[0]), json.dumps(_hm[0])[:120])

# --- BREAK: `available "power and precision"` matched nothing while the
# unquoted form worked, and said nothing about why.
_aq, _, _ = proto([{"cmd": "available", "subject": '"power and precision"'},
                   {"cmd": "available", "subject": "power and precision"}])
check("a quoted subject means the same as an unquoted one",
      _aq[0].get("count") == _aq[1].get("count") and _aq[0].get("count", 0) > 0,
      (_aq[0].get("count"), _aq[1].get("count")))

# --- BREAK: HEARD OF was a silent slice at 25 in a game with a thousand nodes
# in play: no note that it was cut, and no way to see the rest.
s_h = sim()
s_h.fog = True
s_h.done.update(list(NODES)[:900]); s_h._done_changed()
for _k in list(NODES)[:900]:
    s_h.reveal_from(_k)
_p1 = S._agent_available(s_h, NODES, {})
_p2 = S._agent_available(s_h, NODES, {"heard_offset": 25})
check("a truncated 'heard of' list says it was truncated",
      _p1.get("and_more_you_have_heard_of"), _p1.get("and_more_you_have_heard_of"))
check("...and can be paged through",
      _p2.get("heard_of_but_cannot_begin")
      and not ({x["id"] for x in _p1["heard_of_but_cannot_begin"]}
               & {x["id"] for x in _p2["heard_of_but_cannot_begin"]}),
      len(_p2.get("heard_of_but_cannot_begin") or []))

# --- BREAK: at the horizon the banner still said "it is escapable ... work for
# wages", and every action it named was refused with "the run has ended".
s_end = sim()
s_end.year = 9999
check("a finished run is not given advice it will refuse to act on",
      S._agent_state(s_end, NODES).get("stuck") is None,
      S._agent_state(s_end, NODES).get("stuck"))

# --- BREAK: `why` on a mistyped id suggested; `open` said "no such node".
_ro, _, _ = proto([{"cmd": "open", "id": "fin_pawnshopp"}])
check("open on a mistyped id suggests, the way why does",
      "did you mean" in (_ro[0].get("error") or ""), _ro[0].get("error"))

# --- BREAK: "hiring 1e+21 smiths costs 281250000000000012058624 denarii".
_rn, _, _ = proto([{"cmd": "hire", "trade": "smith", "n": 1e21},
                   {"cmd": "buy", "what": "forest", "n": 1e30},
                   {"cmd": "buy", "what": "forest", "n": 3}])
check("an absurd quantity is refused as absurd, not priced in scientific notation",
      all("e+" not in (response.get("error") or "") for response in _rn[:2])
      and all(response.get("ok") is False for response in _rn[:2]),
      [response.get("error", "")[:60] for response in _rn[:2]])
check("...and an ordinary quantity still goes through the same reader",
      _rn[2].get("ok") is not None, _rn[2])

# --- BREAK: `path` after a sack never mentioned the one verb that would move
# the player on, and a run driven mechanically from it sat stuck for 140 years.
s_pth = sim()
s_pth.done.add("lead_chamber"); s_pth._done_changed()
s_pth.mothballed.add("lead_chamber")
_rp = S._agent_dispatch(s_pth, NODES, {"cmd": "path", "id": GOAL})
check("path names what on the route is shut rather than unbuilt",
      "lead_chamber" in (_rp.get("on_this_route_but_shut_down") or []),
      _rp.get("on_this_route_but_shut_down"))
check("...and names restore, which is the verb that reopens it",
      "restore" in str(_rp.get("reopen_them_with")), _rp.get("reopen_them_with"))

# --- BREAK: "no viable option in a required substitution group (fuel, vessel,
# etc.)" - the one blocked-reason a play tester never decoded. It named no
# candidate and no fix.
s_sub = sim()
_gap = next((node_id for node_id in sorted(NODES) if NODES[node_id].get("req_any")
             and not s_sub.substitution_quality(node_id)[1]
             and all(prereq_id in s_sub.done for prereq_id in NODES[node_id]["pre"])), None)
if _gap:
    _why_sub = s_sub.start_reason(_gap)[1]
    check("a substitution group says what it wants and what would serve",
          "substitution group" not in _why_sub and "would do" in _why_sub,
          _why_sub)
else:
    check("a substitution group says what it wants and what would serve",
          True, "no unmet group reachable in rome_100ad")
# And it may not name an option under fog that the player has not heard of.
s_sub_f = sim()
s_sub_f.fog = True
for _k in sorted(NODES):
    if not NODES[_k].get("req_any") or s_sub_f.substitution_quality(_k)[1]:
        continue
    _msg = s_sub_f.start_reason(_k)[1]
    _named = [node_id for node_id in NODES if node_id in _msg and not s_sub_f.is_visible(node_id)]
    if _named:
        check("a substitution refusal never names a node you cannot see",
              False, (_k, _named[:3]))
        break
else:
    check("a substitution refusal never names a node you cannot see", True, "")

# --- BREAK: "unknown_source" reached a player-facing refusal, which is data,
# not English.
s_sl = sim()
s_sl.done.update(NODES)
s_sl.done.discard("el2_potentiometer_method_measurement")
s_sl.done.discard("dynamo")
s_sl._done_changed()
_msl = s_sl.start_reason("el2_potentiometer_method_measurement")[1]
check("a substitution group reads as English, not as a data slug",
      "_" not in _msl.split("you have none")[0], _msl[:90])

# --- BREAK: "FULL CHAIN BEHIND IT: ... N den" summed the tree's BASE cost and
# applied none of the multipliers the same page prints. The eight
# prerequisites of a telescope came out at 24,175 in all five civilisations.
# Three independent fresh sessions - dispatched together under --jobs.
_chain_cids = ("rome_100ad", "han_china_100ad", "norse_900ad")
_chain_results = _par_map(
    lambda cid: proto([{"cmd": "why", "id": "telescope"}], civ=cid)[0][0].get("chain_cost"),
    _chain_cids)
_chains = dict(zip(_chain_cids, _chain_results))
check("the full-chain bill is quoted at this society's prices",
      len(set(_chains.values())) == 3, _chains)
check("...and the dearest society's chain really is the dearest",
      max(_chains, key=lambda c: _chains[c]) == "norse_900ad", _chains)
# The parts have to add up to the whole, at whatever prices.
_s_ch = sim(civ="norse_900ad")
from sim.engine.data import closure as _closure
# The chain is what is BEHIND it, so the node itself is not in the bill.
_behind = sorted(_closure(NODES, "telescope") - {"telescope"})
check("...and it is the sum of what each of those nodes would actually cost",
      abs(_chains["norse_900ad"]
          - sum(_s_ch.project_cost(node_id) for node_id in _behind)) < 0.5,
      (_chains["norse_900ad"],
       round(sum(_s_ch.project_cost(node_id) for node_id in _behind), 1)))

# --- BREAK: `bribe 1` refused at 0% protection as "already as protected as
# money can make you".
_rb, _, _ = proto([{"cmd": "bribe", "amount": 1}])
check("a bribe too small to matter says so, not that you are already covered",
      "too little" in (_rb[0].get("error") or ""), _rb[0].get("error"))

# --- BREAK: "FULL CHAIN BEHIND IT" printed identical figures in year 436
# after 227 technologies as in year 100 with nothing built.
s_cn = sim()
_r_before = S._agent_dispatch(s_cn, NODES, {"cmd": "why", "id": "telescope"})
for _p in ("patron_local", "workshop_first", "identity_cover"):
    s_cn.done.add(_p)
s_cn._done_changed()
_r_after = S._agent_dispatch(s_cn, NODES, {"cmd": "why", "id": "telescope"})
check("the chain behind a node counts down as you build it",
      _r_after["chain_size"] < _r_before["chain_size"],
      (_r_before["chain_size"], _r_after["chain_size"]))
check("...in hours as well as in nodes",
      _r_after["chain_founder_hours"] < _r_before["chain_founder_hours"],
      (_r_before["chain_founder_hours"], _r_after["chain_founder_hours"]))
check("...and in money",
      _r_after["chain_cost"] < _r_before["chain_cost"],
      (_r_before["chain_cost"], _r_after["chain_cost"]))
check("...and it still says how long the whole road was",
      _r_after["chain_size_counting_what_you_have_built"]
      == _r_before["chain_size_counting_what_you_have_built"],
      _r_after["chain_size_counting_what_you_have_built"])

# --- BREAK: "There's no 'why am I stuck?' view - three separate 90-250-year
# stalls, each caused by one node blocked on one thing, each found by typing
# `why` at a guess." Every tester of rounds eight and nine said some version.
_rs, _, _ = proto([{"cmd": "stuck"}])
check("there is one command that answers why you are not getting on",
      _rs and _rs[0].get("ok") and "what_is_holding_you_up" in _rs[0],
      list(_rs[0])[:5] if _rs else None)
# THIS CHECK PINS THE FIX, NOT THE BUG IT REPLACED: turn one is precisely
# when nothing is running, and a play tester who typed `stuck` to find out
# was told "nothing: you have work in hand, money to pay for it and people
# to do it" - the first thing they typed, and false.
check("...and on turn one it says you have started nothing",
      any(reason.get("what") == "you have started nothing"
          for reason in _rs[0]["what_is_holding_you_up"]),
      _rs[0]["what_is_holding_you_up"])
check("...and names something you could start instead",
      any("start " in str(reason.get("why")) for reason in _rs[0]["what_is_holding_you_up"]),
      _rs[0]["what_is_holding_you_up"])
# ...and once something IS running and nothing is wrong, it says so plainly
# without claiming work in hand that is not there.
_s_ok = sim(capital=500000.0)
_s_ok.start_project("identity_cover")
_rs_ok = S._agent_dispatch(_s_ok, NODES, {"cmd": "stuck"})
check("...and with work in hand and money it says nothing is holding you up",
      isinstance(_rs_ok.get("what_is_holding_you_up"), str)
      or all(reason.get("what") != "you have started nothing"
             for reason in _rs_ok["what_is_holding_you_up"]),
      _rs_ok.get("what_is_holding_you_up"))
check("...and names the cheapest thing you could actually begin",
      _rs[0].get("and_the_cheapest_thing_you_could_start_now") in NODES,
      _rs[0].get("and_the_cheapest_thing_you_could_start_now"))
_rs2, _, _ = proto([{"cmd": "start", "id": "identity_cover"},
                    {"cmd": "step", "years": 3},
                    {"cmd": "stuck"}])
_held = _rs2[-1]["what_is_holding_you_up"]
check("...and once you are committed and in the red it names both",
      not isinstance(_held, str)
      and {"work in hand", "arrears"} <= {reason["what"] for reason in _held},
      [reason.get("what") for reason in _held] if not isinstance(_held, str) else _held)
check("...and says what each piece of work in hand is waiting for",
      any(reason.get("each_waiting_on") for reason in _held if isinstance(reason, dict)), _held)
check("...and it renders as a page, not a dict dump",
      "WHY YOU ARE NOT GETTING ON" in _RP("stuck", _rs2[-1])
      and "{" not in _RP("stuck", _rs2[-1]), _RP("stuck", _rs2[-1])[:70])
_rst, _, _ = proto([{"cmd": "state"}])
check("...and `state` advertises it every turn",
      any("stuck" in option for option in (_rst[0].get("also_available") or [])),
      _rst[0].get("also_available"))

# --- BREAK: "things you built and never opened" picked the best-margin shut
# concern by revenue minus upkeep alone and told the player to 'open' it,
# without ever checking whether open_venture would actually agree - measured
# directly against the dice-free Rome credit/named-trade trap (PATH_SEARCH.md):
# at year 700, free_art sits at 0.00 and `stuck` was recommending 'open
# lens_grinding', which needs 2.13 craftsmen to supervise and refuses outright.
# lens_grinding needs more craftsmen to supervise (2.13) than a fresh
# household has free even before anything else competes for them (founder
# alone is worth 1.0), so this is reproducible with nothing but a closed
# prerequisite chain, no multi-century run required.
s_shut = sim(capital=10_000_000.0)
for _p in S.closure(NODES, "lens_grinding"):
    s_shut.done.add(_p)
s_shut.done.add("lens_grinding")
s_shut._done_changed()
check("lens_grinding is done, not operating, and genuinely profitable - the "
      "exact shape 'stuck' looks for",
      s_shut.is_venture("lens_grinding")
      and "lens_grinding" not in s_shut.operating
      and NODES["lens_grinding"]["rev"] > NODES["lens_grinding"]["up"],
      (s_shut.is_venture("lens_grinding"), "lens_grinding" in s_shut.operating))
_sch_free_sg, _art_free_sg = s_shut.venture_staff_free()
_need_sch_sg, _need_art_sg = s_shut.venture_hands("lens_grinding")
check("...and a fresh household genuinely cannot supervise it yet",
      _need_art_sg > _art_free_sg + 0.01,
      (_need_art_sg, _art_free_sg))
_stuck_shut = S._agent_dispatch(s_shut, NODES, {"cmd": "stuck"})
_shut_reason = next((reason for reason in _stuck_shut["what_is_holding_you_up"]
                    if isinstance(reason, dict)
                    and reason.get("what", "").startswith("things you built")),
                   None)
check("`stuck` never tells a player to 'open' something open_venture will "
      "actually refuse",
      _shut_reason is not None
      and "'open lens_grinding'" not in _shut_reason.get("why", ""),
      _shut_reason)
check("...and instead says the true reason (craftsmen, here) it cannot be "
      "opened, so a player knows what to fix rather than spending a turn on "
      "a refusal",
      _shut_reason is not None and "craftsmen to supervise" in _shut_reason.get("why", ""),
      _shut_reason.get("why") if _shut_reason else None)

# ...and the old, simpler advice still fires once the household genuinely CAN
# open the thing - the fix narrows the claim, it does not silence it.
s_can = sim(capital=10_000_000.0)
for _p in S.closure(NODES, "lens_grinding"):
    s_can.done.add(_p)
s_can.done.add("lens_grinding")
s_can._done_changed()
s_can.artisans = 10.0
_stuck_can = S._agent_dispatch(s_can, NODES, {"cmd": "stuck"})
_can_reason = next((reason for reason in _stuck_can["what_is_holding_you_up"]
                   if isinstance(reason, dict)
                   and reason.get("what") == "things you built and never opened"),
                  None)
check("...and once there really are enough hands free, `stuck` goes back to "
      "naming the concrete 'open X' command",
      _can_reason is not None and "'open lens_grinding'" in _can_reason.get("why", ""),
      _can_reason)

# --- BREAK: "MOST RESTS ON THESE" heads its list with items at 230 to 1,580
# denarii against an opening purse of 400, and a break tester followed the
# game's own headline advice into CREDIT EXHAUSTED by year 106. The advice is
# right; the reader needs to know which of it they can act on this year.
_rav, _, _ = proto([{"cmd": "available", "limit": 4, "sort": "price", "reverse": True},
                    {"cmd": "available"}])
check("available says what you could raise for a project",
      _rav[0].get("you_could_raise_for_a_project") is not None
      and _rav[1].get("you_could_raise_for_a_project") is not None,
      _rav[0].get("you_could_raise_for_a_project"))
_page = _RP("available", _rav[0])
check("...and marks the rows you could not raise it for",
      "*" in _page and "A * after COST" in _page,
      [line for line in _page.splitlines() if "after COST" in line])
_cheap, _, _ = proto([{"cmd": "available", "limit": 2}])
check("...and does not mark what you can plainly afford",
      "A * after COST" not in _RP("available", _cheap),
      _RP("available", _cheap)[:200])
