"""SCENARIO: concerns (revenue-earning ventures) in a real game: a staffing closure keeps what it closed known, a concern reopened
soon pays the difference, `state` and `risk` warn of shut concerns and capabilities not operating, `mines` lists what you own,
a late-opened concern ramps from small, restore costs the tenth promised, mothball releases staff time, and opening a net-loss
concern says so.

Held as rule tests elsewhere: which concerns close and in what order, and that a part of a hand short closes nothing
(test_staffing_choice_rules); the grace window and its discounted fee (test_closure_grace_rules).

Regrouped from test_round8_fixes.py, test_round9.py, test_round10.py and test_round12_naive15.py; each check's own comment
records the break it guards.
"""
from .harness import *  # noqa: F401,F403
from sim.engine import category_traits
from sim.engine.units_prose import money_text
from sim.refusal import cause_of, facts_of


# Concerns that earn, tie up more craftsmen than the closure slack and need no foreman, and that a
# funded, staffed game can really open (a concern whose gate work is shut refuses, so is no use here).
_probe = unopened_sim(capital=500000.0)
_probe.done.update(NODES); _probe._done_changed()
_probe.artisans = _probe.scholars = 5.0
OPENABLE = []
for _id in sorted(NODES):
    if (_probe.is_venture(_id) and NODES[_id]["rev"] > 500
            and _probe.venture_hands(_id)[1] > _probe.STAFFING_CLOSURE_SLACK
            and _probe.venture_foreman(_id)[0] is None and _probe.venture_capex(_id) < 0.1 * _probe.capital
            and _probe.open_venture(_id)[0]):
        _probe.close_venture(_id)
        OPENABLE.append(_id)

# --- BREAK: when the staff ran short, the closer picked the concern that
# needed the MOST hands, which is very nearly the same as picking the most
# profitable one. A tester watched a 600-a-year wagon shop close twice while a
# concern earning nothing and staffed identically stayed open.
s_cl = unopened_sim(capital=200000.0)
_pair = [node_id for node_id in NODES
         if NODES[node_id]["rev"] > 0 and NODES[node_id]["up"] >= 0 and not NODES[node_id]["pre"]]
s_cl.done.update(NODES)                 # know everything, so `open` is free
s_cl.operating = set()
# only a concern that ties up more craftsmen than the closure slack can be closed for want of staff
_holders = [node_id for node_id in NODES if NODES[node_id]["rev"] > 0 and s_cl.is_venture(node_id)
            and s_cl.venture_hands(node_id)[1] > s_cl.STAFFING_CLOSURE_SLACK]
_rich = max(_holders, key=lambda node_id: NODES[node_id]["rev"] - NODES[node_id]["up"])
_poor = min(_holders, key=lambda node_id: NODES[node_id]["rev"] - NODES[node_id]["up"])
s_cl.operating.update([_rich, _poor])
s_cl.scholars = s_cl.artisans = 0
s_cl.founder_alive = False              # nobody at all: it must close both,
_shut = s_cl.close_unstaffed_ventures(200)      # and in the right ORDER
check("what the staffing closure closed is still KNOWN, only stopped",
      _rich in s_cl.done and _rich in s_cl.mothballed)

# --- BREAK: shed_loss_makers scanned `done`, so it could unlearn a concern
# that was already shut - saving nothing, since upkeep follows `operating`.
# (The positive cases are checked in round two, section C.)

# --- BREAK: staff attrition runs at 3.5% a year, so a household near the
# supervision line loses a concern most years and paid the full stock and
# premises to reopen it. A play tester watched four close at once, every year.
s_ch = unopened_sim(capital=500000.0)
s_ch.done.update(NODES); s_ch._done_changed()
s_ch.artisans = s_ch.scholars = 5.0
# a concern that earns, costs something to open and ties up more hands than the closure slack
_v = max(OPENABLE, key=s_ch.venture_capex)
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

