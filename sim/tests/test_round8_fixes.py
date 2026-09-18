"""round8_fixes: split verbatim from the old test_regressions.py (original lines 3636-4891).

Moving contiguous blocks verbatim: no check below was reformatted, reworded or otherwise touched in the split.
"""
from .harness import *  # noqa: F401,F403

# ======================================================================
# ROUND 8: four fixes from the seventh break-testing round.
# ======================================================================

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

# --- BREAK: player-facing hazard notes quoted the values vector by its
# internal names ("raises w_magic_fear"), which is engine jargon a player has
# no way to read. Nothing shown to a player may name a values-vector key.
_JARGON = ("w_magic_fear", "w_eminence_danger", "w_religious_rigidity",
           "w_labour_saving", "w_commerce", "w_information", "w_novelty",
           "w_military", "adaptation_rate", "patronage_weight", "bribability")
_dirty = []
for _f in sorted(os.listdir(os.path.join(ROOT, "data/civilizations"))):
    if not _f.endswith(".json") or _f.startswith("_"):
        continue
    _civ = json.load(open(os.path.join(ROOT, "data/civilizations", _f)))
    for _h in _civ.get("hazards", []):
        _txt = " ".join(str(_h.get(x, "")) for x in ("name", "note"))
        _dirty += [(_f, _h.get("name"), _jargon_term) for _jargon_term in _JARGON if _jargon_term in _txt]
check("no hazard a player reads names an internal values-vector key",
      not _dirty, _dirty[:3])

# --- BREAK: `risk` offered `horse_collar` as a hedge against the Antonine
# plague with no word of why. Every entry must say what it leads to.
s_hz = sim()
_steps = []
for _kind in sorted(S.Sim.HAZARD_COUNTERS):
    _steps += s_hz.hedge_first_steps(_kind)
check("every hedge the game suggests says what it gets you",
      _steps and all(step.get("because_it_gives_you") for step in _steps),
      [step["id"] for step in _steps if not step.get("because_it_gives_you")][:3])
check("...and a prerequisite says which counter it is a step toward",
      any(str(step["because_it_gives_you"]).startswith("a step toward")
          for step in _steps))

# --- BREAK: a save written with the fog OFF loaded into a fogged game and
# handed the player the whole tree. The check has to run BEFORE the save's own
# fog flag is restored, or it validates the value it is about to reject.
_sv = "_fogtamper_test.json"          # saves must be relative paths
_svp = os.path.join(ROOT, _sv)
if os.path.exists(_svp):
    os.remove(_svp)
proto([{"cmd": "save", "file": _sv}])                       # written unfogged
_r8, _out8, _rc8 = proto([{"cmd": "load", "file": _sv}, {"cmd": "state"}],
                         fog=True)
check("a save played without fog cannot be loaded into a fogged game",
      any("fog" in json.dumps(x).lower() and x.get("ok") is False for x in _r8),
      _out8[:200])
check("...and refusing it does not kill the session", _rc8 == 0)
if os.path.exists(_svp):
    os.remove(_svp)

# ======================================================================
# ROUND 8b: the game saying what it did, and two attribute-level defects.
# ======================================================================

# --- BREAK: the patron-death guard read `_last_patron_death` and the body set
# `last_patron_death`, so the 25-year cooling-off never applied and the 5%
# roll fired every year for ever - the exact bug its comment claims to fix.
s_pd = sim(capital=50000.0, events=True)
s_pd.done.add("patron_local"); s_pd._done_changed()
s_pd.rng = random.Random(4)
_deaths = []
for _y in range(100, 400):
    s_pd.year = _y
    _before = len(s_pd.log)
    s_pd._random_events(_y)
    _deaths += [message for _, message in s_pd.log[_before:] if "patron dies" in message]
check("a patron cannot die twice inside the cooling-off period",
      len(_deaths) <= 300 // 25 + 1,
      "%d deaths in 300 years" % len(_deaths))
_years = [y for y, message in s_pd.log if "patron dies" in message]
check("...and the gap between them is at least the 25 years it promises",
      all(later_year - earlier_year > 25 for earlier_year, later_year in zip(_years, _years[1:])), _years)
check("a patron's death names what it cost you",
      not _years or any("courting cost" in message and "protection falls" in message
                        for _, message in s_pd.log if "patron dies" in message),
      [message for _, message in s_pd.log if "patron dies" in message][:1])

# --- BREAK: a fire and a raid announced themselves and left the player to
# diff their own state to find out whether anything had happened.
s_fx = sim(capital=10000.0, events=True)
s_fx.rng = random.Random(7)
for _y in range(100, 200):
    s_fx.year = _y
    s_fx._random_events(_y)
_dis = [message for _, message in s_fx.log if "fire in" in message or "banditry" in message]
check("a fire or a raid says what it took",
      _dis and all("denarii" in message or "holding none" in message for message in _dis),
      _dis[:2])

# --- BREAK: shed_loss_makers scanned `done`, so it could unlearn a concern
# that was already shut - saving nothing, since upkeep follows `operating`.
# (The positive cases are checked in round two, section C.)

# --- BREAK: auto_open threw away every refusal open_venture handed it, so a
# concern earning 150 against 15 of upkeep sat shut for six years in silence.
s_ao = sim(capital=1.0)
# Dear to open and plainly worth opening: auto_open must refuse it and SAY SO.
_v = max((node_id for node_id in NODES if NODES[node_id]["rev"] > NODES[node_id]["up"] > 0),
         key=lambda node_id: NODES[node_id]["rev"] - NODES[node_id]["up"])
s_ao.done.add(_v); s_ao._done_changed()
_opened = s_ao.auto_open_ventures()
check("auto_open opens nothing it cannot pay the capex on",
      _v not in _opened, (_v, _opened[:3]))
check("auto_open says why the best concern is still shut",
      any(_v in message for _, message in s_ao.log), [message for _, message in s_ao.log][:2])

