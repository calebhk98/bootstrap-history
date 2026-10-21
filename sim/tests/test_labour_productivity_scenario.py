"""labour_productivity scenario (Complaint 640 audit): four named scenarios through a game: the price of a settled trade,
a society over centuries (schooling, trade absorption, diffusion), a staffing closure and its reopening, and the
standing money figures. The productivity arithmetic, the diffusion curve and the material-gating rule are tests in
test_labour_productivity; trade absorption is test_trade_absorption_rules, the closure choice
test_staffing_choice_rules, the grace window test_closure_grace_rules, the credit freeze and the stall
test_credit_freeze_rules, the `why` supervision block test_why_supervision_rules."""
from .harness import *  # noqa: F401,F403
from sim.refusal import cause_of, facts_of
from sim.labour.api import Labour

# =============================================================================
# THE USER'S THREE QUESTIONS. Q1: does training ten times as many smiths
# actually cut the cost of a smith? Q2: can a technology raise output per
# worker without replacing the worker (labour.py's labour_productivity),
# and is it wired to real tree nodes rather than invented ones?
# =============================================================================

# --- Q1: train ten times as many smiths, measure what a smith costs, before
# and after - exactly as asked, rather than trusting the comment in
# labour_price_factor that claims the price comes back down. household_room
# is patched open for this one check because the question is about the
# PRICING mechanism (labour_pressure vs market_supply), which is orthogonal
# to the household-capacity gate hire() also enforces; nothing else in this
# file, and no other check, depends on the patch.
_orig_room = Labour.household_room
_orig_supervision_room = Labour.supervision_room
Labour.household_room = lambda self: 10_000.0
Labour.supervision_room = lambda self: 10_000.0
try:
    small = unopened_sim(capital=1e9)
    small.labour.hire("smith", 5)
    small.year += 10                 # let the hiring-day pressure fully decay
    big = unopened_sim(capital=1e9)
    big.labour.hire("smith", 50)            # TEN TIMES as many smiths
    big.year += 10                   # same decay, same settling time
    cost_small = (S.ANNUAL_WAGE["smith"] * small.wage_index * small.price_index
                  * small.labour.market.price_factor("smith"))
    cost_big = (S.ANNUAL_WAGE["smith"] * big.wage_index * big.price_index
                * big.labour.market.price_factor("smith"))
    check("once the market has settled, a smith costs the SAME base wage "
          "whether the trade has 5 people in it or 50 - training ten times "
          "as many smiths does not cut the price below the wage table, it "
          "only avoids a lasting premium (see the next two checks for what "
          "training ten times as many DOES change)",
          abs(cost_big - cost_small) < 0.5, (cost_small, cost_big))

    # The same batch of new hiring pressure is a smaller share of a bigger trade.
    thin, thick = small, big
    thin_capital_before, thick_capital_before = thin.capital, thick.capital
    thin.labour.hire("smith", 10)
    thick.labour.hire("smith", 10)
    fee_thin = thin_capital_before - thin.capital
    fee_thick = thick_capital_before - thick.capital
    check("expanding an already-large trade by a fixed amount costs no more "
          "in fees than expanding a small one by the same amount, once both "
          "have settled",
          abs(fee_thick - fee_thin) < 1.0, (fee_thin, fee_thick))

    per_head_thin = thin.labour.wage_bill() / thin.employees["smith"]
    per_head_thick = thick.labour.wage_bill() / thick.employees["smith"]
    check("the standing payroll's per-head cost, measured immediately after "
          "each identical top-up batch, is lower for the bigger trade - the "
          "same recent pressure is diluted across more existing people",
          per_head_thick < per_head_thin,
          "per head, base=5->15: %.2f   base=50->60: %.2f"
          % (per_head_thin, per_head_thick))
finally:
    Labour.household_room = _orig_room
    Labour.supervision_room = _orig_supervision_room