# --- BREAK: twenty concerns, twenty-five years, income flat, because nothing
# said on the main screen what leaving them shut was costing.
s_sh = unopened_sim(capital=50000.0)
for _k in [node_id for node_id in NODES if s_sh.is_venture(node_id) and NODES[node_id]["rev"] > 0]:
    s_sh.done.add(_k)
s_sh._done_changed()
_plain = unopened_sim()
_stsh = S._agent_state(s_sh, NODES)
check("state says in money what your shut concerns would earn",
      _stsh.get("shut_concerns_would_earn_a_year", 0) > 0,
      _stsh.get("shut_concerns_would_earn_a_year"))
check("...and a player running everything is not nagged about it",
      S._agent_state(_plain, NODES).get("shut_concerns_would_earn_a_year") is None,
      S._agent_state(_plain, NODES).get("shut_concerns_would_earn_a_year"))

# --- THE GENERAL CASE the corpus bug was one instance of: has() gates the
# tree and the goal, running() gates the payout, and `shut_concerns` above
# only ever covered the payout being MONEY. A player who built patron_
# imperial and then let it close keeps appearing on `available` to have
# "a patron with soldiers" - has() never stops being true - while every
# running()-gated number that patron actually paid (protection, credit,
# state funding, status - update_protection and credit_limit in society.py
# and economy.py) silently went to zero, and nothing on any screen said so
# until this.
s_cg = unopened_sim(capital=50000.0)
# a capability institution that costs something to keep open (one that costs nothing never closes)
_patron = next(node_id for node_id in sorted(s_cg.NOT_OPERATING_BENEFIT)
               if node_id not in ("corpus_dispersed", "fin_university") and s_cg.is_venture(node_id)
               and not s_cg.mechanic(node_id, "capability").get("redundant_with"))
s_cg.done.add(_patron)
s_cg.done.add("corpus_dispersed")
s_cg._done_changed()
_cg_gaps = s_cg.capability_gaps()
check("a capability institution that is done but not operating is named, "
      "by id, with the specific benefit it is not collecting right now",
      {gap["id"] for gap in _cg_gaps} == {_patron, "corpus_dispersed"},
      _cg_gaps)
check("...and closes the moment the doors reopen - this is a LIVE check of "
      "running(), not a one-time note",
      (s_cg.operating.add(_patron),
       {gap["id"] for gap in s_cg.capability_gaps()})[1] == {"corpus_dispersed"},
      s_cg.capability_gaps())
s_cg.operating.discard(_patron)
check("plague_preparedness is not in the capability warning table: its "
      "protection is read through running() by hazard_relief, not paid as a "
      "capability benefit",
      "plague_preparedness" not in s_cg.NOT_OPERATING_BENEFIT,
      sorted(s_cg.NOT_OPERATING_BENEFIT))
_st_cg = S._agent_state(s_cg, NODES)
check("`state` - the screen a player rereads every year - carries this "
      "warning too, not only a command nobody runs unprompted",
      _st_cg.get("critical_capabilities_not_operating") is not None
      and {gap["id"] for gap in _st_cg["critical_capabilities_not_operating"]}
          == {"corpus_dispersed", _patron},
      _st_cg.get("critical_capabilities_not_operating"))
check("...and says nothing when every completed capability is open",
      S._agent_state(_plain, NODES).get(
          "critical_capabilities_not_operating") is None,
      S._agent_state(_plain, NODES).get("critical_capabilities_not_operating"))
_risk_cg = s_cg.knowledge_risk()
check("`risk` - the screen whose whole job is telling you what protects "
      "you - carries the same warning, independent of `state`",
      _risk_cg.get("critical_capabilities_not_operating") is not None
      and {gap["id"] for gap in _risk_cg["critical_capabilities_not_operating"]}
          == {"corpus_dispersed", _patron},
      _risk_cg.get("critical_capabilities_not_operating"))
check("the id named is never hidden under fog - a player has always "
      "already discovered anything in their own `done`",
      all(s_cg.is_visible(gap["id"]) for gap in _cg_gaps), _cg_gaps)