# --- BREAK: auto_open_ventures blanket-refused EVERYTHING once a household
# owed more than half its credit line, including an already-completed,
# already-earning ordinary concern whose capex it could raise many times over
# and whose payback was months, not years. A traced Rome run built
# exp_trade_route_extend (cost 4,800, net +1,700/year, capex to open a
# further 1,800) by year 117 and then sat on it, unopened, for roughly 850
# years for exactly this reason: sunk capex earning nothing, ever.
s_deep = sim(capital=-50000.0)
_short = "hom_button"      # rev 400, up 8, capex ~31: weeks, not years
assert NODES[_short]["rev"] > NODES[_short]["up"], _short
s_deep.done.add(_short); s_deep._done_changed()
_cl_deep = s_deep.credit_limit()
check("the household in this check really is deep in arrears (over half its credit line)",
      s_deep.capital < 0 and -s_deep.capital > _cl_deep * 0.5,
      (s_deep.capital, _cl_deep))
_opened_deep = s_deep.auto_open_ventures()
check("a completed concern that pays for its own door within months opens "
      "even while deep in arrears",
      _short in _opened_deep, (_short, _opened_deep))

# ...and a genuinely slow one - the shape the ABANDONED-206 history is
# actually about - still does not, on the same deep-arrears household.
s_deep2 = sim(capital=-50000.0)
_long = "fin_stamp"             # rev 200, up 100, capex ~348: years to clear
assert NODES[_long]["rev"] > NODES[_long]["up"], _long
s_deep2.done.add(_long); s_deep2._done_changed()
_opened_deep2 = s_deep2.auto_open_ventures()
check("a completed concern that would take years to pay for its own door "
      "still stays shut while deep in arrears",
      _long not in _opened_deep2, (_long, _opened_deep2))
check("...and the refusal names its own payback period and what would clear it",
      any("pay for its own doors" in message and "clear enough debt" in message
          for _, message in s_deep2.log),
      [message for _, message in s_deep2.log])

# ...and an INSTITUTION - which is what the original ABANDONED-206 regression
# is actually about (a standing bleed against revenue you do not have) - stays
# exactly as blocked as before: this change only widens what an ordinary,
# already-earning concern is offered while deep in arrears, nothing else.
s_deep3 = sim(capital=-50000.0)
s_deep3.done.add("workshop_first"); s_deep3._done_changed()
_opened_deep3 = s_deep3.auto_open_ventures()
check("an institution still opens nothing while deep in arrears, exactly as before",
      "workshop_first" not in _opened_deep3, _opened_deep3)

# SPLIT-SUITE NOTE (not a content change, see this split's own report): the
# original monolithic file left a module-level `s` bound to an unrelated Sim
# from many hundreds of lines earlier (test_literacy_market_pricing.py's own
# `s = sim(civ="rome_100ad", capital=1e9)`), and the check just below reads
# `s.NITRE_COST_PER_M2` - a class constant (economy.py), not instance state -
# rather than `s_ni`, the Sim it actually builds two lines down. Almost
# certainly a copy-paste slip in the original; left exactly as found rather
# than silently fixed. Reproduced here (instead of a stray NameError) so the
# split changes nothing about what this check verifies.
s = S.Sim

# --- BREAK: `buy nitre`. Saltpetre is made, not mined, and there was no
# command that made any: only step(), which took 5% of a MANUAL player's
# capital every year they were short, silently.
s_ni = sim(capital=100000.0)
_laid = s_ni.build_nitre(20000)
check("nitre beds can be laid by hand, and cost what the quote says",
      _laid == 20000 and abs(s_ni.capital
                             - (100000.0 - 20000 * s.NITRE_COST_PER_M2
                                * s_ni.price_index)) < 1e-6,
      (_laid, s_ni.capital))
check("...and they actually supply saltpetre",
      s_ni._own_material_supply("nitre") > 0, s_ni._own_material_supply("nitre"))
s_ni2 = sim(capital=10.0)
check("...and one you cannot afford changes nothing at all",
      s_ni2.build_nitre(20000) == 0.0 and s_ni2.nitre_bed_m2 == 0.0
      and s_ni2.capital == 10.0,
      (s_ni2.nitre_bed_m2, s_ni2.capital))
_r_ni, _, _ = proto([{"cmd": "quote", "what": "nitre", "n": 20000},
                     {"cmd": "buy", "what": "nitre", "n": 20000},
                     {"cmd": "buy", "what": "nitre", "n": -1}])
check("the nitre quote and the nitre purchase agree on the price",
      _r_ni[0].get("to_lay_it") is not None
      and _r_ni[1].get("ok") is False,        # 400 denarii cannot buy 40,000
      (_r_ni[0].get("to_lay_it"), _r_ni[1].get("error")))
check("a negative nitre order is refused, not credited",
      _r_ni[2].get("ok") is False, _r_ni[2])

# --- BREAK: a MANUAL player's capital was spent on nitre beds by step().
s_mn = sim(capital=100000.0, manual=True)
s_mn.binding = "saltpetre"
_cap_before = s_mn.capital
s_mn.policy["auto_mine"] = False
for _ in range(3):
    s_mn.step()
check("with the automatic policies off, nothing lays a nitre bed but you",
      s_mn.nitre_bed_m2 == 0.0, s_mn.nitre_bed_m2)

# --- BREAK: "SHORT OF SALTPETRE: work at 5% of plan" for thirty years, with
# no way to find out what saltpetre was for or what would fix it.
s_rm = sim(capital=100000.0)
for _b in ("charcoal", "saltpetre", "iron"):
    _msg = s_rm.shortage_remedy(_b)
    check("a %s shortage names a command that would end it" % _b,
          "buy " in _msg or "quote " in _msg, _msg[:80])

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
from engine.protocol import _short_of_staff
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
from engine.protocol import render_pretty as _RP
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

# --- BREAK: a debasement announced itself and moved no price a player could
# see, because the model is in real terms. Say so, and name the real bite.
s_db = sim(capital=100000.0, events=True)
_before_price = s_db.project_cost("horse_collar")
while s_db.year < 210:
    s_db.step()
