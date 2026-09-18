"""Concerns (revenue-earning ventures): opening, closing, staffing,
ramping, restoring and mothballing them, plus the "done but not operating"
capability-institution warning and the mines-you-own screen.

Regrouped from test_round8_fixes.py, test_round9.py, test_round10.py and
test_round12_naive15.py (see CLAUDE.md's test-file reorganisation note); the
original round numbering recorded when a check was written, not what it
tests, so it is regrouped here by subject. Checks moved verbatim - see each
one's own comment for the break it guards.
"""
from .harness import *  # noqa: F401,F403


# --- BREAK: when the staff ran short, the closer picked the concern that
# needed the MOST hands, which is very nearly the same as picking the most
# profitable one. A tester watched a 600-a-year wagon shop close twice while a
# concern earning nothing and staffed identically stayed open.
s_cl = sim(capital=200000.0)
_pair = [node_id for node_id in NODES
         if NODES[node_id]["rev"] > 0 and NODES[node_id]["up"] >= 0 and not NODES[node_id]["pre"]]
s_cl.done.update(NODES)                 # know everything, so `open` is free
s_cl.operating = set()
_rich = max(NODES, key=lambda node_id: NODES[node_id]["rev"] - NODES[node_id]["up"])
_poor = min((node_id for node_id in NODES if NODES[node_id]["rev"] > 0),
            key=lambda node_id: NODES[node_id]["rev"] - NODES[node_id]["up"])
s_cl.operating.update([_rich, _poor])
s_cl.scholars = s_cl.artisans = 0
s_cl.founder_alive = False              # nobody at all: it must close both,
_shut = s_cl.close_unstaffed_ventures(200)      # and in the right ORDER
check("an unstaffed shutdown closes the least valuable concern first",
      _shut[0] == _poor, (_shut[:2], _rich, _poor))
check("...and keeps going until the payroll actually covers what is left",
      not s_cl.operating, sorted(s_cl.operating)[:4])
check("...and what it closed is still KNOWN, only stopped",
      _rich in s_cl.done and _rich in s_cl.mothballed)

# --- BREAK: shed_loss_makers scanned `done`, so it could unlearn a concern
# that was already shut - saving nothing, since upkeep follows `operating`.
# (The positive cases are checked in round two, section C.)

# --- BREAK: staff attrition runs at 3.5% a year, so a household near the
# supervision line loses a concern most years and paid the full stock and
# premises to reopen it. A play tester watched four close at once, every year.
s_ch = sim(capital=500000.0)
s_ch.done.update(NODES); s_ch._done_changed()
s_ch.artisans = s_ch.scholars = 5.0
_v = next(node_id for node_id in NODES if s_ch.is_venture(node_id) and NODES[node_id]["rev"] > 500)
s_ch.open_venture(_v)
_full = s_ch.venture_capex(_v)
s_ch.artisans = s_ch.scholars = 0.0
s_ch.founder_alive = False
check("a concern nobody is left to watch is closed",
      _v in s_ch.close_unstaffed_ventures(105), _v)
s_ch.artisans = s_ch.scholars = 5.0
s_ch.founder_alive = True
s_ch.year = 107
_cap = s_ch.capital
s_ch.open_venture(_v)
check("...and reopening it soon costs the difference, not the whole shop",
      (_cap - s_ch.capital) < _full * 0.2, (_cap - s_ch.capital, _full))
# Past the grace it really has been given up.
s_ch2 = sim(capital=500000.0)
s_ch2.done.update(NODES); s_ch2._done_changed()
s_ch2.artisans = s_ch2.scholars = 5.0
s_ch2.open_venture(_v)
s_ch2.artisans = s_ch2.scholars = 0.0
s_ch2.founder_alive = False
s_ch2.close_unstaffed_ventures(105)
s_ch2.artisans = s_ch2.scholars = 5.0
s_ch2.founder_alive = True
s_ch2.year = 105 + s_ch2.STAFF_CLOSURE_GRACE + 1
_cap2 = s_ch2.capital
s_ch2.open_venture(_v)
check("...but a shop left shut for years is opened again in full",
      (_cap2 - s_ch2.capital) > _full * 0.8, (_cap2 - s_ch2.capital, _full))
