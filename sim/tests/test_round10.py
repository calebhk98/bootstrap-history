"""round10: split verbatim from the old test_regressions.py (original lines 6063-6643).

Moving contiguous blocks verbatim: no check below was reformatted, reworded or otherwise touched in the split.
"""
from .harness import *  # noqa: F401,F403

# ======================================================================
# ROUND 10: two testers won, and the break tester found four ways the game
# was wrong about its own numbers.
# ======================================================================

# --- BREAK: paying off your debt IN FULL made you insolvent. `work scholar
# 2000` sells the founder's whole year, which takes the practice's income to
# nothing FOR that year, which collapsed the credit line from 1,397 to 210 in
# the middle of a step - and the project spending already committed against
# the old line breached the new one. Owing 628 was safe; owing nothing was
# ruin.
_rd, _, _ = proto([{"cmd": "start", "id": "arithmetic_positional"},
                   {"cmd": "step", "years": 1},
                   {"cmd": "work", "trade": "scholar", "hours": 2000},
                   {"cmd": "step", "years": 1},
                   {"cmd": "state"}])
check("clearing your debt by working does not make you insolvent",
      not any("INSOLVENCY" in json.dumps(x) for x in _rd), 
      [e for x in _rd for e in (x.get("events") or []) if "INSOLVENCY" in str(e)])
check("...and does not take your whole reputation with it",
      _rd[-1].get("reputation", 0) > 1.0, _rd[-1].get("reputation"))
s_cc = sim()
_full = s_cc.credit_limit()
s_cc.wage_hours_this_year = s_cc.director_pool()
check("a lender does not cut your line because you took a job this year",
      abs(s_cc.credit_limit() - _full) < 1e-6, (_full, s_cc.credit_limit()))

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

# --- BREAK: `ventures` understated every concern by a uniform 2.234x against
# the `money` ledger, and its NEEDS column printed the BUILD crew where the
# engine charges supervision - a quarter of it, and never the number the
# refusal quotes.
s_vv = sim(capital=5000000.0)
s_vv.done.update(NODES); s_vv._done_changed()
s_vv.artisans = s_vv.scholars = 40.0
_opened = 0
for _k in sorted(NODES):
    if s_vv.is_venture(_k) and _opened < 5 and s_vv.open_venture(_k)[0]:
        _opened += 1
for _ in range(4):
    s_vv.step()
_vr = S._agent_dispatch(s_vv, NODES, {"cmd": "ventures"})
_led = s_vv.revenue_sources()
check("ventures quotes the same earnings the ledger credits",
      all(abs(r["earns_a_year"] - _led.get(r["id"], r["earns_a_year"])) < 0.11
          for r in _vr["running"]),
      [(r["id"], r["earns_a_year"], _led.get(r["id"])) for r in _vr["running"]][:2])
check("...and its NEEDS column is the supervision the engine charges",
      all(abs(r["needs"]["craftsmen"] - s_vv.venture_hands(r["id"])[1]) < 0.011
          for r in _vr["running"]),
      [(r["id"], r["needs"]) for r in _vr["running"]][:2])


# --- BREAK: "CREDIT EXHAUSTED: 2 projects halted, unfinished" - "halted"
# means paused to a reader and meant deleted here. A break tester watched 795
# denarii and about 800 founder-hours vanish, with scientific_method dying 115
# denarii short of done and every hour already spent, and `stop` losing the
# same thing so no branch saved it.
s_ce = sim()
s_ce.start_project("identity_cover")
for _ in range(3):
    s_ce.step()
_spent = s_ce.active["identity_cover"]["spent"]
check("a project part-paid for has really been part-paid for",
      _spent > 100, _spent)
s_ce.credit_limit = lambda: 0.0
s_ce.enforce_credit_limit(s_ce.year)
check("the creditors stopping your work does not burn what you paid",
      abs(s_ce.paid_towards.get("identity_cover", 0.0) - _spent) < 0.5,
      s_ce.paid_towards)
check("...and the event says so, and names what it stopped",
      any("identity_cover" in m and "stands to your credit" in m
          for _, m in s_ce.log),
      [m for _, m in s_ce.log if "CREDIT EXHAUSTED" in m][:1])