check("debasement does not move a real price quote (the model is real terms)",
      # TOLERANCE RESHAPED BY WIRING MILESTONE 4, AND MEASURED RATHER THAN
      # GUESSED. This window (100-210 AD, events=True) runs the Antonine
      # plague's staff_loss hazard through several annual waves, and
      # self.population - the age-cohort model that replaced the old scalar
      # pop_deficit - recovers between waves only through ordinary births
      # and deaths, with no separate exponential decay clock. Two waves a
      # few years apart therefore compound onto a slightly larger surviving
      # shortfall than the old arithmetic left, wage_index follows, and
      # horse_collar's residual labour sensitivity carries a little of that
      # into its quote.
      #
      # Measured, and identical on three consecutive runs (the simulation is
      # deterministic): 709.41000062578 -> 709.4100052577509, which is
      # 4.63e-06 absolute and 6.53e-09 RELATIVE.
      #
      # RELATIVE, not absolute. The old 1e-6 was an absolute bound on a
      # ~709-denarius quote, so its real strictness was 1.4e-09 relative and
      # would have drifted silently the moment horse_collar's cost changed
      # magnitude for any unrelated reason. 1e-7 relative keeps 15x headroom
      # over the measured residual and is still roughly six orders of
      # magnitude below a real debasement-scale move - Rome's own
      # real_erosion is 0.06, which on this quote would be ~42 denarii. The
      # check's actual point is covered at full strength by the two checks
      # below, which read the log's own words.
      abs(s_db.project_cost("horse_collar") - _before_price) / _before_price < 1e-7,
      (_before_price, s_db.project_cost("horse_collar")))
_dbm = [message for _, message in s_db.log if "coin is worth" in message]
check("...and the announcement says so, rather than leaving it to be found",
      _dbm and "do not move" in _dbm[0] and "your chest" in _dbm[0],
      _dbm[:1])
check("...and names what the debasement actually took this year",
      _dbm and ("denarii" in _dbm[0] or "holding none" in _dbm[0]), _dbm[:1])


# ======================================================================
# ROUND 8c: eminence had no lever, and "chance of ruin" was not the chance
# of ruin. Both play testers died to it and both described it the same way.
# ======================================================================

def _big(rep=98.0, em=39.0, yr=250, cap=5000000.0):
    big_sim = sim(capital=cap)
    big_sim.done.update(list(NODES)[:1400]); big_sim._done_changed()
    big_sim.reputation, big_sim.eminence, big_sim.year = rep, em, yr
    return big_sim

_em = _big()
_rep0, _em0 = _em.reputation, _em.eminence
_ok_w, _why_w = _em.withdraw_from_public_life()
check("there is a command that lowers prominence the year you use it",
      _ok_w and _em.eminence < _em0 * 0.6, (_em0, _em.eminence))
check("...and its price is reputation, not money",
      _em.reputation < _rep0 - 5 and abs(_em.capital - 5000000.0) < 1e-6,
      (_rep0, _em.reputation, _em.capital))
check("...but never below what the work you built is worth on its own",
      _em.reputation >= _em.standing_floor() - 1e-6,
      (_em.reputation, _em.standing_floor()))
check("...and it cannot be done twice in a decade",
      _em.withdraw_from_public_life()[0] is False,
      _em.withdraw_from_public_life()[1])
_em2 = _big()
_em2.year += _em2.WITHDRAW_EVERY + 1
check("...and can be done again once enough years have passed",
      _em2.withdraw_from_public_life()[0], _em2.year)

# It must not take the price when there is nothing to buy - the same rule
# `bribe` learned the hard way.
_quiet = _big(rep=40.0, em=1.0)
_rq = _quiet.reputation
check("withdrawing when nobody is watching is refused, not charged",
      _quiet.withdraw_from_public_life()[0] is False
      and _quiet.reputation == _rq,
      (_quiet.reputation, _rq))

# The settling point was ABOVE the danger line, which is a promise that a
# successful run dies. Familiarity - the model's own measure of how
# unsurprising you have become - now damps it.
_fam = _big()
_fam.familiarity = 0.0
_cold = _fam.prominence_hazard()
_fam.familiarity = 0.9
_warm = _fam.prominence_hazard()
check("a city that has watched you for a century is less alarmed by you",
      _warm < _cold * 0.92, (_cold, _warm))
# A sixth off, not a third: the first attempt at this damping took the hazard
# so far down that a break tester measured three thousand run-years with the
# sum of every reported chance of ruin at exactly 0.00.
check("...but never stops being alarmed altogether",
      _warm > _cold * 0.8, (_cold, _warm))
# The shape that matters: build the counter and you sit under the line;
# do not and you sit well over it.
_em_shape = {}
for _acad in (False, True):
    _s = sim(capital=50000000.0)
    _s.done.update(list(NODES)[:1400])
    run_it(_s, "patron_imperial", "academy_network")
    if not _acad:
        _s.done.discard("academy_network")
        _s.operating.discard("academy_network")
    _s._done_changed()
    _s.reputation, _s.year, _s.familiarity = 98.0, 400, 0.9
    _em_shape[_acad] = _s.eminence_report()["settles_at_if_nothing_changes"]
check("a great man near the throne who built no academies is over the line",
      _em_shape[False] > sim().cfg["eminence_danger"], _em_shape)
check("...and the same man who built them is under it",
      _em_shape[True] < sim().cfg["eminence_danger"], _em_shape)

# "7% chance of ruin" was the chance SOMETHING landed; four fifths of those
# are survivable. A play tester survived two and was ended by the third.
_rep = _big().eminence_report()
check("the report separates 'something happens' from 'the run ends'",
      _rep["chance_the_run_ENDS_this_year"] < _rep["chance_of_ruin_this_year"],
      (_rep["chance_of_ruin_this_year"], _rep["chance_the_run_ENDS_this_year"]))
check("...and says which outcomes there are and how likely each is",
      abs(sum(_rep["if_it_lands_it_is"].values()) - 1.0) < 1e-9,
      _rep["if_it_lands_it_is"])
check("...and names the lever, by the word you would type",
      "withdraw" in str(_rep["the_one_lever"]), _rep["the_one_lever"])

# It has to survive a save, or a --session game gets a free retirement a year.
_wsv = "_withdrawtest.json"
_wsvp = os.path.join(ROOT, _wsv)
if os.path.exists(_wsvp):
    os.remove(_wsvp)
_rw, _, _ = proto([{"cmd": "withdraw"}, {"cmd": "save", "file": _wsv},
                   {"cmd": "load", "file": _wsv}, {"cmd": "withdraw"}])
check("a retirement cannot be repeated by saving and reloading",
      _rw[-1].get("ok") is False, _rw[-1])
if os.path.exists(_wsvp):
    os.remove(_wsvp)


# ======================================================================
# ROUND 8d: things the game said that were not true, and levers it lacked.
# ======================================================================

