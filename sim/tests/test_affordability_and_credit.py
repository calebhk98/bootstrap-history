"""spending_power("buy" vs "start"/"open"), credit_limit, arrears,
insolvency and the warnings and refusals built on them.

Regrouped from test_round8_fixes.py, test_round9.py and test_round10.py -
see CLAUDE.md's test-file reorganisation note. Checks moved verbatim; each
one's own comment explains the break it guards.
"""
from .harness import *  # noqa: F401,F403


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

# --- BREAK: an idle million bled 15,000 a year with nothing anywhere saying why.
_rr, _, _ = proto([{"cmd": "money"}], kit="absurd")
check("the ledger names the part of your living costs that is your wealth",
      (_rr[0].get("what_it_costs_you") or {}).get("_of_which_because_you_are_rich", 0) > 1000,
      _rr[0].get("what_it_costs_you"))

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

# --- BREAK: "CLOSE TO THE LIMIT ... (103%) ... every project in hand is
# halted" in a year when nothing was halted, because it had already happened.
s_pl = sim()
s_pl.capital = -s_pl.credit_limit() * 1.03
s_pl.warn_near_the_limit(105)
check("the limit warning is about what is ahead of you, not behind",
      not s_pl.log, [message for _, message in s_pl.log])

# --- BREAK: a senatorial patron added 15,000 to the credit line whoever you
# were, so a household with 1,800 of revenue could owe 23,000 - about 1,500 a
# year of interest against 1,800 of income, which no practice can ever repay.
s_cl = sim()
_thin = s_cl.credit_limit()
s_cl.done.add("patron_senatorial"); s_cl._done_changed()
check("a grand friend does not lend you more than your income can carry",
      s_cl.credit_limit() < _thin * 3, (_thin, s_cl.credit_limit()))
check("...and the interest on the whole line stays under what you earn",
      s_cl.credit_limit() * s_cl.debt_interest_rate() < s_cl.revenue(),
      (s_cl.credit_limit() * s_cl.debt_interest_rate(), s_cl.revenue()))
check("...while a founder with a practice can still just reach a cover identity",
      sim().capital + sim().credit_limit() >= sim().project_cost("identity_cover"),
      (sim().capital + sim().credit_limit(), sim().project_cost("identity_cover")))

# --- BREAK: status upkeep was unconditional - 1,100 a year for a citizenship
# and a senatorial patron a ruined household could not afford and had no way
# to shed - and it bled a Rome run 741 a year for sixty-four years.
s_st = sim()
s_st.done.update({"citizenship", "patron_senatorial"}); s_st._done_changed()
_rich = sim(capital=2000000.0)
_rich.done.update({"citizenship", "patron_senatorial"}); _rich._done_changed()
# The two ranks are worth 1,100 a year of show at Rome's prices; a household
# with 233 of income does not pay it.
check("a ruined household stops keeping up appearances",
      s_st.living_cost() < sim().living_cost() + 50.0,
      (s_st.living_cost(), sim().living_cost()))
check("...and a household that can afford the show still pays for it",
      _rich.living_cost() > s_st.living_cost() * 2, (_rich.living_cost(),
                                                     s_st.living_cost()))

# --- BREAK: the optimizer's budget for new work counted upkeep, living costs
# and mines and NOT the interest it was already paying, so a household bleeding
# 552 a year decided it had five years of headroom against money that did not
# exist.
s_bd = sim(capital=-20000.0, manual=False)
s_bd.insolvent_years = 20
_before = len(s_bd.active)
s_bd.step()
check("a household deep in arrears does not commit to new work",
      len(s_bd.active) <= _before + 1, (len(s_bd.active), _before))

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
      not any("INSOLVENCY" in json.dumps(reply) for reply in _rd),
      [event for reply in _rd for event in (reply.get("events") or []) if "INSOLVENCY" in str(event)])
check("...and does not take your whole reputation with it",
      _rd[-1].get("reputation", 0) > 1.0, _rd[-1].get("reputation"))
s_cc = sim()
_full = s_cc.credit_limit()
s_cc.wage_hours_this_year = s_cc.director_pool()
check("a lender does not cut your line because you took a job this year",
      abs(s_cc.credit_limit() - _full) < 1e-6, (_full, s_cc.credit_limit()))

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
      any("identity_cover" in message and "stands to your credit" in message
          for _, message in s_ce.log),
      [message for _, message in s_ce.log if "CREDIT EXHAUSTED" in message][:1])
s_ce.capital, s_ce.credit_frozen_until = 50000.0, 0
s_ce.start_project("identity_cover")
check("...and beginning again takes it off the bill",
      abs(s_ce.active["identity_cover"]["cost_left"]
          - (s_ce.project_cost("identity_cover") - _spent)) < 0.5,
      (s_ce.active["identity_cover"]["cost_left"],
       s_ce.project_cost("identity_cover")))
check("...and the credit is spent once, not every time",
      "identity_cover" not in s_ce.paid_towards, s_ce.paid_towards)
