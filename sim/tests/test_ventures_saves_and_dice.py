"""Running concerns, hiring and staffing gates, save and resume (including the dice), and the identity_cover prerequisite."""
from .harness import *  # noqa: F401,F403
from .agent_command_helpers import ask_agent, with_end_year, pristine_game

# --- `load` validates the file before touching the running game. `save` and `load` both refuse an
# absolute path, so every file here lives in a relative scratch directory under ROOT.
_loadtest_abs = os.path.join(ROOT, _LOADTEST_DIR)
os.makedirs(_loadtest_abs, exist_ok=True)


def _rel(name):
    return "%s/%s" % (_LOADTEST_DIR, name)


_load_game = with_end_year(sim())
ask_agent(_load_game, cmd="step", years=1)
_good = ask_agent(_load_game, cmd="save", file=_rel("sess.json"))
check("a legitimate save from this game loads cleanly",
      ask_agent(_load_game, cmd="load", file=_rel("sess.json")).get("ok") is True, _good)

_bad_saves = {
    "not an object at all": "[1, 2, 3]",
    "an unrelated JSON object": json.dumps({"hello": "world"}),
    "missing required fields": json.dumps({"year": 100, "capital": 400}),
}
for _i, (_label, _content) in enumerate(_bad_saves.items()):
    _name = "bad%d.json" % _i
    open(os.path.join(_loadtest_abs, _name), "w").write(_content)
    _before = ask_agent(_load_game, cmd="state")
    _resp = ask_agent(_load_game, cmd="load", file=_rel(_name))
    _after = ask_agent(_load_game, cmd="state")
    check("load refuses %s with a clear message, not a crash" % _label,
          _resp.get("ok") is False and "Traceback" not in _resp.get("error", "")
          and len(_resp.get("error", "")) < 400, _resp)
    check("a refused load (%s) leaves the running game untouched" % _label,
          _before.get("year") == _after.get("year") and _before.get("capital") == _after.get("capital"),
          (_before.get("year"), _after.get("year")))

# a save for a civilisation other than the one currently running
ask_agent(sim(civ="norse_900ad"), cmd="save", file=_rel("norse.json"))
_r2 = ask_agent(_load_game, cmd="load", file=_rel("norse.json"))
check("load refuses a save from a different civilisation",
      _r2.get("ok") is False and "civilisation" in _r2.get("error", ""), _r2)

# a save that refers to a node id the current tree does not have
_blob = json.load(open(os.path.join(_loadtest_abs, "sess.json")))
_target_done = _blob["seats"][_blob["acting_seat"]]["projects"]["done"]["__set__"]
_target_done.append("this_node_does_not_exist_anymore")
json.dump(_blob, open(os.path.join(_loadtest_abs, "unknown_node.json"), "w"))
_before = ask_agent(_load_game, cmd="state")
_r3 = ask_agent(_load_game, cmd="load", file=_rel("unknown_node.json"))
check("load refuses a save that refers to a node the tree no longer has",
      _r3.get("ok") is False and "this_node_does_not_exist_anymore" in _r3.get("error", ""), _r3)
check("that refusal leaves the running game untouched too",
      _before.get("year") == ask_agent(_load_game, cmd="state").get("year"))

# --- the Mexica break tester, six findings, one check each ------------------
# Every one of these was reproduced from the tester's own transcript before it
# was fixed; each check is the tester's repro, kept.

# 1. `work` earned wages as a chemist in a society whose `hire` and `labour`
#    both said chemists do not exist there.
_wk_game = sim()
_wk = [ask_agent(_wk_game, cmd="hire", trade="chemist", n=1), ask_agent(_wk_game, cmd="work", trade="chemist", hours=10),
       ask_agent(_wk_game, cmd="work", trade="scribe", hours=10)]
check("you cannot be paid for a trade this society does not have",
      _wk[0].get("ok") is False and _wk[1].get("ok") is False
      and _wk[2].get("ok") is True,
      [result.get("ok") for result in _wk])