# --- BREAK: "waiting on money" while holding 73,234,107 denarii against
# 45,448 owed. step() pays at most one year's instalment - the cost over the
# node's calendar floor - so a ten-year work absorbs a tenth a year however
# rich you are, and nothing anywhere said there was a pace at all.
from engine.protocol import _waiting_on as _WO
s_pace = sim(capital=50000000.0)
_slow = "academy_network"
s_pace.active[_slow] = dict(ph_left=0.0, yrs=1.0, spent=0.0,
                            cost_left=s_pace.project_cost(_slow))
_msg_rich = _WO(s_pace, NODES, _slow, s_pace.active[_slow],
                s_pace.active[_slow]["cost_left"])
check("a rich player is told the pace, not that they are short of money",
      "pace" in _msg_rich and "a year" in _msg_rich, _msg_rich)
check("...and is told how many more years that pace needs",
      "year" in _msg_rich and any(char.isdigit() for char in _msg_rich), _msg_rich)
s_broke = sim(capital=1.0)
s_broke.credit_limit = lambda: 0.0
s_broke.active[_slow] = dict(ph_left=0.0, yrs=1.0, spent=0.0,
                             cost_left=s_broke.project_cost(_slow))
_msg_poor = _WO(s_broke, NODES, _slow, s_broke.active[_slow],
                s_broke.active[_slow]["cost_left"])
check("...and a player who really cannot raise the instalment is told that",
      _msg_poor.startswith("money"), _msg_poor)

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

# --- BREAK: the run ended with one sentence and then a queue of identical
# refusals. A play tester started a whole second game with the fog off just to
# learn how far along the road they had died.
s_fin = sim()
s_fin.year = 600
from engine.protocol import final_report as _FRPT, render_final as _RF
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

# --- BREAK: `_TECH_EFFECTS` offered as a playable civilisation.
_civerr = ""
try:
    S.load_civ("rome")
except SystemExit as e:
    _civerr = str(e)
check("the reference data files are not offered as civilisations to play",
      "_TECH_EFFECTS" not in _civerr and "rome_100ad" in _civerr, _civerr)


# --- BREAK: the Mexica menu says "no draught animals, no iron, no wheel in
# practical use" and horse_collar was startable on arrival in the Valley of
# Mexico in 1500, with `why` still calling it a collar for a draught horse.
_mex = sim(civ="mexica_1500")
_HORSE = "horse_collar"
_ok_h, _why_h = _mex.start_reason(_HORSE)
check("a society with no draught animal cannot begin draught-animal work",
      not _ok_h and "draught animal" in _why_h, _why_h)
check("...and the refusal names the one thing that would open it",
      "exp_import_draught_animals" in _why_h, _why_h)
check("...and it is not in what you could begin today",
      not any(entry["id"] == _HORSE
              for entry in S._agent_available(_mex, NODES, {"all": True})["available"]),
      _HORSE)
_mex.done.add("exp_import_draught_animals"); _mex._done_changed()
check("...and bringing the animals across opens all of it at once",
      _mex.needs_first(_HORSE)[0] is None, _mex.needs_first(_HORSE))
_rom = sim(civ="rome_100ad")
check("a society that HAS horses is not gated at all (the control case)",
      _rom.needs_first(_HORSE)[0] is None, _rom.needs_first(_HORSE))
# Every gate has to be liftable, or it is a wall rather than a handicap.
for _cf in sorted(os.listdir(os.path.join(ROOT, "data/civilizations"))):
    if not _cf.endswith(".json") or _cf.startswith("_"):
        continue
    _cv = json.load(open(os.path.join(ROOT, "data/civilizations", _cf)))
    for _lbl, _ent in (_cv.get("needs_first") or {}).items():
        if _lbl.startswith("_"):
            continue
        check("%s: the '%s' gate names a real node that lifts it"
              % (_cv["id"], _lbl),
              _ent.get("node") in NODES and _ent["node"] not in (_ent.get("ids") or []),
              _ent.get("node"))
        check("%s: every id behind the '%s' gate is a real node"
              % (_cv["id"], _lbl),
              all(x in NODES for x in (_ent.get("ids") or [])),
              [x for x in (_ent.get("ids") or []) if x not in NODES])


# ======================================================================
# ROUND 8e: three answers to "can I afford this", and advice you cannot take.
# ======================================================================

s_af = sim(capital=400.0)
check("there is ONE affordability rule, and it says which it is using",
      abs(s_af.spending_power("buy") - (400.0 + s_af.credit_limit() * 0.5)) < 1e-6
      and abs(s_af.spending_power("start") - (400.0 + s_af.credit_limit())) < 1e-6,
      (s_af.spending_power("buy"), s_af.spending_power("start")))
_q, _, _ = proto([{"cmd": "quote", "what": "mine", "material": "coal", "n": 500},
                  {"cmd": "available"}])
check("quote counts the credit a lender would actually advance",
      _q[0].get("you_could_raise", 0) > _q[0].get("you_have", 0), _q[0].get("you_could_raise"))
check("...and says what its 'afford' figure means",
      "credit" in str(_q[0].get("afford_means")), _q[0].get("afford_means"))
_hint = str((_q[1].get("to_see_more") or {}).get("what you can pay for", ""))
check("the AFFORD hint uses the rule `start` uses, since it is about starting",
      str(int(sim(capital=400.0).spending_power("start"))).replace(",", "")
      in _hint.replace(",", ""), _hint)

# --- BREAK: the arrears banner quoted 46 a year against a ledger Net/yr of
# -159.5, because it left out the interest that exists BECAUSE of the arrears.
s_ar = sim(capital=-4000.0)
s_ar.insolvent_years = 20
s_ar.revenue = lambda: 0.0
_diag = s_ar.stall_diagnosis()
_led = (s_ar.revenue() - s_ar.upkeep() - s_ar.living_cost()
        - s_ar.mine_operating_cost()
        - max(0.0, -s_ar.capital) * s_ar.debt_interest_rate())
check("the arrears banner quotes the same loss the ledger does",
      _diag and "{:,.0f}".format(-_led) in _diag["you_are_stuck"],
      (_diag or {}).get("you_are_stuck"))
check("...and names the part of it that is interest on the arrears themselves",
      any("interest on the arrears" in reason for reason in _diag["what_would_change_it"]),
      _diag["what_would_change_it"])

# --- BREAK: the banner recommended wage work, and `work` answered the player
# who took it with "this cost you 50. Wage work is for when you have no
# practice to lose." The game recommended a mistake and then named it as one.
s_w = sim(capital=-4000.0)
s_w.insolvent_years = 20
_dw = s_w.stall_diagnosis()
_wages = [reason for reason in (_dw or {}).get("what_would_change_it", [])
          if reason.startswith("work as a ")]