# --- Q2: technology that raises output per worker without replacing them.
s = unopened_sim(capital=1e9)
before_call_on = s.labour.hours_you_can_call_on("smith")
before_supply = s.labour.market_supply("smith")
s.done.add("met_trip_hammer")
after_call_on = s.labour.hours_you_can_call_on("smith")
after_supply = s.labour.market_supply("smith")
check("a real productivity technology (the trip hammer) raises the WORK a smith's hours can produce this year, "
      "without changing market_supply: it makes the existing smiths faster, it does not conjure more of them",
      after_call_on > before_call_on * 1.05 and after_supply == before_supply,
      (before_call_on, after_call_on, before_supply, after_supply))

check("every node named in LABOUR_PRODUCTIVITY_SOURCES is a real node in "
      "the compiled tree, not a name that was never wired to anything",
      all(node_id in NODES for node_id, _, _ in s.LABOUR_PRODUCTIVITY_SOURCES),
      [node_id for node_id, _, _ in s.LABOUR_PRODUCTIVITY_SOURCES if node_id not in NODES])
check("every trade named in LABOUR_PRODUCTIVITY_SOURCES is a real trade in "
      "the wage table",
      all(trade in WAGES for _, trade, _ in s.LABOUR_PRODUCTIVITY_SOURCES),
      [trade for _, trade, _ in s.LABOUR_PRODUCTIVITY_SOURCES if trade not in WAGES])
# EDUCATING A WHOLE SOCIETY. The user's own question: "can we make the whole
# country's literacy rates improve? What if we make 5,000 schools and
# tractors and food production... can I create a 90%+ literate population?"
# See SocietyMixin.advance_society (society.py).
from sim.labour.labour_allocation import FARM_TRADE as _FARM_TRADE

s_noschool = unopened_sim(capital=2000000.0, manual=False)
s_noschool.trades_created.add("electrician")
_gen0 = s_noschool.literacy("literacy_general")
for i in range(1, 401):
    s_noschool.advance_society(s_noschool.year + i)
check("with no school ever running literacy does not move at all - this "
      "is something a society is TAUGHT, not a free drift",
      s_noschool.literacy("literacy_general") == _gen0, s_noschool.literacy("literacy_general"))
check("a taught trade never naturalises without a single school ever "
      "running, however long the run",
      "electrician" not in s_noschool.trades_endemic
      and s_noschool.employees.get("electrician", 0.0) == 0.0,
      (sorted(s_noschool.trades_endemic), s_noschool.employees.get("electrician")))

s_max = run_it(unopened_sim(capital=2000000.0, manual=False),
               "school_founded", "academy_network")
for _institution in ("school_founded", "academy_network"):
    s_max.state.projects.business.set_size(_institution, 9.0)
# A society with almost nobody left on the farms.
s_max.state.economy.society_labour_hours = {_FARM_TRADE: 0.02, "other": 0.98}
for i in range(1, 701):
    s_max.advance_society(s_max.year + i)
check("heavy schooling in a society with a small farm share, over "
      "centuries, can reach a 90%+ literate general population",
      s_max.literacy("literacy_general") >= 0.9, s_max.literacy("literacy_general"))
check("...and never reaches the whole population: some cannot learn to read",
      s_max.literacy("literacy_general") < 1.0, s_max.literacy("literacy_general"))
check("the lettered/propertied class closes most of its own gap too, on "
      "the same schooling",
      s_max.literacy("literacy_elite") >= 0.95, s_max.literacy("literacy_elite"))

# =============================================================================
# A TRADE THE FOUNDER INTRODUCED BECOMES A TRADE THE SOCIETY HAS. The user's
# sharpest question: "if I invent electricity, you can't say that after 100
# years I still can't find anyone who can make or research generators." See
# SocietyMixin._advance_trade_absorption/_grow_endemic_trade (society.py).
s_teach = run_it(unopened_sim(capital=5000000.0, manual=False),
                 "school_founded", "academy_network")
for _institution in ("school_founded", "academy_network"):
    s_teach.state.projects.business.set_size(_institution, 9.0)
s_teach.trades_created.add("electrician")
_yrs_needed = s_teach._trade_absorption_years(s_teach._schooling_flow())
_y0 = s_teach.year
_not_yet_year = _y0 + max(1, int(_yrs_needed) - 5)
for yr in range(_y0 + 1, _not_yet_year + 1):
    s_teach.advance_society(yr)