# 3. state.living_cost was living_and_appearances PLUS the whole payroll, while
#    `money` reported the two separately, to the decimal.
_lc_game = sim()
ask_agent(_lc_game, cmd="hire", trade="smith", n=3)
_st, _mo = ask_agent(_lc_game, cmd="state"), ask_agent(_lc_game, cmd="money")
_costs = (_mo.get("what_it_costs_you") or {})
check("state and money do not label the same money two different ways",
      abs(_st.get("living_cost", 0) - _costs.get("living_and_appearances", -1)) < 0.15
      and abs(_st.get("wage_bill", 0) - _costs.get("wages", -1)) < 0.15,
      "state %r / money %r" % ({field_name: _st.get(field_name) for field_name in ("living_cost", "wage_bill")},
                               {field_name: _costs.get(field_name) for field_name in ("living_and_appearances", "wages")}))

# 3. state and the prompt both said 2,400 founder-hours free after 2,300 of
#    them had been sold, and then refused one more hour for having none.
# Derived from the pool, not a literal: this check hardcoded 2,300 hours and
# started failing the moment the founder's year came down to 2,000, because
# `work` correctly refused to sell hours that no longer existed.
_pool = sim().labour.director_pool()
_sell = _pool - 100
_st2_game = sim()
_st2 = [ask_agent(_st2_game, cmd="work", trade="scholar", hours=_sell), ask_agent(_st2_game, cmd="state")]
check("hours already sold for wages are not still reported as free",
      _st2[0].get("ok") is True and _st2[1]["founder_hours_available"] < 200,
      "%r free after selling %g of %g" % (_st2[1].get("founder_hours_available"),
                                          _sell, _pool))

# 5. You could sell every one of your 2,400 hours as a labourer and still
#    collect the full fee from a surgery you were demonstrably not in. The
#    practice is your own two hands; that was the same hours sold twice.
# Wages now track labour tightness and can exceed an ordinary practice, so
# the practice is scaled up until a year of day labour genuinely is a loss.
_PRACTICE_BOOM = 5.0
s = sim()
s.output_factor = _PRACTICE_BOOM
_rev_before = s.revenue()
_earned, _note = s.labour.work_for_wages("labourer", s.labour.director_pool())
check("hours sold as a labourer are not also spent practising medicine",
      _earned > 0 and _rev_before > 0 and s.revenue() < _rev_before * 0.05,
      "revenue %.1f -> %.1f having sold every hour" % (_rev_before, s.revenue()))
# ...and the player is told, rather than left to find it in the ledger. A
# tester measured a year of labour at 66 denarii against a 227 cost of living
# and a 259-a-year practice switched off, and called `work` self-destructive.
# It is, for a physician; the defect was that nothing said so.
check("selling your hours at a loss says so, and still happens",
      _note and "cost you" in _note, _note)
s2 = sim()
s2.output_factor = _PRACTICE_BOOM
s2.labour.work_for_wages("labourer", s2.labour.director_pool() * 0.5)
check("selling half your hours costs you half the practice, not all of it",
      abs(s2.revenue() - _rev_before * 0.5) < _rev_before * 0.06,
      "%.1f against half of %.1f" % (s2.revenue(), _rev_before))

# 6. `buy mine` spent every denarius you had and handed back a fraction of the
#    mine you asked for, without asking. A command you typed is not a standing
#    order to spend everything.
_mn_game = sim()
_mn = [ask_agent(_mn_game, cmd="buy", what="mine", material="copper", n=500), ask_agent(_mn_game, cmd="state")]
check("a mine you cannot pay for is refused, not part-bought with all your money",
      _mn[0].get("ok") is False and "Nothing was changed" in (_mn[0].get("error") or "")
      and _mn[1]["capital"] > 300,
      (_mn[0].get("error", "")[:80], _mn[1].get("capital")))