if _wages:
    _trade = _wages[0].split("work as a ")[1].split(":")[0].strip()
    _pay, _note = sim(capital=-4000.0).work_for_wages(_trade, 2000)
    check("the trade the banner names is one that actually gains",
          not (_note and "cost you" in _note), (_trade, _note))
else:
    check("the banner does not recommend wage work when it would lose money",
          True, "not offered")

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

# --- BREAK: an idle million bled 15,000 a year with nothing anywhere saying why.
_rr, _, _ = proto([{"cmd": "money"}], kit="absurd")
check("the ledger names the part of your living costs that is your wealth",
      (_rr[0].get("what_it_costs_you") or {}).get("_of_which_because_you_are_rich", 0) > 1000,
      _rr[0].get("what_it_costs_you"))

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


# ======================================================================
# ROUND 8f: screens that disagreed with each other.
# ======================================================================

# --- BREAK: "(these add up to the revenue above)" - 166.7 + 66.7 = 233.4
# under a stated 233.5. A claim of exact addition, checkable in one line.
for _civ_name in ("rome_100ad", "han_china_100ad", "norse_900ad", "england_1300"):
    _s = sim(civ=_civ_name, capital=200000.0)
    for _i, _k in enumerate(node_id for node_id in NODES if NODES[node_id]["rev"] > 0):
        if _i >= 6:
            break
        _s.done.add(_k); _s.operating.add(_k)
    _s._done_changed()
    _src = _s.revenue_sources()
    _sum = sum(value for value in _src.values() if isinstance(value, (int, float)))
    check("%s: the ledger rows add up to the revenue they are printed under"
          % _civ_name, abs(_sum - _s.revenue()) < 0.05, (_sum, _s.revenue()))

# --- BREAK: "market can supply 22,500 hours", then 24,500 after hiring one
# smith. market_supply is hours available TO YOU, your own staff included.
s_ms = sim(capital=200000.0)
_town0, _mine0 = s_ms.market_supply_split("smith")
s_ms.hire("smith", 1)
_town1, _mine1 = s_ms.market_supply_split("smith")
check("hiring does not conjure more of a trade into the town",
      abs(_town0 - _town1) < 1e-6, (_town0, _town1))
check("...and what your own people add is counted separately",
      _mine1 > _mine0 and abs(_town1 + _mine1 - s_ms.market_supply("smith")) < 1e-6,
      (_mine0, _mine1, s_ms.market_supply("smith")))

# --- BREAK: after `hire smith 1`, `labour` dropped smith from YOU COULD HIRE,
# which reads as "no more smiths available" - and `hire smith 1` still worked.
_rl, _, _ = proto([{"cmd": "hire", "trade": "smith", "n": 1}, {"cmd": "labour"}])
check("a trade you employ is still listed as one you could hire",
      "smith" in (_rl[1].get("you_could_hire_here") or []),
      _rl[1].get("you_could_hire_here"))


# ======================================================================
# ROUND 8g: two losses a player could not see coming or prevent.
# ======================================================================

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

# --- BREAK: six projects wiped in one year. The countdown to abandonment ran
# silently for three years and then took everything spent.
s_hl = sim(capital=500000.0)
_need_eng = "ag2_cold_store"
s_hl.active[_need_eng] = dict(ph_left=float(NODES[_need_eng]["ph"]), yrs=0.0,
                              spent=0.0, cost_left=s_hl.project_cost(_need_eng))
s_hl.step()
check("a project that cannot go on says so the first year, not the fourth",
      any(_need_eng in message and "before it is abandoned" in message for _, message in s_hl.log),
      [message for _, message in s_hl.log][:2])
_st_all = S._agent_state(s_hl, NODES)
_st_hl = _st_all["active"][_need_eng]
check("...and state carries the countdown and the trade that would save it",
      _st_hl.get("will_be_abandoned_in_years") == 3
      and "engineer" in (_st_hl.get("because_nobody_here_can") or []),
      _st_hl)
check("...and the page says the one command that keeps your hours",
      "stop %s" % _need_eng in _RP("state", _st_all),
      [line for line in _RP("state", _st_all).splitlines() if "ABANDONED" in line])


# --- BREAK: the advice on how to get artisans said "build workshop_first (you
# need somewhere for them to work)" while `why workshop_first` said it was
# blocked for want of artisans. A play tester quoted the two lines at each
# other.
s_circ = sim()
s_circ.done.add("patron_local"); s_circ._done_changed()
_adv = s_circ._staff_advice("artisans")
check("advice never points at a remedy waiting on the thing it supplies",
      "workshop_first" not in _adv or "waiting on artisans" in _adv, _adv)
s_circ.artisans = 20.0
check("...and names it plainly once it is actually reachable",
      "waiting on artisans" not in s_circ._staff_advice("artisans"),
      s_circ._staff_advice("artisans"))
check("giving that advice does not recurse into itself",
      isinstance(sim().start_reason("workshop_first")[1], str), "no RecursionError")

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


# ======================================================================
# ROUND 8h: mechanics that only announced themselves after they had bitten.
# ======================================================================

# --- BREAK: a recoverable cash dip became "CREDIT EXHAUSTED: 4 projects
# halted" and a forty-year dead run. "money shows a credit limit but nothing
# shows how close to insolvency you are."
s_lim = sim()
s_lim.capital = -s_lim.credit_limit() * 0.75
s_lim.warn_near_the_limit(105)
check("the credit limit warns you BEFORE you cross it",
      any("CLOSE TO THE LIMIT" in message for _, message in s_lim.log), [message for _, message in s_lim.log])
check("...and names what you could still do about it",
      any("stop" in message and "mothball" in message for _, message in s_lim.log),
      [message for _, message in s_lim.log][:1])
_n_before = len(s_lim.log)
s_lim.warn_near_the_limit(106)
check("...and does not say it again every year",
      len(s_lim.log) == _n_before, len(s_lim.log) - _n_before)
s_ok = sim()
s_ok.warn_near_the_limit(105)
check("a solvent player is not warned about a limit they are nowhere near",
      not s_ok.log, [message for _, message in s_ok.log])
_rm, _, _ = proto([{"cmd": "money"}])
check("the ledger says how much of the credit line is used",
      _rm[0].get("of_that_limit_you_have_used") is not None,
      _rm[0].get("of_that_limit_you_have_used"))

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