_after_year = _y0 + int(_yrs_needed) + 10
for yr in range(_not_yet_year + 1, _after_year + 1):
    s_teach.advance_society(yr)
check("a heavily-schooled society naturalises a taught trade within about "
      "a century of the founder introducing it",
      "electrician" in s_teach.trades_endemic, s_teach.year - _y0)
for yr in range(_after_year + 1, _after_year + 101):
    s_teach.advance_society(yr)
check("...and goes on to actually produce its own electricians, for free, "
      "bounded by the exact same literate_capacity() wall a founder hiring "
      "or teaching them by hand is bounded by",
      0 < s_teach.employees.get("electrician", 0.0)
      <= s_teach.labour.literate_capacity("electrician") + 1e-6,
      (round(s_teach.employees.get("electrician", 0.0), 2),
       round(s_teach.labour.literate_capacity("electrician"), 2)))

_sess_edu = os.path.join(ROOT, _rel("education.json"))
S.save_state(s_teach, _sess_edu)
s_teach2 = S.Sim(NODES, ORDER, random.Random(1), events=False, manual=True,
                 civ=S.load_civ("rome_100ad"))
s_teach2.goal, s_teach2.done_year = GOAL, {}
S.load_state(s_teach2, _sess_edu)
check("which trades have naturalised, and when each was introduced, "
      "survive a save and a fresh process loading it back",
      s_teach2.trades_endemic == s_teach.trades_endemic
      and s_teach2.trade_introduced_year == s_teach.trade_introduced_year,
      (sorted(s_teach2.trades_endemic), s_teach2.trade_introduced_year))

_st_edu = [S._agent_dispatch(s_teach, NODES, {"cmd": "state"})]
check("`state` reports this society's literacy and how far it could go "
      "from here",
      "literacy" in _st_edu[0]
      and 0.0 <= _st_edu[0]["literacy"]["general"] <= 1.0
      and _st_edu[0]["literacy"]["general_ceiling_now"]
          >= _st_edu[0]["literacy"]["general"],
      _st_edu[0].get("literacy"))
check("...and which taught trades the society has absorbed on its own",
      "trades_society_now_has_on_its_own" in _st_edu[0],
      _st_edu[0].get("trades_society_now_has_on_its_own"))

# =============================================================================
# WHAT YOU BUILT DOES NOT STAY YOURS. "You selling gunpowder to the
# military, someone else will likely want some of that money. Over a
# generation or two." See SocietyMixin.diffusion_share/diffusion_index
# (society.py) - a number exposed for a competitive-pricing pass to spend,
# deliberately not yet spent in revenue() itself (see that function's own
# docstring for why, and for the seam left for the agent doing that work).
_rev_node = next(node_id for node_id in sorted(NODES) if NODES[node_id].get("rev", 0) > 0)
_no_rev_node = next(node_id for node_id in sorted(NODES) if NODES[node_id].get("rev", 0) <= 0)

s_dif = unopened_sim(capital=1000000.0)
check("diffusion_index is 0 with nothing operating",
      s_dif.diffusion_index() == 0.0, s_dif.diffusion_index())
check("a technology nobody has opened for business has nothing to leak",
      s_dif.diffusion_share(_rev_node) == 0.0, s_dif.diffusion_share(_rev_node))
s_dif.done.add(_rev_node); s_dif.operating.add(_rev_node)
s_dif.done_year[_rev_node] = s_dif.year
s_dif.done.add(_no_rev_node); s_dif.operating.add(_no_rev_node)
s_dif.done_year[_no_rev_node] = s_dif.cfg["start_year"] - 200
check("a concern with no revenue at all has no market to leak into, "
      "however long it has been open",
      s_dif.diffusion_share(_no_rev_node) == 0.0,
      s_dif.diffusion_share(_no_rev_node))