s_ce.capital, s_ce.credit_frozen_until = 50000.0, 0
s_ce.start_project("identity_cover")
check("...and beginning again takes it off the bill",
      abs(s_ce.active["identity_cover"]["cost_left"]
          - (s_ce.project_cost("identity_cover") - _spent)) < 0.5,
      (s_ce.active["identity_cover"]["cost_left"],
       s_ce.project_cost("identity_cover")))
check("...and the credit is spent once, not every time",
      "identity_cover" not in s_ce.paid_towards, s_ce.paid_towards)

# --- BREAK: `restore` charged the full price for a concern the staffing rule
# had shut, while the closing message promises a tenth.
s_rs = sim(capital=500000.0)
s_rs.done.update(NODES); s_rs._done_changed()
s_rs.artisans = s_rs.scholars = 5.0
_vv = next(k for k in sorted(NODES)
           if s_rs.is_venture(k) and NODES[k]["rev"] > 500)
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
_vh = max((k for k in sorted(NODES)
           if s_hy.is_venture(k) and NODES[k]["rev"] > 500
           and 1.6 <= s_hy.venture_hands(k)[1] <= 5.0
           and s_hy.venture_hands(k)[0] <= 5.0),
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


# --- BREAK: three places printed the founder's own staff differently. The
# prompt showed hired heads ("sch 0 art 0"), `why` compared a project against
# effective_scholars() and s.artisans ("you have 1, 0"), and start_project
# actually gated on craft_hands_available() - which counts the founder AND
# hours already bought. A play tester read two of the three on one turn and
# reported the game as having lost count of their household.
s_cn = sim(capital=20000.0)
_kn = next(k for k in sorted(NODES) if NODES[k]["art"] >= 2 and NODES[k]["sch"] == 0)
s_cn.commission("mason", 4000.0)
_why_cn = S._node_explain(s_cn, NODES, _kn)
check("`why` counts the same artisans `start` does: yourself and hours bought",
      abs(_why_cn["you_have"]["artisans"] - round(s_cn.craft_hands_available(), 1)) < 0.05,
      (_why_cn["you_have"], s_cn.craft_hands_available(), s_cn.artisans))
check("...and says which people it is counting",
      "yourself" in str(_why_cn.get("you_have_counts")), _why_cn.get("you_have_counts"))
check("...and it is more than the bare payroll, having bought a mason's year",
      _why_cn["you_have"]["artisans"] > s_cn.artisans + 0.5,
      (_why_cn["you_have"]["artisans"], s_cn.artisans))

# --- BREAK: rubber was priced at 99,999 a kilo, a sentinel left over from the
# abolished "unobtainable" tier, and it survived the abolition of the concept
# that justified it. A play tester worked out that one kilo was four hundred
# artisan-years, that a rubber eraser cost 3,001,105 against 5 for a
# breadcrumb, and that securing a rubber supply did not change the price by a
# denarius. It was also over half of the whole tree's capital cost.
_RUB = ("rubber_kg", "rubber_tubing_kg")
for _r in _RUB:
    check("%s is priced like a distant import, not like a sentinel" % _r,
          0 < PRICES["purchase_prices_denarii"][_r]["p"] < 1000,
          PRICES["purchase_prices_denarii"][_r]["p"])
# ...and the reason the sentinel existed - that nothing stopped you buying it -
# is answered where it belongs, in the tree: you cannot use rubber until you
# have gone and got some.
def _anc_of(k, seen=None):
    seen = seen if seen is not None else set()
    for _p in NODES[k]["pre"]:
        if _p not in seen:
            seen.add(_p); _anc_of(_p, seen)
    return seen
_rub_users = sorted(k for k, v in NODES.items()
                    if any("rubber" in m for m in (v.get("mat") or {})))
_ungated = [k for k in _rub_users
            if not ({"mat_natural_rubber", "mat_synthetic_rubber"} & _anc_of(k))]
# --- BREAK: a node whose own note names a material it does not require. The
# blind prerequisite audit found in2_electron_source_cathode saying "Tungsten
# chosen for high melting point and low evaporation" with no tungsten anywhere
# in its ancestry. Ductile tungsten filament wire is the Coolidge process and
# is a real achievement: tungsten is too brittle to draw until it is sintered
# from powder and worked hot, which is why powder metallurgy belongs here too.
#
# It was nearly deferred on a misread number. mat_tungsten's closure is 102
# nodes, which looked like adding a hundred nodes to a 145-node goal path - but
# 101 of those 102 were already in that closure, so the MARGINAL addition is
# one. Raw closure size is the wrong quantity to price a new edge with.
_cath = NODES["in2_electron_source_cathode"]["pre"]
check("the cathode that is made of tungsten requires tungsten",
      "mat_tungsten" in _cath, _cath)
check("...and the powder metallurgy that makes tungsten drawable at all",
      "met_powder_metallurgy" in _cath, _cath)
check("...and the note that named it is still the reason it is there",
      "tungsten" in (NODES["in2_electron_source_cathode"].get("note") or "").lower(),
      (NODES["in2_electron_source_cathode"].get("note") or "")[:90])

check("nothing can be made of rubber without first securing rubber",
      not _ungated, _ungated)
check("(and there really are rubber recipes to gate)", len(_rub_users) > 10,
      len(_rub_users))

# --- BREAK: grant_ambient ran BEFORE the civ's named starting_techs were
# added, so anything they unlocked was credited on the player's first `step`
# and printed as "COMPLETED 100: Amphitheatre with tiered seating" - a
# completion for something they had never started, in the same words as their
# own work. Nothing free may arrive after the game begins.
for _civ_ga in ("rome_100ad", "han_china_100ad", "norse_900ad", "mexica_1500",
                "england_1300"):
    _s_ga = sim(civ=_civ_ga)
    _before_ga = set(_s_ga.done)
    _s_ga.step()
    check("%s hands you nothing free on turn one" % _civ_ga,
          not (_s_ga.done - _before_ga), sorted(_s_ga.done - _before_ga))


# --- BREAK: `stop` burned the money as well as the hours, "same as a real
# abandoned enterprise" - so when the creditors were about to take everything,
# stopping something yourself cost exactly as much as letting them, and `stop`
# was never the right move. The site does not un-dig itself either way.
s_sp = sim()
s_sp.start_project("identity_cover")
for _ in range(2):
    s_sp.step()
_spent_sp = s_sp.active["identity_cover"]["spent"]
_ok_sp, _why_sp = s_sp.stop_project("identity_cover")
check("stopping a project keeps the money already paid",
      _ok_sp and abs(s_sp.paid_towards.get("identity_cover", 0.0)
                     - _spent_sp) < 0.5,
      (s_sp.paid_towards, _spent_sp))
check("...and says so",
      "comes off the bill" in str(_why_sp), _why_sp)
s_sp.capital = 50000.0
s_sp.start_project("identity_cover")
check("...and beginning again bills only the remainder",
      abs(s_sp.active["identity_cover"]["cost_left"]
          - (s_sp.project_cost("identity_cover") - _spent_sp)) < 0.5,
      s_sp.active["identity_cover"]["cost_left"])
check("...but the hours really are gone: that was your year",
      abs(s_sp.active["identity_cover"]["ph_left"]
          - NODES["identity_cover"]["ph"]) < 1e-6,
      s_sp.active["identity_cover"]["ph_left"])
# And the affordability gate has to test the REMAINDER, or a nearly-paid-for
# project is refused for a bill it no longer owes.
s_sp2 = sim()
s_sp2.paid_towards = {"identity_cover": s_sp2.project_cost("identity_cover") - 5.0}
check("...and a nearly-paid project is not refused for its gross price",
      s_sp2.start_project("identity_cover")[0],
      s_sp2.start_reason("identity_cover"))

# --- BREAK: `start` discounts a halted project's remaining bill by what was
# already sunk into it (see _paid_now above) - but `why` kept quoting the
# gross sticker price forever, for a project a creditor or the player's own
# `stop` had halted partway. An England player planning from `why` was
# planning against a number the engine would never actually charge; the
# real, discounted figure showed up only inside a `start` refusal or its
# success line, after the fact.
s_wp = sim(capital=1000.0)
_wp_k = next(kk for kk in s_wp.order if s_wp.can_start(kk) and NODES[kk]["ph"] > 0)
s_wp.start_project(_wp_k)
s_wp.active[_wp_k]["spent"] = 500.0
s_wp.stop_project(_wp_k)
_wp_out = S._agent_dispatch(s_wp, NODES, {"cmd": "why", "id": _wp_k})
check("`why` on a halted, partly-paid project shows both the gross total "
      "and what 'start' would actually charge, with the sunk amount "
      "accounting for the difference",
      _wp_out["cost"].get("already_paid_towards_this") == 500.0
      and abs(_wp_out["cost"]["what_start_would_actually_charge"]
              - (_wp_out["cost"]["total"] - 500.0)) < 0.5,
      _wp_out["cost"])
check("...and it matches what `start` would actually bill, not a second "
      "estimate of it",
      abs(_wp_out["cost"]["what_start_would_actually_charge"]
          - S._agent_dispatch(s_wp, NODES, {"cmd": "start", "id": _wp_k}
                              )["the_bill_you_have_taken_on"]) < 0.5,
      (_wp_out["cost"]["what_start_would_actually_charge"],))
# And the ordinary case - nothing sunk into this node - gets no such field.
s_wp2 = sim(capital=1000.0)
_wp2_k = next(kk for kk in s_wp2.order if s_wp2.can_start(kk))
_wp2_out = S._agent_dispatch(s_wp2, NODES, {"cmd": "why", "id": _wp2_k})
check("...while a project with nothing sunk into it gets no discount "
      "field at all - there is nothing to discount",
      "already_paid_towards_this" not in _wp2_out["cost"], _wp2_out["cost"])

# --- BREAK: a newly opened venture ramps to its full quoted revenue over
# revenue_ramp_years (3) - real, reasonable, and, per an England playtester,
# announced nowhere but a footnote inside `money` (still_ramping()), read
# only after the gap between the quote and the ledger had already confused
# somebody. Said now, in the same breath as the figure it qualifies, right
# when opening is the moment that starts the clock.
s_ow = sim(capital=1_000_000.0)
s_ow.done.add("fin_pawnshop")
s_ow._done_changed()
_ow_ok, _ow_msg = s_ow.open_venture("fin_pawnshop")
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
_ln_k = next((k for k, n in NODES.items()
             if n.get("up", 0) > n.get("rev", 0) > 0
             and k not in s_ln.CAPABILITY_INSTITUTIONS), None)
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
_ln2_cands = sorted(k for k in s_ln2.CAPABILITY_INSTITUTIONS
                    if NODES.get(k, {}).get("up", 0) > NODES.get(k, {}).get("rev", 0))
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


# --- BREAK: "MOST RESTS ON THESE" heads its list with items at 230 to 1,580
# denarii against an opening purse of 400, and a break tester followed the
# game's own headline advice into CREDIT EXHAUSTED by year 106. The advice is
# right; the reader needs to know which of it they can act on this year.
_rav, _, _ = proto([{"cmd": "available", "limit": 4, "offset": 200},
                    {"cmd": "available"}])
check("available says what you could raise for a project",
      _rav[0].get("you_could_raise_for_a_project") is not None
      and _rav[1].get("you_could_raise_for_a_project") is not None,
      _rav[0].get("you_could_raise_for_a_project"))
_page = _RP("available", _rav[0])
check("...and marks the rows you could not raise it for",
      "*" in _page and "A * after COST" in _page,
      [l for l in _page.splitlines() if "after COST" in l])
_cheap, _, _ = proto([{"cmd": "available", "limit": 2}])
check("...and does not mark what you can plainly afford",
      "A * after COST" not in _RP("available", _cheap),
      _RP("available", _cheap)[:200])


# --- JOB 1: "something happens shortly after the game starts and then
# nothing happens for centuries" was the same shape of complaint across
# several rounds of playtesting, on more than one civilization. Audited and
# fixed by adding real, dated events; this check keeps the fix from rotting
# by failing if a future edit to a civilization file reopens a long silent
# stretch. Ninety years is generous against what every file now actually
# does (England's worst remaining gap is 63, Norse's is 86) but still catches
# the kind of quarter-millennium silence the audit found.
for _cf in sorted(glob.glob(os.path.join(ROOT, "data", "civilizations", "*.json"))):
    _cid = os.path.basename(_cf)[:-5]
    if _cid.startswith("_"):
        continue
    _cd = json.load(open(_cf))
    _start = _cd["year"]
    _windows = sorted((h["years"][0], h["years"][1]) for h in _cd.get("hazards", []))
    _prev, _gaps = _start, []
    for (_a, _b) in _windows:
        _gaps.append(_a - _prev)
        _prev = max(_prev, _b)
    check("%s: no silent stretch longer than 90 years between its dated "
          "events" % _cid,
          all(g <= 90 for g in _gaps), _gaps)
    if _cid != "mexica_1500":
        # The Mexica's list runs out at the edge of real history, not at the
        # horizon - extending it past here would mean inventing the future,
        # which the drug war entry's own note says this file will not do.
        # Every OTHER civilization's list should reach close to the end of
        # the 500-700 year run the brief asked for.
        check("%s: its events reach close to the end of a 700-year run, "
              "not just the first half of it" % _cid,
              (_start + 700) - _prev <= 90, (_start, _prev))

# --- JOB 2: A PLAGUE MOVES THE WHOLE SOCIETY, NOT JUST YOUR OWN HOUSEHOLD. A
# playtester watched the Black Death take a third of their own staff and
# nothing else happen anywhere in the game, and asked why a mortality event
# this size left the rest of the economy untouched - no dearer hiring, no
# dearer wages, nothing. self.pop_deficit (core.py, fed by _shocks in
# society.py) is the fix: the hazard now also costs the whole labour market
# people, and a smaller labour market pays more to hire from.
s = sim(civ="england_1300")
_normal_wage = s.wage_index
s.year = 1348
s._shocks(1348)
check("the Black Death costs the whole society people, not only your own "
      "household",
      abs(s.pop_deficit - 0.45) < 1e-6, s.pop_deficit)

# --- your own quarantine (plague_preparedness) protects your own household
# - that is what hazard_relief already does to the personal staff_loss above
# - and must NOT also soften the society-wide figure: the rest of the world
# never built your hedge.
s2 = sim(civ="england_1300")
s2.done.add("plague_preparedness"); s2.operating.add("plague_preparedness")
s2._done_changed()
s2.year = 1348
s2._shocks(1348)
check("a hedge against plague shields your own staff, not the whole "
      "population's labour market",
      abs(s2.pop_deficit - 0.45) < 1e-6, s2.pop_deficit)

# --- scarcer labour is dearer labour immediately: the event and the economy
# screen must not disagree for the remainder of the year in which it fires.
_shock_wage = s.wage_index
check("wages rise immediately after a mortality shock, because the labour "
      "market just got smaller",
      _shock_wage > _normal_wage * 1.2, (_normal_wage, _shock_wage))
s.year = 1349
s._demographic_recovery(1349)
check("wages remain elevated the year after a mortality shock",
      s.wage_index > _normal_wage * 1.2, (_normal_wage, s.wage_index))
check("the wage cascade is LOGGED, so a player can see why their wage bill "
      "jumped instead of having to notice it in the accounts",
      any("running" in m and "above normal" in m for _y, m in s.log),
      [m for _y, m in s.log if "wage" in m.lower()])

# --- it fades on the clock the hazard earned, not instantly and not
# forever - the actual brief: "the effect decaying back over a historically
# plausible recovery period rather than being permanent or instant".
s4 = sim(civ="england_1300")
s4.year = 1348
s4._shocks(1348)
for _yr in range(1349, 1349 + 50):
    s4._demographic_recovery(_yr)
_mid_premium = s4.wage_index / _normal_wage - 1.0
for _yr in range(1349 + 50, 1349 + 150):
    s4._demographic_recovery(_yr)
_end_premium = s4.wage_index / _normal_wage - 1.0
check("fifty years on, the wage premium from the Black Death is still "
      "substantial, not gone in a handful of years",
      _mid_premium > 0.10, _mid_premium)
check("...and by England's roughly 150-year demographic recovery it has "
      "mostly faded, not stayed at its peak forever",
      _end_premium < 0.05, _end_premium)

# --- a milder mortality event earns a shorter recovery than the Black
# Death's 150 years, in proportion to how much of the population it
# actually took, not the same horizon regardless of size.
s5 = sim(civ="rome_100ad")
for _yr in range(165, 181):
    s5.year = _yr
    s5._shocks(_yr)
    if s5.pop_deficit > 0:
        break
check("the Antonine plague (28% of staff) earns a shorter demographic "
      "recovery than the Black Death's (45%) 150 years, scaled to size",
      0 < s5._pop_recovery_years < 150.0, s5._pop_recovery_years)

# --- JOB 3: TECHNOLOGY RAISES THE POPULATION, SLOWLY. Sanitation,
# antisepsis, crop rotation and the like should feed back into a bigger
# labour market eventually, but a lower death rate shows up in the headcount
# a generation later, not the day a latrine opens - so apply_tech_effects
# must queue the gain rather than apply it the year the node completes.
s6 = sim(civ="rome_100ad")
_base_pop = s6._pop_scale_base
s6.apply_tech_effects("sanitation_antisepsis")
check("a population-raising technology does not move the population the "
      "instant it completes",
      s6._pop_scale_base == _base_pop, s6._pop_scale_base)
for _yr in range(100, 100 + 40):
    s6._demographic_recovery(_yr)
check("...but it has fully landed by the end of its forty-year ramp",
      abs(s6._pop_scale_base - (_base_pop + 0.02)) < 1e-6, s6._pop_scale_base)
check("...and the gain stops growing once it has landed, rather than "
      "compounding forever",
      not s6._pop_tech_pending, s6._pop_tech_pending)
s6.apply_tech_effects("sanitation_antisepsis")
for _yr in range(140, 140 + 20):
    s6._demographic_recovery(_yr)
check("halfway through a SECOND such technology's ramp, only half of its "
      "own gain has landed - the ramp does not dump the total on year one",
      abs(s6._pop_scale_base - (_base_pop + 0.02 + 0.01)) < 1e-6,
      s6._pop_scale_base)

# =============================================================================
# SEVERITY HONESTY: the words attached to a dated hazard must match `loss`,
# the number the mitigation mechanic actually applied, never `raw`, the
# hazard's own historical unmitigated figure - a player whose sanitation and
# quarantine cut the Antonine plague's 28% down to a fraction of a percent
# still read "(would have been -28%: ...)" glued onto the same sentence and
# reasonably called it a catastrophe.
def _plague_line(mitigated_nodes):
    _s = sim(civ="rome_100ad", capital=1000000.0)
    if mitigated_nodes:
        run_it(_s, *mitigated_nodes)
    _s.scholars, _s.artisans = 50.0, 200.0
    for _t in list(_s.employees):
        _s.employees[_t] = 50.0
    _s.rng = random.Random(1)          # a seed that rolls the 32% plague check
    _s.year = 165
    _s._shocks(165)
    return next((_m for _y, _m in _s.log if "Antonine plague" in _m), "")


_HEAVY = ["sanitation_antisepsis", "med_quarantine_sanitation", "germ_theory",
          "md2_isolation_hospital", "med_vaccination_progression",
          "md2_vaccine_smallpox", "md2_vaccine_plague", "md2_vaccine_typhoid",
          "md2_sand_filtration", "soap_hard", "med_nursing_profession",
          "plague_preparedness", "crop_rotation", "ag2_silage_silo",
          "fud_canning_appert_method"]
_line_none = _plague_line([])
_line_heavy = _plague_line(_HEAVY)
_line_some = _plague_line(["sanitation_antisepsis", "med_quarantine_sanitation"])
check("an unmitigated plague states its own historical rate plainly",
      "staff -28%" in _line_none, _line_none)
check("a heavily mitigated plague's OWN clause never re-quotes the "
      "historical -28% as if it were the outcome - only the near-zero "
      "figure the mechanic actually applied",
      "held off almost entirely" in _line_heavy
      and "would have been" not in _line_heavy
      and "staff -28%" not in _line_heavy.split(".")[0],
      _line_heavy)
check("a partially mitigated plague is 'softened', not 'held off almost "
      "entirely' and not silent about the hedge either",
      "softened by" in _line_some, _line_some)
check("the empire-wide toll is still told, in every case, as a separate "
      "fact explicitly not the household's own experience",
      all("Empire-wide, population -28%" in _l and "either way" in _l
          for _l in (_line_none, _line_heavy, _line_some)),
      (_line_none, _line_heavy, _line_some))