# --- BREAK: the founder's year quietly grew from 2,000 hours to 10,175 and
# nothing ever said so - the largest change to the resource the game is built
# on, noticed by accident.
def _deputies_are_announced():
    deputies_sim = sim(capital=2000000.0, manual=False)
    run_it(deputies_sim, "school_founded", "patron_imperial", "academy_network")
    for _ in range(30):
        deputies_sim.step()
    said = [message for _, message in deputies_sim.log if "deput" in message]
    return (any("deput" in message and "your year is" in message for _, message in deputies_sim.log)
            and len(said) <= int(deputies_sim.directors_extra) + 1, said[:1])

slow_check("gaining a deputy is announced with what it does to your year, "
           "once per whole deputy rather than every year",
           _deputies_are_announced)

# --- BREAK (naive15/england): "hire smith 2 was flatly REFUSED with 'costs
# 495 pence in advance and you have -1697' ... even though my credit limit
# had lots of headroom" - the asymmetry (hire/train/commission may draw only
# half the credit line; start may draw the whole of it) is deliberate and
# documented (economy.py: spending_power - a lender funds work already under
# way, not a payroll or a one-off fee), so the fix is the message, not the
# arithmetic: it must say WHICH rule this is and WHY, not just decline.
#
# RECALIBRATED for the spending_power consolidation: this block used to set
# capital to "just past hire's half-line room" using hire's OWN inline
# capital+credit_limit()*0.5 - the very arithmetic that turned out to be one
# of seven copies of this rule, and the one that (unlike economy.py's
# canonical spending_power) never floored capital at zero. Under that inline
# copy, room kept shrinking as debt deepened, with nothing stopping it going
# negative; under the canonical rule a household already in the hole is
# floored at zero before the credit-line share is added, so the room hire,
# train and commission actually allow is a FIXED half a credit line
# regardless of how deep the debt already is - deeper debt no longer makes
# hiring, training or commissioning any harder than shallower debt does. So
# "just past half-line room" is no longer a function of capital at all: pick
# a fee between spending_power("buy") (what hire/train/commission may draw)
# and spending_power("start") (what only a project may draw) and it is
# refused, however deep in debt the household already is.
s_asym = sim(capital=0.0)
s_asym.capital = -50000.0   # deep in debt - the fix is that this no longer matters
_ok_h, _msg_h = s_asym.hire("smith", 3)   # 3 smiths: between half and whole the line
check("a cash-short hire is still refused (the asymmetry itself is kept, "
      "not loosened)", _ok_h is False, (_ok_h, _msg_h))
check("...but the refusal now says WHICH rule this is: half the credit "
      "line, not all of it",
      "half" in _msg_h and "credit line" in _msg_h, _msg_h)
check("...and WHY: a lender funds work under way (what starting a project "
      "can point to), not a payroll or a one-off fee",
      "work already under way" in _msg_h
      and ("payroll" in _msg_h or "wage" in _msg_h), _msg_h)
_fee_h = 3.0 * S.ANNUAL_WAGE.get("smith", 375.0) * s_asym.wage_index * s_asym.price_index \
    * s_asym.labour_price_factor("smith")
check("...and still states the plain facts a refusal always has: the exact "
      "cost hire() actually computed",
      "{:,.0f}".format(round(_fee_h)) in _msg_h, (_fee_h, _msg_h))
# The identical family (train's keep-fed fee, commission's job fee) shares
# the SAME wording, written once, so the three cannot drift apart from each
# other or from the reasoning behind them (rather than each re-deriving its
# own spending_power comparison AND its own separate explanation).
_ok_t, _msg_t = s_asym.train("machinist", 3, None)
check("train's cash-short refusal uses the identical reasoning as hire's, "
      "not a second wording for the same rule",
      _ok_t is False and "half" in _msg_t and "work already under way" in _msg_t,
      _msg_t)
s_asym2 = sim(capital=0.0)
s_asym2.capital = -50000.0
_ok_c, _msg_c = s_asym2.commission("smith", 3500.0)
check("commission's cash-short refusal uses the same reasoning too",
      _ok_c is False and "half" in _msg_c and "work already under way" in _msg_c,
      _msg_c)

# --- BREAK (verified against the real engine): the arithmetic
# `self.capital + self.credit_limit() * 0.5` was written out, by hand, at six
# sites in labour.py and protocol.py (a seventh, in projects.py, agreed today
# only by luck), instead of calling economy.py's spending_power("buy") - the
# function whose own docstring names it as the fix for this exact class of
# bug. None of the six inline copies floored capital at zero the way
# spending_power does, so at capital=-500, credit_limit()=210 the quote
# screens (which always called spending_power) said "you could raise 105"
# while hire/train/commission computed -395 and refused any fee at all,
# telling the same household it was "about 475 short" of a fee it could
# plainly afford. Two things have to be shown: that the seven sites now
# route through the one function (so the next change to the rule cannot
# drift again), and that this actually flips what a household in debt is
# allowed to do.
import inspect as _insp_sp
from engine import labour as _sp_labour, projects as _sp_projects

# TWO QUESTIONS, NOT ONE, AND THE KIND IS THE WHOLE POINT. "buy" counts the
# debt already carried, because a wage or a commission buys nothing back.
# "open" does not, because a door on a concern that is already built and
# already earning pays for its own fee - and gating that on arrears is what
# left a tester's seven finished concerns shut and a Rome run's trade route
# unopened for 850 years. A site asking the wrong one of these is a bug in
# either direction, so the guard names the kind rather than merely checking
# that SOME spending_power call is present.
_SPENDING_POWER_SITES = [
    (_sp_labour.LabourMixin._cash_in_hand_refusal, "labour._cash_in_hand_refusal", "buy"),
    (_sp_labour.LabourMixin.hire, "labour.hire", "buy"),
    (_sp_labour.LabourMixin.train, "labour.train", "buy"),
    (_sp_labour.LabourMixin.auto_commission_for_blocked,
     "labour.auto_commission_for_blocked", "buy"),
    (_sp_labour.LabourMixin.commission, "labour.commission", "buy"),
    (_sp_projects.ProjectsMixin.auto_open_ventures, "projects.auto_open_ventures", "open"),
    (_sp_projects.ProjectsMixin.open_venture, "projects.open_venture", "open"),
]
for _sp_fn, _sp_name, _sp_kind in _SPENDING_POWER_SITES:
    _sp_src = _insp_sp.getsource(_sp_fn)
    check("%s asks spending_power(%r) - the right one of the two questions - "
          "and does not reimplement the arithmetic" % (_sp_name, _sp_kind),
          ('spending_power("%s")' % _sp_kind) in _sp_src
          and "self.capital + self.credit_limit()" not in _sp_src,
          "checked %s's own source" % _sp_name)