# A shop you closed BY CHOICE was never cheap, and must not become cheap.
s_ch3 = sim(capital=500000.0)
s_ch3.done.update(NODES); s_ch3._done_changed()
s_ch3.artisans = s_ch3.scholars = 5.0
s_ch3.open_venture(_v)
s_ch3.close_venture(_v)
_cap3 = s_ch3.capital
s_ch3.open_venture(_v)
check("a concern you shut on purpose still costs the full price to reopen",
      (_cap3 - s_ch3.capital) > _full * 0.8, (_cap3 - s_ch3.capital, _full))

# --- BREAK: twenty concerns, twenty-five years, income flat, because nothing
# said on the main screen what leaving them shut was costing.
s_sh = sim(capital=50000.0)
for _k in list(NODES)[:200]:
    s_sh.done.add(_k)
s_sh._done_changed()
_stsh = S._agent_state(s_sh, NODES)
check("state says in money what your shut concerns would earn",
      _stsh.get("shut_concerns_would_earn_a_year", 0) > 0,
      _stsh.get("shut_concerns_would_earn_a_year"))
check("...and a player running everything is not nagged about it",
      S._agent_state(sim(), NODES).get("shut_concerns_would_earn_a_year") is None,
      S._agent_state(sim(), NODES).get("shut_concerns_would_earn_a_year"))

# --- THE GENERAL CASE the corpus bug was one instance of: has() gates the
# tree and the goal, running() gates the payout, and `shut_concerns` above
# only ever covered the payout being MONEY. A player who built patron_
# imperial and then let it close keeps appearing on `available` to have
# "a patron with soldiers" - has() never stops being true - while every
# running()-gated number that patron actually paid (protection, credit,
# state funding, status - update_protection and credit_limit in society.py
# and economy.py) silently went to zero, and nothing on any screen said so
# until this.
s_cg = sim(capital=50000.0)
s_cg.done.add("patron_imperial")
s_cg.done.add("corpus_dispersed")
s_cg._done_changed()
_cg_gaps = s_cg.capability_gaps()
check("a capability institution that is done but not operating is named, "
      "by id, with the specific benefit it is not collecting right now",
      {gap["id"] for gap in _cg_gaps} == {"patron_imperial", "corpus_dispersed"},
      _cg_gaps)
check("the warning has the exact shape asked for: 'Critical capability "
      "completed but not operating: <id>. <benefit> is currently "
      "inactive.', with the fix command that actually reopens it",
      all(gap["warning"] == ("Critical capability completed but not "
                           "operating: %s. %s is currently inactive."
                           % (gap["id"], gap["benefit_switched_off"]))
          and gap["fix"] == "open %s" % gap["id"]
          for gap in _cg_gaps),
      _cg_gaps)
check("...and closes the moment the doors reopen - this is a LIVE check of "
      "running(), not a one-time note",
      (s_cg.operating.add("patron_imperial"),
       {gap["id"] for gap in s_cg.capability_gaps()})[1] == {"corpus_dispersed"},
      s_cg.capability_gaps())
s_cg.operating.discard("patron_imperial")
check("plague_preparedness is deliberately never warned about: its only "
      "measurable protection (HAZARD_COUNTERS) is has()-gated like corpus, "
      "so closing it costs nothing today, and a false alarm here is "
      "exactly the wall-of-text failure this feature exists to avoid",
      "plague_preparedness" not in s_cg.NOT_OPERATING_BENEFIT,
      sorted(s_cg.NOT_OPERATING_BENEFIT))
check("fin_university's sole benefit is shared (an `or`) with "
      "school_founded in update_protection, so it is only named while "
      "BOTH are closed, never while school_founded alone still covers it",
      (lambda s: (
          s.done.add("fin_university"), s.done.add("school_founded"),
          s.operating.add("school_founded"), s._done_changed(),
          "fin_university" not in {gap["id"] for gap in s.capability_gaps()})[-1]
      )(sim()),
      "checked fin_university/school_founded or-gate")
_st_cg = S._agent_state(s_cg, NODES)
check("`state` - the screen a player rereads every year - carries this "
      "warning too, not only a command nobody runs unprompted",
      _st_cg.get("critical_capabilities_not_operating") is not None
      and {gap["id"] for gap in _st_cg["critical_capabilities_not_operating"]}
          == {"corpus_dispersed", "patron_imperial"},
      _st_cg.get("critical_capabilities_not_operating"))
check("...and says nothing when every completed capability is open",
      S._agent_state(sim(), NODES).get(
          "critical_capabilities_not_operating") is None,
      S._agent_state(sim(), NODES).get("critical_capabilities_not_operating"))