# --- the England normal-play tester -------------------------------------------
# 1. `train optician 1` destroyed the save. trades_created holds TRADE names and
#    was validated against the tech tree, so teaching any of the five trades
#    that gate chemistry, precision and electricity wrote a name the next load
#    refused as a missing technology. It cost that tester two runs and, by their
#    own measurement, 1,230 technologies.
_tr_game = sim()
ask_agent(_tr_game, cmd="train", trade="optician", n=1)
_tr_path = os.path.join(ROOT, _rel("trained.json"))
S.save_state(_tr_game, _tr_path)
_tr_loaded = sim()
try:
    S.load_state(_tr_loaded, _tr_path)
    _tr_error = None
except Exception as error:
    _tr_error = repr(error)
check("teaching a trade does not destroy the save",
      _tr_error is None and "optician" in _tr_loaded.trades_created, _tr_error)

# 6. A quote read years ago is not what you pay: project_cost moves with
#    prices, the coinage and materials. The bill IS fixed when you start, and
#    nothing said what it was fixed at.
_q1_game = sim()
_q1 = [ask_agent(_q1_game, cmd="why", id="hom_eraser_breadcrumb"), ask_agent(_q1_game, cmd="start", id="hom_eraser_breadcrumb")]
check("starting something says what bill you have just taken on",
      _q1[1].get("the_bill_you_have_taken_on") is not None
      and _q1[0]["cost"].get("as_of_year"),
      (_q1[1].get("the_bill_you_have_taken_on"), _q1[0]["cost"].get("as_of_year")))

# --- knowing how, and actually running it ------------------------------------
# The user, on the deepest thing anyone said about this model: "you research
# the finance stuff and instantly make money -- but shouldn't that just unlock
# the ABILITY to do it? You research loans, now you can give out loans. What if
# you didn't give out any?" 1,337 nodes carried revenue and 1,256 of those also
# carried upkeep, so the tree already called them going concerns; the only
# thing missing was the act of opening the doors.
# Hire somebody first: a concern needs a pair of your hands to run it, which
# is the whole point of the staffing floor. Nobody runs a pawnshop alone from
# nowhere.
_v_game = sim(capital=2.0e6)
ask_agent(_v_game, cmd="hire", trade="artisan", n=2)
_v_game.done.add("fin_restaurant")
_v_game._done_changed()
_before = ask_agent(_v_game, cmd="money")
_open = ask_agent(_v_game, cmd="open", id="fin_restaurant")
_after = ask_agent(_v_game, cmd="money")
check("working out how to do something does not by itself pay you",
      "fin_restaurant" not in (_before.get("where_the_money_comes_from") or {}),
      _before.get("where_the_money_comes_from"))
check("opening the doors is what pays you",
      _open.get("ok") is True
      and (_after.get("where_the_money_comes_from") or {}).get("fin_restaurant"),
      _after.get("where_the_money_comes_from"))

s2 = sim(capital=200000.0)
s2.labour.hire("artisan", 2)
s2.done.add("fin_restaurant")
s2._done_changed()
_cap0 = s2.capital
s2.open_venture("fin_restaurant")
check("opening a concern costs stock and premises, not nothing",
      _cap0 - s2.capital >= NODES["fin_restaurant"]["up"],
      "%.0f to open against %.0f a year of running cost"
      % (_cap0 - s2.capital, NODES["fin_restaurant"]["up"]))

# You cannot run fifty businesses with three people.
s3 = sim(capital=1000000.0)
# BIG ENOUGH THAT ONE PERSON CANNOT RUN IT. The founder counts as a pair of
# hands now, so a small shop is exactly what they CAN open alone; the staffing
# rule is about scale, and this check has to test scale.
_heavy = [node_id for node_id in NODES if NODES[node_id]["rev"] >= book_money(6000.0)][:1]
if _heavy:
    s3.done.add(_heavy[0]); s3._done_changed()
    s3.artisans = 0.0
    _okh, _whyh = s3.open_venture(_heavy[0])
    check("a concern nobody is free to run cannot be opened",
          _okh is False and "nobody free" in (_whyh or ""), _whyh)