s_dif.done_year[_rev_node] = s_dif.year - 20
_plain = s_dif.diffusion_share(_rev_node)
s_dif.done.add("corpus_dispersed"); s_dif.operating.add("corpus_dispersed")
s_dif._done_changed()
_published = s_dif.diffusion_share(_rev_node)
check("published knowledge (corpus_dispersed) escapes to competitors "
      "faster than a secret kept in one workshop",
      _published > _plain, (_plain, _published))
check("...and diffusion_index rises, revenue-weighted, once something is operating",
      s_dif.diffusion_index() > 0.0, s_dif.diffusion_index())
_st_dif = S._agent_dispatch(s_dif, NODES, {"cmd": "state"})
check("`state` reports how much of what you run has diffused to competitors",
      "diffusion_index" in _st_dif and 0.0 <= _st_dif["diffusion_index"] <= 1.0,
      _st_dif.get("diffusion_index"))

# --- Staffing: one game for `why`'s supervision figure, the staffing closure, the
# automatic reopen, and the price `restore` quotes inside and after the grace window.
s_staff = unopened_sim(capital=1_000_000.0)
_SUPERVISED = concern_needing_craftsmen_to_supervise()

# `why` quoted the BUILD crew as the staff requirement, while `open` enforces
# ongoing SUPERVISION (venture_hands). `why` must show both, from the same function.
_why = S._agent_dispatch(s_staff, NODES, {"cmd": "why", "id": _SUPERVISED})
_why_open = _why["staff_to_keep_it_open"]
_expect_sch, _expect_art = s_staff.venture_hands(_SUPERVISED)
check("`why`'s supervision figure is computed by the same function `open` "
      "enforces (venture_hands), not a second estimate of it",
      abs(_why_open["scholars"] - round(_expect_sch, 2)) < 0.01
      and abs(_why_open["artisans"] - round(_expect_art, 2)) < 0.01,
      "why said %s, venture_hands says %.2f/%.2f" % (_why_open, _expect_sch, _expect_art))
# A concern the staffing rule shut never came back on its own once restaffed.
s_staff.done.update(NODES[_SUPERVISED]["pre"])
s_staff.done.add(_SUPERVISED)
s_staff._done_changed()
s_staff.employees["artisan"] = 6.0
s_staff.labour._resync_pools()
ok, _ = s_staff.open_venture(_SUPERVISED)
check("set-up: the supervised concern opens with six craftsmen on staff", ok)
s_staff.employees["artisan"] = 0.0
s_staff.labour._resync_pools()
closed = s_staff.close_unstaffed_ventures(s_staff.year)
check("losing every craftsman shuts a concern that needs them to supervise",
      closed == [_SUPERVISED] and _SUPERVISED in s_staff.mothballed
      and _SUPERVISED in getattr(s_staff, "shut_for_staff", {}), closed)
s_staff.employees["artisan"] = 6.0
s_staff.labour._resync_pools()
reopened = s_staff.reopen_restaffed_ventures(s_staff.year)
check("...and it comes back on its own once restaffed, with no 'open' typed",
      reopened == [_SUPERVISED] and _SUPERVISED in s_staff.operating and _SUPERVISED not in s_staff.mothballed
      and _SUPERVISED not in getattr(s_staff, "shut_for_staff", {}), reopened)

# `restore` must say which price it charged: the discounted tenth inside the
# grace window, the full price after it.
s_staff.employees["artisan"] = 0.0
s_staff.labour._resync_pools()
s_staff.close_unstaffed_ventures(s_staff.year)
check("set-up: the closure is recorded as staffing-caused",
      _SUPERVISED in getattr(s_staff, "shut_for_staff", {}), s_staff.shut_for_staff)
_ok_in_grace, _msg_in_grace = s_staff.restore_work(_SUPERVISED)
check("restoring within the grace window is charged the discounted price, and the closure says so",
      _ok_in_grace and facts_of(_msg_in_grace)["discounted"] and facts_of(_msg_in_grace)["closure_age"] is not None,
      _msg_in_grace)