_risk_cg = s_cg.knowledge_risk()
check("`risk` - the screen whose whole job is telling you what protects "
      "you - carries the same warning, independent of `state`",
      _risk_cg.get("critical_capabilities_not_operating") is not None
      and {gap["id"] for gap in _risk_cg["critical_capabilities_not_operating"]}
          == {"corpus_dispersed", "patron_imperial"},
      _risk_cg.get("critical_capabilities_not_operating"))
check("the id named is never hidden under fog - a player has always "
      "already discovered anything in their own `done`",
      all(s_cg.is_visible(gap["id"]) for gap in _cg_gaps), _cg_gaps)

# --- BREAK: auto_mine took 353,039 a year against 467,227 of revenue and
# there was no command that named what you owned or what it cost.
s_mn = sim(capital=2000000.0)
s_mn.open_mine("coal", 400, partial=False)
_rmn_new = S._agent_dispatch(s_mn, NODES, {"cmd": "mines"})
check("a shaft you have just sunk is listed while it is still being sunk",
      _rmn_new["mines_you_own"] != "none"
      and _rmn_new["still_being_sunk"].get("coal"),
      _rmn_new.get("mines_you_own"))
for _ in range(int(s_mn.MINE_LEAD_YEARS) + 1):
    s_mn.year += 1
    s_mn.commission_mines()
_rmn = S._agent_dispatch(s_mn, NODES, {"cmd": "mines"})
check("there is a command that lists the mines you own and their cost",
      _rmn["mines_you_own"] != "none"
      and _rmn["they_cost_you_a_year_in_all"] > 0, _rmn.get("mines_you_own"))
check("...and each row says how to shut it",
      all("close" in mine_row["shut_it_with"] for mine_row in _rmn["mines_you_own"]),
      _rmn["mines_you_own"][:1])
check("...and it renders as a table, not a dict dump",
      "YOUR OWN WORKINGS" in _RP("mines", _rmn) and "{" not in _RP("mines", _rmn),
      _RP("mines", _rmn)[:60])

# --- BREAK: "A concern you open reaches its full figure over 3 years" - and a
# concern built in 100 and opened in 130 was at full takings the day its doors
# opened, because the ramp read the year you worked it OUT. Delaying `open`
# was strictly better than opening promptly.
s_rp = sim(capital=500000.0)
_vr = next(node_id for node_id in sorted(NODES)
           if s_rp.is_venture(node_id) and NODES[node_id]["rev"] > 500 and not NODES[node_id]["pre"])
s_rp.done.add(_vr); s_rp.done_year[_vr] = 100; s_rp._done_changed()
s_rp.artisans = s_rp.scholars = 20.0
s_rp.year = 130
s_rp.open_venture(_vr)
_ramps = []
for _y in (130, 131, 132, 133):
    s_rp.year = _y
    _ramps.append(round(s_rp.venture_ramp(_vr), 3))
check("a concern opened late still starts small",
      _ramps[0] < 0.4, _ramps)
check("...and reaches its full figure over the years the ledger promises",
      _ramps == [1 / 3.0, 2 / 3.0, 1.0, 1.0][:4]
      or (_ramps[0] < _ramps[1] < _ramps[2] == _ramps[3] == 1.0), _ramps)
# Reopening something you already ran does not restart its custom.
s_rp.year = 140
s_rp.close_venture(_vr)
s_rp.open_venture(_vr)
check("...and reopening a shop the town already knows does not start it over",
      s_rp.venture_ramp(_vr) == 1.0, s_rp.venture_ramp(_vr))

# --- BREAK: `restore` charged the full price for a concern the staffing rule
# had shut, while the closing message promises a tenth.
s_rs = sim(capital=500000.0)
s_rs.done.update(NODES); s_rs._done_changed()
s_rs.artisans = s_rs.scholars = 5.0
_vv = next(node_id for node_id in sorted(NODES)
           if s_rs.is_venture(node_id) and NODES[node_id]["rev"] > 500)
s_rs.open_venture(_vv)
_fullfee = max(s_rs.project_cost(_vv) * 0.3, NODES[_vv]["up"] * 2.0)
s_rs.artisans = s_rs.scholars = 0.0
s_rs.founder_alive = False
s_rs.close_unstaffed_ventures(105)
s_rs.artisans = s_rs.scholars = 5.0
s_rs.founder_alive = True
s_rs.year = 107
_cap_rs = s_rs.capital
s_rs.restore_work(_vv)
check("restoring a shop the staffing rule shut costs the tenth it promised",
      (_cap_rs - s_rs.capital) < _fullfee * 0.2,
      (_cap_rs - s_rs.capital, _fullfee))