# Shutting it stops both sides and keeps the knowledge.
s4 = sim(capital=200000.0)
s4.labour.hire("artisan", 2)
s4.done.add("fin_restaurant"); s4._done_changed()
s4.open_venture("fin_restaurant")
_rev_on, _up_on = s4.revenue(), s4.upkeep()
s4.mothball_work("fin_restaurant")
check("closing a concern stops what it earned and what it cost, both",
      s4.revenue() < _rev_on and s4.upkeep() < _up_on
      and "fin_restaurant" in s4.done,
      "rev %.0f->%.0f up %.0f->%.0f, still known %s"
      % (_rev_on, s4.revenue(), _up_on, s4.upkeep(), "fin_restaurant" in s4.done))

_manual_policy, _optimizer_policy = sim(manual=True).policy, sim(manual=False).policy
check("opening things for you is on for the optimizer and off for a player",
      _manual_policy["auto_open"] is False and _optimizer_policy["auto_open"] is True,
      (_manual_policy["auto_open"], _optimizer_policy["auto_open"]))

# What you run has to survive a save, or reloading quietly shuts your business.
_vs = "%s/ventures.json" % _LOADTEST_DIR
ask_agent(_v_game, cmd="save", file=_vs)
ask_agent(_v_game, cmd="load", file=_vs)
_rt = [ask_agent(_v_game, cmd="state")]
check("what you are running survives a save and reload",
      _rt[-1].get("concerns_you_run") == 1,
      "runs %r after a round trip" % _rt[-1].get("concerns_you_run"))

# Two Roman-branded grants were still being handed free to every civilisation.
_ROMAN = ("_roman", "_rome", "annona", "insula", "societas", "collegium",
          "argentarii", "latifundi", "cursus", "pharos")
for _civ in ("han_china_100ad", "norse_900ad", "mexica_1500", "england_1300"):
    _sc = sim(civ=_civ)
    _bad = sorted(granted_name for granted_name in _sc.granted if any(roman_marker in granted_name for roman_marker in _ROMAN))
    check("%s is not handed Roman institutions for nothing" % _civ,
          not _bad, _bad)

# --- the Norse deadlock ------------------------------------------------------
# A Norse run ended at year 1500 with 31,068 denarii, 136 technologies and 1.6
# craftsmen, unable to build workshop_first because it needs 2 - while every
# institution that raises the staff ceiling (freedman_staff, collegium_licensed,
# school_founded) needs workshop_first first. You needed two craftsmen to build
# the place craftsmen work, and could never get to two. The Norse reached the
# goal in 0% of runs and it was never about money.
#
# The gate read self.artisans alone, so work you had already paid an outside
# shop to do did not count - and the refusal's own advice was to go and
# commission it.
s = sim(civ="norse_900ad", capital=100000.0)
# Prerequisites are tested before staff, so satisfy them: the point of this
# check is the staff gate, not the ladder above it.
for _p in NODES["workshop_first"]["pre"]:
    s.done.add(_p)
s._done_changed()
_ok0, _why0 = s.start_reason("workshop_first")
_blocked_on_staff = "craftsmen" in (_why0 or "")
s.labour.commission("carpenter", 4000)
_ok1, _why1 = s.start_reason("workshop_first")
check("craftsmen you have under contract count toward what a project needs",
      _blocked_on_staff and "craftsmen" not in (_why1 or ""),
      "before: %s | after: %s" % ((_why0 or "")[:60], (_why1 or "")[:60]))
check("commission can unblock the gate whose own advice is to commission",
      s.labour.craft_hands_available() >= 2.0,
      "%.2f craft hands from 4,000 contracted hours" % s.labour.craft_hands_available())