s_staff.employees["artisan"] = 0.0
s_staff.labour._resync_pools()
s_staff.close_unstaffed_ventures(s_staff.year)
s_staff.year += s_staff.STAFF_CLOSURE_GRACE + 1
_ok_lapsed, _msg_lapsed = s_staff.restore_work(_SUPERVISED)
check("...and restoring after the window has lapsed is charged the full price, and the closure says so",
      _ok_lapsed and not facts_of(_msg_lapsed)["discounted"] and facts_of(_msg_lapsed)["closure_age"] is not None
      and facts_of(_msg_lapsed)["fee"] > facts_of(_msg_in_grace)["fee"],
      (_msg_in_grace, _msg_lapsed))

# --- One game for the credit freeze, the standing-figure regression and the stall diagnosis.
s_money = unopened_sim(capital=100000.0)

# Settling again while an earlier freeze is in force: the date rule is settlement_freeze (test_credit_freeze_rules); here
# the settlement reads it and records the old and new dates as facts.
s_money.capital = -(s_money.credit_limit() * 1.5)
s_money.last_settlement = -999
s_money.credit_frozen_until = 110
_log_start = len(s_money.log)
s_money.default_on_debt(105)
_freeze_messages = [message for _, message in s_money.log[_log_start:] if cause_of(message) == "insolvency_settled"]
check("a settlement while an earlier freeze is in force moves the unlock date and records both dates",
      bool(_freeze_messages) and s_money.credit_frozen_until == facts_of(_freeze_messages[0])["credit_frozen_until"]
      and facts_of(_freeze_messages[0])["freeze_moved"] and facts_of(_freeze_messages[0])["frozen_before"] == 110,
      _freeze_messages)

# `state`'s and `money`'s recurring net_per_year is the STANDING figure: selling
# founder-hours with `work` must not swing it for one year.
s_money.capital = 100000.0
s_money.credit_frozen_until = 0
_net_before = S._agent_dispatch(s_money, NODES, {"cmd": "state"}).get("net_per_year")
_money_before = S._agent_dispatch(s_money, NODES, {"cmd": "money"}).get("net_per_year")
_pay, _ = s_money.labour.work_for_wages("scholar", 1500)
check("set-up: selling founder-hours for wages actually registers as this year's wage_hours_this_year",
      s_money.wage_hours_this_year > 0 and _pay > 0, (s_money.wage_hours_this_year, _pay))
s_money.capital = 100000.0   # isolate the hours counter from the wealth-dependent living cost
_after = S._agent_dispatch(s_money, NODES, {"cmd": "state"})
check("net_per_year (the 'recurring' figure) does not swing just because this year's hours were sold",
      abs(_after.get("net_per_year") - _net_before) < 5.0, (_net_before, _after.get("net_per_year")))
check("...while net_after_project_spend - explicitly THIS year's figure - still reflects it",
      abs(_after.get("net_after_project_spend") - _net_before) > 50.0,
      (_net_before, _after.get("net_after_project_spend")))
_money_after = S._agent_dispatch(s_money, NODES, {"cmd": "money"}).get("net_per_year")
check("`money`'s net_per_year is insulated from the same one-year swing, matching `state`'s",
      abs(_money_after - _money_before) < 5.0, (_money_before, _money_after))

# stall_diagnosis's own net must be computed the same standing way: reproduce the
# swing test against it on a household that is actually stalled.
s_money = unopened_sim(capital=-40000.0)     # deep enough that the interest outruns the income
s_money.insolvent_years = 20
s_money.wage_hours_this_year = 0
_diag_before = s_money.stall_diagnosis()
_stalled_capital = s_money.capital
check("set-up: this household really is stalled, so stall_diagnosis returns a real diagnosis to compare",
      bool(_diag_before), _diag_before)
s_money.labour.work_for_wages("scholar", 1500)
s_money.capital = _stalled_capital
_diag_after = s_money.stall_diagnosis()
check("stall_diagnosis's own net is insulated from a one-year wage sale the same way net_per_year is",
      _diag_after and _diag_before and _diag_after["you_are_stuck"] == _diag_before["you_are_stuck"],
      (_diag_before, _diag_after))