# --- BREAK: the supervision test was an exact comparison, and attrition moves
# the payroll by fractions of a man every single year. A play tester watched
# the same concern close and reopen "every single turn for four centuries" and
# called it endless busywork. Nobody shuts a shop over a fortieth of a man.
s_hy = sim(capital=500000.0)
s_hy.done.update(NODES); s_hy._done_changed()
s_hy.artisans = s_hy.scholars = 6.0
_vh = max((node_id for node_id in sorted(NODES)
           if s_hy.is_venture(node_id) and NODES[node_id]["rev"] > 500
           and 1.6 <= s_hy.venture_hands(node_id)[1] <= 5.0
           and s_hy.venture_hands(node_id)[0] <= 5.0),
          key=lambda k: s_hy.venture_hands(k)[1])
_ok_hy, _ = s_hy.open_venture(_vh)
check("(a shop to test the staffing rule on is open)",
      _vh in s_hy.operating, (_vh, _ok_hy, s_hy.venture_hands(_vh)))
_need_s, _need_a = s_hy.venture_staff_used()
_own = s_hy.FOUNDER_IS_WORTH if s_hy.founder_alive else 0.0
# stand the payroll exactly on the line, then let a tenth of a man die
s_hy.artisans = _need_a - _own - 0.1
s_hy.scholars = max(0.0, _need_s - 1.0)
s_hy.close_unstaffed_ventures(110)
check("a tenth of a man short does not shut the shop",
      _vh in s_hy.operating, (s_hy.artisans, _need_a, sorted(s_hy.operating)))
# but a real pair of hands gone does
s_hy.artisans = _need_a - _own - 0.6
s_hy.close_unstaffed_ventures(111)
check("...but a whole hand short still does",
      _vh not in s_hy.operating, (s_hy.artisans, _need_a))

# --- BREAK: a newly opened venture ramps to its full quoted revenue over
# revenue_ramp_years (3) - real, reasonable, and, per an England playtester,
# announced nowhere but a footnote inside `money` (still_ramping()), read
# only after the gap between the quote and the ledger had already confused
# somebody. Said now, in the same breath as the figure it qualifies, right
# when opening is the moment that starts the clock.
s_ow = sim(capital=1_000_000.0)
s_ow.done.add("fin_restaurant")
s_ow._done_changed()
_ow_ok, _ow_msg = s_ow.open_venture("fin_restaurant")
check("opening a revenue-earning concern says it ramps up over time, in "
      "the same success message that quotes the mature figure",
      _ow_ok and str(s_ow.cfg["revenue_ramp_years"]) in _ow_msg
      and "less at first" in _ow_msg,
      _ow_msg)
# A pure-cost capability (no revenue at all) has nothing to ramp, and gets
# no such note - there is no custom to find it.
s_ow2 = sim(capital=1_000_000.0)
s_ow2.done.add("identity_cover")
s_ow2._done_changed()
_ow2_ok, _ow2_msg = s_ow2.open_venture("identity_cover")
check("...while a zero-revenue capability gets no ramp note at all",
      _ow2_ok and "ramp" not in _ow2_msg.lower()
      and "less at first" not in _ow2_msg,
      _ow2_msg)

# --- BREAK: a Han playtester opened a net-loss concern four separate
# times, three of them after already having caught and written up the
# mistake once, because EARNS/YR and UPKEEP/YR sit side by side on every
# screen and nothing ever subtracts them for the reader. Flagged now, at
# the one moment a player could still back out - opening itself - for any
# ordinary venture where upkeep exceeds revenue even fully ramped up.
s_ln = sim(capital=1_000_000.0)
_ln_k = next((node_id for node_id, node in NODES.items()
             if node.get("up", 0) > node.get("rev", 0) > 0
             and node_id not in s_ln.CAPABILITY_INSTITUTIONS), None)
check("a real, non-capability net-loss-making node exists in the tree to "
      "test against",
      _ln_k is not None, _ln_k)