# open/ventures are how technology turns into income and were missing from the
# command list; `open` on the founder's own practice denied it was theirs while
# `money` itemised it as their largest source of income.
_hc_game = sim(civ="han_china_100ad")
_hc = [ask_agent(_hc_game, cmd="help", topic="commands"), ask_agent(_hc_game, cmd="open", id="med_cataract_couching")]
check("every way of turning knowledge into income is in the command list",
      all(command in json.dumps(_hc[0]) for command in ("open", "ventures")),
      sorted((_hc[0].get("commands") or {}).keys())[:6])
check("the game does not deny that your own practice is yours",
      "already doing that" in (_hc[1].get("error") or ""), _hc[1].get("error"))

# --- round 5, the Han testers --------------------------------------------
# 1. THE WORST: resuming a save re-rolled the dice. Nothing saved the random
#    state, so a project sitting at its completion threshold re-rolled its
#    failure check on every resume: `start fin_bimetallism` then one `step`
#    per process oscillated 100%/60%/100%/60% for ever, burning hours and
#    money and never finishing. Reproduced 5 times out of 5. It also silently
#    re-drew every hazard and event a returning player would meet.
_dice_game = sim(civ="han_china_100ad")
_dice_game.rng.random()
_dice_path = os.path.join(ROOT, _rel("dice.json"))
S.save_state(_dice_game, _dice_path)
_dice_resumed = sim(civ="han_china_100ad")
S.load_state(_dice_resumed, _dice_path)
check("a resumed game carries on the same dice, so a project at its threshold does not re-roll on every resume",
      [_dice_game.rng.random() for _ in range(5)] == [_dice_resumed.rng.random() for _ in range(5)])

# 2. Founder hours could be spent twice: `train` wrote its own counter and
#    `work` read only the wage one, so 3,800 hours went into a 2,000-hour year.
_dh_game = sim(civ="han_china_100ad", capital=2.0e6)
_dh = [ask_agent(_dh_game, cmd="train", trade="machinist", n=2), ask_agent(_dh_game, cmd="train", trade="chemist", n=2),
       ask_agent(_dh_game, cmd="state"), ask_agent(_dh_game, cmd="work", trade="smith", hours=2000)]
check("hours spent teaching are not still available to sell",
      _dh[2]["founder_hours_available"] < 400 and _dh[3].get("ok") is False,
      "%r free, work accepted=%r" % (_dh[2].get("founder_hours_available"),
                                     _dh[3].get("ok")))

# 3. A bribe that buys nothing said so and charged 5,000 anyway.
_bb_game = sim(capital=2.0e6)
_bb = [ask_agent(_bb_game, cmd="bribe", amount=5000), ask_agent(_bb_game, cmd="bribe", amount=5000), ask_agent(_bb_game, cmd="state")]
check("a bribe that would buy nothing is refused, not charged",
      _bb[1].get("ok") is False and "Nothing was changed" in (_bb[1].get("error") or ""),
      _bb[1].get("error"))

# 7. A project blamed the wrong resource for 275 years. `logarithms` sat at
#    "waiting on your hours" from 325 AD to the horizon with 1,900 idle founder
#    hours, while the real cause was 40,000 scribe-hours wanted from a society
#    that can field a few thousand. waiting_on was read off whatever the last
#    step happened to record instead of being worked out against today.
s = sim(civ="han_china_100ad")
# Enough of Han's own money for the hires, so the stall is about scribes.
s.capital = 5000 * s.labour.market.quote_annual("scholar")
for _p in NODES["logarithms"]["pre"]:
    s.done.add(_p)
s._done_changed()
s.labour.hire("scholar", 2)
s.start_project("logarithms")
s.step()
_w = S._waiting_on(s, NODES, "logarithms", s.active["logarithms"], 0)
check("a stalled project names the resource actually stalling it",
      "scribe" in _w and "your hours" not in _w, _w)