check("fin_university's sole benefit is shared (an `or`) with "
      "school_founded in update_protection, so it is only named while "
      "BOTH are closed, never while school_founded alone still covers it",
      (lambda s: (
          s.done.add("fin_university"), s.done.add("school_founded"),
          s.operating.add("school_founded"), s._done_changed(),
          "fin_university" not in {gap["id"] for gap in s.capability_gaps()})[-1]
      )(_plain),
      "checked fin_university/school_founded or-gate")

# --- BREAK: auto_mine took 353,039 a year against 467,227 of revenue and
# there was no command that named what you owned or what it cost.
s_mn = unopened_sim(capital=2000000.0)
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
# --- BREAK: "A concern you open reaches its full figure over 3 years" - and a
# concern built in 100 and opened in 130 was at full takings the day its doors
# opened, because the ramp read the year you worked it OUT. Delaying `open`
# was strictly better than opening promptly.
s_rp = unopened_sim(capital=500000.0)
_vr = OPENABLE[0]
s_rp.done.update(NODES); s_rp.done_year[_vr] = 100; s_rp._done_changed()
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
s_rs = unopened_sim(capital=500000.0)
s_rs.done.update(NODES); s_rs._done_changed()
s_rs.artisans = s_rs.scholars = 5.0
_vv = max(OPENABLE, key=s_rs.project_cost)
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

s_misc = unopened_sim(capital=1_000_000.0)

# --- BREAK 1: a fully-built concern worth ~1,500/yr that could never be
# opened because the founder was short 0.01 of a craftsman's supervision
# time, and `mothball` - the tool for freeing committed resources - refused
# to release the tiny holder on the grounds it had no money upkeep, so
# there was "nothing to save". The resource actually short was staff time,
# not money, and mothball asked about money alone.
_s_mb = s_misc
# every concern in the data now keeps up a share of its build bill, so the staff-time-only case is made
# by zeroing the money upkeep on this game's own copy of an openable concern
_mb_id = OPENABLE[0]
_s_mb.nodes[_mb_id]["up"] = 0.0
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
# A concern with genuinely nothing to save - no money upkeep, not running,
# so no staff held either - must still be refused honestly.
_s_mb2 = s_misc
_mb2_id = next(node_id for node_id, node in NODES.items()
               if node.get("up", 0) <= 0 and node.get("rev", 0) <= 0
               and node_id not in _s_mb2.granted
               and not (_s_mb2.never_abandon(node_id) and category_traits.has_trait(node["cat"], "never_abandoned")))
_s_mb2.done.add(_mb2_id); _s_mb2._done_changed()
_mb2_ok, _mb2_msg = _s_mb2.mothball_work(_mb2_id)
check("...but a thing with genuinely nothing to save (no money, no staff "
      "held) is still refused, honestly",
      not _mb2_ok and cause_of(_mb2_msg) == "nothing_to_save", _mb2_msg)

# --- BREAK: a Han playtester opened a net-loss concern four separate
# times, three of them after already having caught and written up the
# mistake once, because EARNS/YR and UPKEEP/YR sit side by side on every
# screen and nothing ever subtracts them for the reader. Flagged now, at
# the one moment a player could still back out - opening itself - for any
# ordinary venture where upkeep exceeds revenue even fully ramped up.
s_ln = s_misc
# the loss is judged on what the concern really earns and costs, as the opening message is
_ln_k = next((node_id for node_id in OPENABLE
              if s_ln.venture_real_upkeep(node_id) > s_ln.venture_real_earnings(node_id, fully_ramped=True)
              and node_id not in s_ln.CAPABILITY_INSTITUTIONS
              and all(need <= free for need, free in zip(s_ln.venture_hands(node_id), s_ln.venture_staff_free()))), None)
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
          and money_text(s_ln.venture_real_upkeep(_ln_k) - s_ln.venture_real_earnings(_ln_k, fully_ramped=True),
                         s_ln, grouped=True) in _ln_msg,
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
s_ln2 = s_misc
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
          _ln2_ok and facts_of(_ln2_msg)["net_loss_warned"] is False, _ln2_msg)