_wo_src = _insp_sp.getsource(_WO)
check("protocol._waiting_on's stalled-project pacing message calls "
      "spending_power() too, not its own copy of the arithmetic",
      "spending_power(" in _wo_src
      and "s.capital + s.credit_limit()" not in _wo_src,
      "checked _waiting_on's own source")

# The bug's own worked example, run for real: a household owing 500 against
# a 210 credit line. It can raise NOTHING - it is already past the line, and
# credit_limit() is how far into arrears anyone will let you go, not headroom
# to add on top of the hole. hire/train/commission always had this right and
# computed it inline; spending_power() floored the capital term and so told
# every quote screen the household could still raise 105. The screen was the
# liar, not the six commands.
s_bug = sim(capital=0.0)
s_bug.capital = -500.0
s_bug.credit_limit = lambda: 210.0
_sp_bug = s_bug.spending_power("buy")
check("spending_power('buy') counts the debt already carried: 500 into a "
      "210 line can raise nothing, where the floored version said 105",
      abs(_sp_bug - 0.0) < 1e-9, _sp_bug)
_sp_solvent = sim(capital=0.0)
_sp_solvent.capital = 400.0
_sp_solvent.credit_limit = lambda: 210.0
check("...and it is still capital plus half the line when there is no hole "
      "to count - 400 + 105",
      abs(_sp_solvent.spending_power("buy") - 505.0) < 1e-9,
      _sp_solvent.spending_power("buy"))
_fph_bug = WAGES["smith"] * 1.6 * s_bug.wage_index * s_bug.price_index \
    * s_bug.labour_price_factor("smith")
s_bug_u = sim(capital=0.0)
s_bug_u.capital = -500.0
s_bug_u.credit_limit = lambda: 210.0
_ok_bu, _msg_bu = s_bug_u.commission("smith", 1.0)
check("...and commission() refuses a household already past its line, which "
      "is what it always did - the fix made the SCREEN agree with it, not "
      "the other way round",
      _ok_bu is False, (_ok_bu, _msg_bu))
s_bug_o = sim(capital=0.0)
s_bug_o.capital = -500.0
s_bug_o.credit_limit = lambda: 210.0
s_bug_o.capital = 400.0            # out of the hole, same 210 line
_ok_bo, _msg_bo = s_bug_o.commission("smith", 9999.0)
check("...and still refuses a fee over the half-line once the household is "
      "solvent again - the rule itself is unchanged, only how it is computed",
      _ok_bo is False, (_ok_bo, _msg_bo))

# auto_commission_for_blocked's own guard (labour.py:1753, called from
# step() - this is the one of the seven that changes what the OPTIMISER
# does, not just what a typed command is told).
s_gate = sim(capital=0.0)
s_gate.capital = -1000.0
s_gate.credit_limit = lambda: 0.0   # spending_power("buy") is exactly zero
check("auto_commission_for_blocked refuses outright the moment "
      "spending_power('buy') is exactly zero - the same threshold hire, "
      "train and commission use, not a separately-drifting zero-credit case",
      s_gate.spending_power("buy") == 0.0
      and s_gate.auto_commission_for_blocked() is None,
      s_gate.spending_power("buy"))

# protocol.py's stalled-project "why": a household 50,000 in debt but with a
# real 2,000 line and an installment (900/yr) it can actually service should
# be told the PACE is what is holding the project up, not that it lacks the
# money - which is exactly what the old inline copy (capital+credit*0.5 =
# -49,000, never floored) got backwards.
_slow_pace = "academy_network"
s_pace2 = sim(capital=0.0)
s_pace2.capital = -50000.0
s_pace2.credit_limit = lambda: 2000.0
s_pace2.project_cost = lambda node_id: 9000.0
s_pace2.active[_slow_pace] = dict(ph_left=0.0, yrs=1.0, spent=0.0, cost_left=9000.0)
_msg_pace_deep = _WO(s_pace2, NODES, _slow_pace, s_pace2.active[_slow_pace], 9000.0)
check("a household 50,000 past a 2,000 line is told MONEY is what holds the "
      "project up - it can raise nothing, and saying 'pace' there would be "
      "the same lie the quote screen used to tell",
      "money" in _msg_pace_deep, _msg_pace_deep)

# --- The player-visible symptom itself: the number `quote`/`why`/`state`
# show (protocol._spare_capacity's "you_could_raise_right_now", built from
# spending_power("buy")) has to be the SAME number hire actually enforces -
# not a screen that says one thing while the command does another.
s_sym = sim(capital=0.0)
s_sym.capital = -50000.0
_quoted = _protocol._spare_capacity(s_sym, {})["you_could_raise_right_now"]
check("the affordability figure the quote screen shows while in debt "
      "matches spending_power('buy') exactly",
      abs(_quoted - s_sym.spending_power("buy")) < 0.05,
      (_quoted, s_sym.spending_power("buy")))
_pph_sym = S.ANNUAL_WAGE.get("smith", 375.0) * s_sym.wage_index * s_sym.price_index \
    * s_sym.labour_price_factor("smith")