check("...and says how far short the society is, in numbers",
      "can field" in _w or "booked" in _w, _w)

# A play tester watched their year grow from 2,000 hours to 6,090 with nothing
# saying why. It is deputies, not the founder working harder.
_hrs = [ask_agent(pristine_game(), cmd="state")]
check("state says where the founder's hours actually come from",
      (_hrs[0].get("where_your_hours_come_from") or {}).get("hours_each_deputy_adds"),
      _hrs[0].get("where_your_hours_come_from"))

# --- the persona is a persona, not a licence to do arithmetic ----------------
# The user, on identity_cover: "does anything building on it actually require
# it, or does it just make it so that you have social metrics that help? You
# could build a hot air balloon or bike without an identity, you are just more
# likely to be called a witch."
#
# They were right, and it was worse than that. identity_cover's whole
# implementation was +1.0 to the reputation floor and +400 to the credit
# limit; the "reduces all future suspicion" in its own description referred to
# a field that no longer exists. Its real function was to gate a quarter of
# the tree - and it was empirically the single node blocking England and
# Mexica from ever reaching the goal, because arithmetic_positional needs it
# and nothing else.
check("writing down zero does not require a respectable persona",
      "identity_cover" not in NODES["arithmetic_positional"]["pre"]
      and "identity_cover" not in NODES["scientific_method"]["pre"],
      (NODES["arithmetic_positional"]["pre"], NODES["scientific_method"]["pre"]))
check("...but being received by a patron, and publishing, still do",
      "identity_cover" in NODES["patron_local"]["pre"]
      and "identity_cover" in NODES["world_map"]["pre"],
      (NODES["patron_local"]["pre"], NODES["world_map"]["pre"]))


def _persona(has):
    persona_sim = sim(civ="england_1300")
    if has:
        run_it(persona_sim, "identity_cover")
    persona_sim.update_protection()
    return persona_sim


_no, _yes = _persona(False), _persona(True)
_n = NODES["hot_air_balloon"]
check("a persona makes the same strange work less alarming, as it says it does",
      _yes.alarm_of(_n) < _no.alarm_of(_n) * 0.85
      and _yes.protection > _no.protection,
      "alarm %.2f -> %.2f, protection %.3f -> %.3f"
      % (_no.alarm_of(_n), _yes.alarm_of(_n), _no.protection, _yes.protection))
check("...and you can still build the balloon without one",
      _no.alarm_of(_n) > 0 and "identity_cover" not in NODES["hot_air_balloon"]["pre"],
      NODES["hot_air_balloon"]["pre"])

# --- round 6, the England break tester ---------------------------------------
# 1. THE EXPLOIT THE VENTURE MODEL CREATED. `open` refused without supervisors
#    and then nothing ever looked again, so the tester hired five craftsmen,
#    opened eleven concerns in one turn, fired all six people and watched net
#    income RISE - seventeen concerns running against "EMPLOY: 0 people", and
#    the same loom still paying 435 a year in 1800 through the Black Death.
s = sim(civ="england_1300", capital=book_money(500000.0, "england_1300"))
s.labour.hire("artisan", 6)
_big = [node_id for node_id in NODES if book_money(2000.0) <= NODES[node_id]["rev"] <= book_money(9000.0)][:4]
for _k in _big:
    s.done.add(_k)
s._done_changed()
_opened = [node_id for node_id in _big if s.open_venture(node_id)[0]]
_rev_staffed = s.revenue()
s.labour.fire("artisan", 6)
s.step()
check("a concern nobody is left to watch stops trading",
      _opened and not s.operating and s.revenue() < _rev_staffed * 0.2,
      "revenue %.0f -> %.0f, still running %d"
      % (_rev_staffed, s.revenue(), len(s.operating)))
check("...and the game says which ones closed and why",
      any("nobody left to keep an eye on" in message for _year, message in s.log),
      [message for _year, message in s.log][-2:])