if _ln_k:
    s_ln.done.add(_ln_k)
    s_ln._done_changed()
    _ln_ok, _ln_msg = s_ln.open_venture(_ln_k)
    check("opening an ordinary concern that costs more than it earns, even "
          "fully ramped, is flagged right there in the success message - "
          "not left for the reader to subtract two numbers themselves",
          _ln_ok and "costs more than it earns" in _ln_msg
          and "{:,.0f}".format(NODES[_ln_k]["up"] - NODES[_ln_k]["rev"])
          in _ln_msg,
          _ln_msg)
# A capability institution (a school, a workshop, a patron...) losing money
# is the INTENDED shape of the trade, never flagged as a mistake here.
# sorted(), not CAPABILITY_INSTITUTIONS' own frozenset order: a bare
# frozenset of strings iterates in whatever order this process's
# PYTHONHASHSEED happens to give it, and one candidate here
# (fin_argentarii) is a societal institution open_venture refuses outright
# for a reason that has nothing to do with cost - "next()" over the
# unsorted set picked it about one run in ten and failed the check below
# for a refusal this test was never asking about. Trying candidates in a
# fixed order and skipping ones that cannot be opened at all asks the
# actual question - does an OPENABLE loss-making institution get warned
# about its loss - reproducibly.
s_ln2 = sim(capital=1_000_000.0)
_ln2_cands = sorted(node_id for node_id in s_ln2.CAPABILITY_INSTITUTIONS
                    if NODES.get(node_id, {}).get("up", 0) > NODES.get(node_id, {}).get("rev", 0))
_ln2_k, _ln2_ok, _ln2_msg = None, False, ""
for _cand in _ln2_cands:
    s_ln2.done.add(_cand)
    s_ln2._done_changed()
    _ok, _msg = s_ln2.open_venture(_cand)
    if _ok:
        _ln2_k, _ln2_ok, _ln2_msg = _cand, _ok, _msg
        break
    s_ln2.done.discard(_cand)
    s_ln2._done_changed()
check("a capability institution that runs at a loss by design, and can "
      "actually be opened, exists to test the exclusion against",
      _ln2_k is not None, (_ln2_cands, _ln2_msg))
if _ln2_k:
    check("...and opening it gets no 'costs more than it earns' warning - "
          "that loss is the point, not a mistake",
          _ln2_ok and "costs more than it earns" not in _ln2_msg, _ln2_msg)

# --- BREAK 1: a fully-built concern worth ~1,500/yr that could never be
# opened because the founder was short 0.01 of a craftsman's supervision
# time, and `mothball` - the tool for freeing committed resources - refused
# to release the tiny holder on the grounds it had no money upkeep, so
# there was "nothing to save". The resource actually short was staff time,
# not money, and mothball asked about money alone.
_s_mb = sim()
_mb_id = next(k for k, n in NODES.items()
              if n.get("up", 0) <= 0 and n.get("rev", 0) > 0 and _s_mb.is_venture(k))
_s_mb.done.add(_mb_id); _s_mb._done_changed()
_s_mb.operating.add(_mb_id)
_mb_sch, _mb_art = _s_mb.venture_hands(_mb_id)
check("the zero-upkeep venture used for this test really does tie up staff",
      _mb_art > 0.005 or _mb_sch > 0.005, (_mb_id, _mb_sch, _mb_art))
_mb_ok, _mb_msg = _s_mb.mothball_work(_mb_id)
check("mothball releases a concern whose cost is staff time, not money, "
      "even though its money upkeep is zero",
      _mb_ok, _mb_msg)
check("...and it actually frees the craftsmen/scholars it held, not just "
      "the (zero) money",
      _s_mb.venture_staff_used() == (0.0, 0.0), _s_mb.venture_staff_used())
check("...and says so, rather than only ever talking about money",
      "craftsm" in _mb_msg or "scholar" in _mb_msg, _mb_msg)
# A concern with genuinely nothing to save - no money upkeep, not running,
# so no staff held either - must still be refused honestly.
_s_mb2 = sim()
_mb2_id = next(k for k, n in NODES.items()
               if n.get("up", 0) <= 0 and n.get("rev", 0) <= 0
               and k not in _s_mb2.granted
               and not (_s_mb2.never_abandon(k) and n["cat"] in _s_mb2.NEVER_ABANDON))
_s_mb2.done.add(_mb2_id); _s_mb2._done_changed()
_mb2_ok, _mb2_msg = _s_mb2.mothball_work(_mb2_id)
check("...but a thing with genuinely nothing to save (no money, no staff "
      "held) is still refused, honestly",
      not _mb2_ok and "nothing to save" in _mb2_msg, _mb2_msg)