_n_under_sym = max(1, int(_quoted // _pph_sym))
_n_over_sym = _n_under_sym + 2
s_sym_u = sim(capital=0.0)
s_sym_u.capital = -50000.0
_ok_su, _msg_su = s_sym_u.hire("smith", _n_under_sym)
check("...and when that figure is zero because the household is past its "
      "line, hire() refuses too - screen and command say the same no",
      (_quoted <= 0.0) == (_ok_su is False), (_quoted, _ok_su, _msg_su))
s_sym_ok = sim(capital=0.0)
s_sym_ok.capital = 20000.0
_quoted_ok = _protocol._spare_capacity(s_sym_ok, {})["you_could_raise_right_now"]
_ok_sok, _msg_sok = s_sym_ok.hire("smith", 1)
check("...and a solvent household the screen says can raise thousands really "
      "is let through by hire(), so the agreement is not just 'both refuse'",
      _quoted_ok > 1000.0 and _ok_sok is True, (_quoted_ok, _ok_sok, _msg_sok))
s_sym_o = sim(capital=0.0)
s_sym_o.capital = -50000.0
_ok_so, _msg_so = s_sym_o.hire("smith", _n_over_sym)
check("...and a hire past what the quote screen says the household could "
      "raise really is refused, so the two numbers cannot silently disagree "
      "again",
      _ok_so is False, (_quoted, _msg_so))

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


# --- BREAK: F34, "numbers that do not reconcile, collected". Every one of
# these was a subtraction a break tester did on figures printed together.
_rn2, _, _ = proto([{"cmd": "hire", "trade": "smith", "n": 2},
                    {"cmd": "labour"},
                    {"cmd": "work", "trade": "scribe", "hours": 500},
                    {"cmd": "start", "id": "units_standards"},
                    {"cmd": "step", "years": 1},
                    {"cmd": "money"}], kit="absurd")
_lab = _rn2[1]
_rows = {record["trade"]: record for record in (_lab.get("on_your_staff") or [])}
if "smith" in _rows:
    check("the wage bill is the quoted wage times the number of people",
          abs(_rows["smith"]["a_year_of_one"] * _rows["smith"]["you_employ"]
              - _lab["annual_wage_bill"]) < 1.0,
          (_rows["smith"], _lab["annual_wage_bill"]))
_wk = _rn2[2]
check("work's three figures subtract to each other",
      abs((_wk["earned"] - _wk["it_cost_your_own_practice"])
          - _wk["so_you_are_up"]) < 0.051, _wk)
_mn = _rn2[5]
check("money's net before and after the work in hand differ by exactly that",
      abs((_mn["net_per_year"] - _mn["spent_on_projects_last_year"])
          - _mn["net_after_project_spend"]) < 0.11, _mn)
_st2, _, _ = proto([{"cmd": "state"}], kit="absurd")
check("...and the after figure is the one `state` prints, to the decimal",
      "net_after_project_spend" in _st2[0], list(_st2[0])[:5])


# --- BREAK: `why med_cataract_couching` said "REVENUE: 500 den/yr" beside a
# ledger crediting 166.7 for the same node - `why` overstating income
# threefold, as a break tester put it.
_rwy, _, _ = proto([{"cmd": "why", "id": "med_cataract_couching"}])
check("why says what a practice node pays YOU, not only what the trade is worth",
      _rwy[0].get("but_it_pays_YOU") is not None
      and _rwy[0]["but_it_pays_YOU"] < _rwy[0]["revenue"],
      (_rwy[0].get("revenue"), _rwy[0].get("but_it_pays_YOU")))
_st_r, _, _ = proto([{"cmd": "money"}])
_led = _st_r[0].get("where_the_money_comes_from") or {}
check("...and that figure is the ledger's, to the decimal",
      abs(_rwy[0]["but_it_pays_YOU"]
          - _led.get("med_cataract_couching", -1)) < 0.11,
      (_rwy[0].get("but_it_pays_YOU"), sorted(_led)[:4]))
_rwy2, _, _ = proto([{"cmd": "why", "id": "horse_collar"}])
check("...and a node that is NOT your practice carries no such line",
      _rwy2[0].get("but_it_pays_YOU") is None, _rwy2[0].get("but_it_pays_YOU"))

# --- BREAK: `ventures` "1 scholars, 1 craftsmen" on the same screen as
# `labour`'s "ON YOUR STAFF: nobody". Three screens, three counts.
_rv2, _, _ = proto([{"cmd": "ventures"}, {"cmd": "labour"}])
check("the free-hands count says that one of them is you",
      _rv2[0].get("one_of_each_of_those_is_you") is True
      and _rv2[1].get("you_employ_in_total") == 0,
      (_rv2[0].get("people_free_to_run_something_new"),
       _rv2[1].get("you_employ_in_total")))

# --- BREAK: two settlements each announced "reputation -12" against a
# reputation of 4.9, and the second did nothing at all.
s_ins = sim(capital=-99999.0)
s_ins.reputation = 4.9
s_ins.insolvent_years = 30
s_ins.enforce_credit_limit(150)
_m1 = [message for _, message in s_ins.log if "INSOLVENCY" in message][-1]
check("a reputation penalty announces what it actually took",
      "-4.9" in _m1, _m1)
s_ins.capital = -99999.0
s_ins.insolvent_years = 30
s_ins.enforce_credit_limit(200)
_m2 = [message for _, message in s_ins.log if "INSOLVENCY" in message][-1]
check("...and says plainly when there was nothing left to take",
      "already at nothing" in _m2, _m2)


# --- BREAK: "this society's literacy will not supply more than 5.9 scholars
# in total, ever, at any price" - and it never moved, through paper, printing,
# a university and three academies. The factor was clamped at 1.0 and Rome
# starts AT the reference, so for Rome the whole mechanism was inert.
s_lit = sim()
_cap0 = s_lit.literate_capacity("machinist")
for _k in ("rag_paper", "printing_press", "if_movable_type", "school_founded",
           "academy_network", "corpus_written"):
    if _k in NODES:
        s_lit.apply_tech_effects(_k)
_cap1 = s_lit.literate_capacity("machinist")
check("teaching a society to read raises what it can staff",
      _cap1 > _cap0 * 1.5, (_cap0, _cap1))
check("...but not without bound",
      _cap1 < _cap0 * 5, (_cap0, _cap1))
check("a trade that needs no letters is not capped by literacy at all",
      s_lit.literate_capacity("smith") == float("inf"),
      s_lit.literate_capacity("smith"))
# --- BREAK: `train electrician 20` gave 27 while machinists stopped at 5.9.
check("every taught trade is bounded by literacy, electrician included",
      not (set(S.Sim.LITERATE_TRADES) ^ set(S.Sim.LITERATE_TRADES))
      and all(trade in S.Sim.LITERATE_TRADES for trade in S.TRADES_ABSENT),
      sorted(set(S.TRADES_ABSENT) - set(S.Sim.LITERATE_TRADES)))
s_el = sim(capital=2000000.0)
_ok_el, _why_el = s_el.train("electrician", 20)
check("...so twenty electricians cannot be taught into a society of twelve",
      not _ok_el and "literacy" in str(_why_el), _why_el)