# effective_scholars() has always counted the founder as one of the scholars;
# nothing counted them as a pair of hands, though the premise of the game is a
# person who knows how every one of these things is made. workshop_first wants
# two craftsmen, so a Norse run that could field one could never build the
# place craftsmen work.
s = sim(civ="norse_900ad")
check("the founder is one of the craftsmen as well as one of the scholars",
      s.labour.craft_hands_available() >= 1.0 and s.labour.effective_scholars() >= 1.0,
      "%.1f hands, %.1f scholars, with nobody hired"
      % (s.labour.craft_hands_available(), s.labour.effective_scholars()))
s2 = sim(civ="norse_900ad")
for _p in NODES["workshop_first"]["pre"]:
    s2.done.add(_p)
s2._done_changed()
s2.labour.hire("carpenter", 1)
check("...so one hired hand is enough to raise your first workshop",
      s2.start_reason("workshop_first")[0],
      s2.start_reason("workshop_first")[1])

# --- BREAK: the pivot node of the entire game did nothing under --manual, the
# interactive protocol's only mode. school_founded's own text promises "+4
# scholars", _complete() added it with a bare self.scholars += 4, and the very
# next step() called _resync_pools() - unconditionally, every year - which has
# always recomputed self.scholars purely from self.employees and so overwrote
# the grant to whatever employees already held. A player who founded the
# school and then did anything else at all would have read a refusal a year
# later naming the same scholar shortfall the school was built to answer,
# with nothing saying why. Fixed by giving the grant its own durable record
# (_grant_staff) that _resync_pools adds back rather than discards.
s_gr = sim(capital=10000000.0, manual=True)
s_gr.done.add("school_founded")
s_gr._done_changed()
s_gr.operating.add("school_founded")
s_gr.labour._grant_staff(scholars=4)
_after_grant = s_gr.scholars
s_gr.step()
check("founding the school still leaves you its scholars a year later",
      s_gr.scholars >= _after_grant - 1e-6,
      (_after_grant, s_gr.scholars))
check("...and a project that needed exactly what it granted can now start",
      s_gr.labour.effective_scholars() >= 4.0,
      s_gr.labour.effective_scholars())

# `quote` existed because a tester went from 38,151 denarii to zero on one
# unpriced mine command. A break tester then spent 27,500 - 68% of capital -
# on `buy forest 100`, with no price shown and no way to ask for one.
_qf_game = sim(capital=2.0e6)
_qf = [ask_agent(_qf_game, cmd="quote", what="forest", n=100), ask_agent(_qf_game, cmd="quote", what="slaves", n=5)]
check("you can ask the price of a forest before you buy one",
      _qf[0].get("ok") is True and _qf[0].get("to_buy_it", 0) > 0,
      _qf[0].get("error") or _qf[0].get("to_buy_it"))
check("...and of people",
      _qf[1].get("ok") is True and _qf[1].get("to_buy_them", 0) > 0,
      _qf[1].get("error") or _qf[1].get("to_buy_them"))
s = sim(capital=book_money(100000.0))
_before_f = s.capital
_quoted = _qf[0]["to_buy_it"]
s.buy_forest(100)
check("the quoted price of a forest is the price you are charged",
      abs((_before_f - s.capital) - _quoted) < 1.0,
      "quoted %.1f, charged %.1f" % (_quoted, _before_f - s.capital))

# 2. "Told to my face I could take 6 more people, I took 7 with a different
#    verb." buy went round the feed/house/oversee cap that hire enforces.
s = sim(capital=1000000.0)
_room = s.labour.household_room()
_ok_over = s.labour.buy_slaves(int(_room) + 5)
check("buying people obeys the same household cap as hiring them",
      _ok_over == 0 and s.slaves == 0,
      "room %.2f, bought %s" % (_room, _ok_over))
check("...and buying within it still works",
      s.labour.buy_slaves(max(1, int(_room) - 1)) > 0, "room %.2f" % _room)
