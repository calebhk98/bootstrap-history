"""labour_productivity: regression checks, run individually with `--only labour_productivity`."""
from .harness import *  # noqa: F401,F403
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
    small = sim(capital=1e9)
    small.labour.hire("smith", 5)
    small.year += 10                 # let the hiring-day pressure fully decay
    big = sim(capital=1e9)
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
s = sim(capital=1e9)
check("with nothing built, an hour of a trade's time is worth exactly an "
      "hour - labour_productivity changes nothing until a real technology "
      "earns it",
      s.labour.labour_productivity("smith") == 1.0, s.labour.labour_productivity("smith"))

before_call_on = s.labour.hours_you_can_call_on("smith")
before_supply = s.labour.market_supply("smith")
s.done.add("met_trip_hammer")
after_call_on = s.labour.hours_you_can_call_on("smith")
after_supply = s.labour.market_supply("smith")
check("a real productivity technology (the trip hammer, whose note says "
      "'much faster than hand hammering') raises the WORK a smith's hours "
      "can produce this year",
      after_call_on > before_call_on * 1.05, (before_call_on, after_call_on))
check("...without changing market_supply - the technology makes the "
      "existing smiths faster, it does not conjure more of them, so hiring "
      "capacity and labour_price_factor are untouched",
      after_supply == before_supply, (before_supply, after_supply))
check("...and leaves an UNRELATED trade's productivity at exactly 1.0 - a "
      "trip hammer for smiths does not make carpenters faster too",
      s.labour.labour_productivity("carpenter") == 1.0, s.labour.labour_productivity("carpenter"))

s2 = s
for _node, _tr, _add in s2.LABOUR_PRODUCTIVITY_SOURCES:
    s2.done.add(_node)
check("stacking every productivity technology this run has wired in never "
      "pushes any trade's multiplier past the cap, however many technologies "
      "a civilization eventually builds",
      all(s2.labour.labour_productivity(trade) <= s2.labour.LABOUR_PRODUCTIVITY_CAP + 1e-9
          for _, trade, _ in s2.LABOUR_PRODUCTIVITY_SOURCES),
      [(trade, s2.labour.labour_productivity(trade)) for _, trade, _ in sorted(
          s2.LABOUR_PRODUCTIVITY_SOURCES, key=lambda r: r[1])])

check("every node named in LABOUR_PRODUCTIVITY_SOURCES is a real node in "
      "the compiled tree, not a name that was never wired to anything",
      all(node_id in NODES for node_id, _, _ in s2.LABOUR_PRODUCTIVITY_SOURCES),
      [node_id for node_id, _, _ in s2.LABOUR_PRODUCTIVITY_SOURCES if node_id not in NODES])
check("every trade named in LABOUR_PRODUCTIVITY_SOURCES is a real trade in "
      "the wage table",
      all(trade in WAGES for _, trade, _ in s2.LABOUR_PRODUCTIVITY_SOURCES),
      [trade for _, trade, _ in s2.LABOUR_PRODUCTIVITY_SOURCES if trade not in WAGES])
# EDUCATING A WHOLE SOCIETY. The user's own question: "can we make the whole
# country's literacy rates improve? What if we make 5,000 schools and
# tractors and food production... can I create a 90%+ literate population?"
# See SocietyMixin.advance_society (society.py).
from sim.labour.labour_allocation import FARM_TRADE as _FARM_TRADE

s_noschool = sim(capital=2000000.0, manual=False)
s_noschool.trades_created.add("electrician")
_gen0 = s_noschool.civ["literacy_general"]
for i in range(1, 401):
    s_noschool.advance_society(s_noschool.year + i)
check("with no school ever running literacy does not move at all - this "
      "is something a society is TAUGHT, not a free drift",
      s_noschool.civ["literacy_general"] == _gen0, s_noschool.civ["literacy_general"])
check("a taught trade never naturalises without a single school ever "
      "running, however long the run",
      "electrician" not in s_noschool.trades_endemic
      and s_noschool.employees.get("electrician", 0.0) == 0.0,
      (sorted(s_noschool.trades_endemic), s_noschool.employees.get("electrician")))

s_school = run_it(sim(capital=2000000.0, manual=False), "school_founded")
_gen0b = s_school.civ["literacy_general"]
_ceil_farming = s_school.literacy_ceiling_general()
for i in range(1, 401):
    s_school.advance_society(s_school.year + i)
check("a single running school in a farming society raises literacy over "
      "generations but plateaus at the ceiling the farm share sets",
      _gen0b < s_school.civ["literacy_general"] <= _ceil_farming + 1e-6
      and _ceil_farming < 0.9,
      (round(s_school.civ["literacy_general"], 3), round(_ceil_farming, 3)))

s_max = run_it(sim(capital=2000000.0, manual=False),
               "school_founded", "academy_network")
s_max.inst_units = {"school_founded": 9.0, "academy_network": 9.0}
# A society with almost nobody left on the farms.
s_max.state.economy.society_labour_hours = {_FARM_TRADE: 0.02, "other": 0.98}
for i in range(1, 701):
    s_max.advance_society(s_max.year + i)
check("heavy schooling in a society with a small farm share, over "
      "centuries, can reach a 90%+ literate general population",
      s_max.civ["literacy_general"] >= 0.9, s_max.civ["literacy_general"])
check("...and never reaches the whole population: some cannot learn to read",
      s_max.civ["literacy_general"] < 1.0, s_max.civ["literacy_general"])
check("the lettered/propertied class closes most of its own gap too, on "
      "the same schooling",
      s_max.civ["literacy_elite"] >= 0.95, s_max.civ["literacy_elite"])

# =============================================================================
# A TRADE THE FOUNDER INTRODUCED BECOMES A TRADE THE SOCIETY HAS. The user's
# sharpest question: "if I invent electricity, you can't say that after 100
# years I still can't find anyone who can make or research generators." See
# SocietyMixin._advance_trade_absorption/_grow_endemic_trade (society.py).
s_teach = run_it(sim(capital=5000000.0, manual=False),
                 "school_founded", "academy_network")
s_teach.inst_units = {"school_founded": 9.0, "academy_network": 9.0}
s_teach.trades_created.add("electrician")
_yrs_needed = s_teach._trade_absorption_years(s_teach._schooling_flow())
check("heavy schooling brings absorption well under the ~110-year "
      "unschooled base, and never under the 35-year one-lifetime floor",
      35.0 <= _yrs_needed < 110.0, _yrs_needed)
_y0 = s_teach.year
_not_yet_year = _y0 + max(1, int(_yrs_needed) - 5)
for yr in range(_y0 + 1, _not_yet_year + 1):
    s_teach.advance_society(yr)
check("...and not endemic before that many years have actually passed",
      "electrician" not in s_teach.trades_endemic, s_teach.year - _y0)
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

s_dif = sim(capital=1000000.0)
check("diffusion_index is 0 with nothing operating",
      s_dif.diffusion_index() == 0.0, s_dif.diffusion_index())
check("a technology nobody has opened for business has nothing to leak",
      s_dif.diffusion_share(_rev_node) == 0.0, s_dif.diffusion_share(_rev_node))
s_dif.done.add(_rev_node); s_dif.operating.add(_rev_node)
s_dif.done_year[_rev_node] = s_dif.year
check("freshly opened, on the day the doors open, none of its edge has "
      "leaked yet - the brief's own requirement, echoing goods_market_factor's",
      s_dif.diffusion_share(_rev_node) == 0.0, s_dif.diffusion_share(_rev_node))
s_dif.year += int(s_dif.VENTURE_DIFFUSION_HALF_LIFE_YEARS)
_half = s_dif.diffusion_share(_rev_node)
check("about half the edge is gone after one half-life",
      0.45 <= _half <= 0.55, _half)
s_dif.year += 400
_far = s_dif.diffusion_share(_rev_node)
check("...but a first mover never loses all of it, however long the "
      "venture runs - capped, like every other saturating share in this file",
      abs(_far - s_dif.VENTURE_DIFFUSION_CAP) < 1e-6, _far)

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

# --- the rubber bug: a node consumed a material nothing in its own ancestry can
# produce, and the game sold it at a flat book price. The rule and its data live
# in data/material_gating.json and sim/engine/validate_material_gating.py.
from sim.engine import validate_material_gating as _gating
_rules = _gating.load_gating(S.ROOT)
_gaps = _gating.check_material_gating(NODES, _rules)
check("every consumer of a gated material has a producer in its own ancestry, "
      "or a declared reason it does not", not _gaps, _gaps)
_probe_nodes = {"maker": {"pre": []}, "user": {"pre": ["maker"], "mat": {"widget_kg": 1}},
                "stranger": {"pre": [], "mat": {"widget_kg": 1}}}
_probe_rule = {"widget_kg": {"producer_nodes": ["maker"]}}
check("the gating rule flags a consumer with no producer and accepts a declared exemption",
      len(_gating.check_material_gating(_probe_nodes, _probe_rule)) == 1
      and _gating.check_material_gating(
          _probe_nodes, {"widget_kg": {**_probe_rule["widget_kg"],
                                       "ungated_consumers": {"stranger": "judged purchasable here"}}}) == [],
      _gating.check_material_gating(_probe_nodes, _probe_rule))

# --- Staffing: one game for `why`'s supervision figure, the staffing closure, the
# automatic reopen, and the price `restore` quotes inside and after the grace window.
s_staff = sim(capital=1_000_000.0)
_SUPERVISED = None
for _candidate_id in sorted(NODES):
    _candidate = NODES[_candidate_id]
    if _candidate["rev"] > 0 and _candidate["sch"] == 0 and _candidate["art"] > 0 and not (_candidate.get("lab") or {}).get("artisan"):
        _scholars, _craftsmen = s_staff.venture_hands(_candidate_id)
        if (_scholars == 0
                and max(_candidate["art"], s_staff.FOUNDER_IS_WORTH + s_staff.STAFFING_CLOSURE_SLACK) < _craftsmen <= 5.5
                and s_staff.venture_foreman(_candidate_id)[0] is None):
            _SUPERVISED = _candidate_id
            break
assert _SUPERVISED, "no concern needs craftsmen to supervise"

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
check("the supervision figure can genuinely exceed the build crew shown as staff_needed",
      _why_open["artisans"] > _why["staff_needed"]["artisans"],
      "staff_needed %s, staff_to_keep_it_open %s" % (_why["staff_needed"], _why_open))
_pure = S._agent_dispatch(s_staff, NODES, {"cmd": "why", "id": "ag2_adulteration_law"})
check("a pure-knowledge node (no revenue, no upkeep) carries no "
      "staff_to_keep_it_open - there is no concern to supervise",
      _pure.get("staff_to_keep_it_open") is None, _pure.get("staff_to_keep_it_open"))

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
check("restoring within the grace window names that it is the discounted "
      "price, not a bare number",
      _ok_in_grace and "discounted tenth" in _msg_in_grace, _msg_in_grace)
s_staff.employees["artisan"] = 0.0
s_staff.labour._resync_pools()
s_staff.close_unstaffed_ventures(s_staff.year)
s_staff.year += s_staff.STAFF_CLOSURE_GRACE + 1
_ok_lapsed, _msg_lapsed = s_staff.restore_work(_SUPERVISED)
check("...and restoring after the window has lapsed says outright that the "
      "discount window is gone and this is the full price",
      _ok_lapsed and "too long for the tenth" in _msg_lapsed, _msg_lapsed)
check("...and the lapsed-window fee really is about ten times the in-grace one",
      float(_msg_lapsed.split("for ")[1].split(" denarii")[0].replace(",", ""))
      > 5 * float(_msg_in_grace.split("for ")[1].split(" denarii")[0].replace(",", "")),
      (_msg_in_grace, _msg_lapsed))

# --- One game for the credit freeze, the standing-figure regression and the stall diagnosis.
s_money = sim(capital=100000.0)

# A first-ever settlement says nothing about a moved date.
s_money.capital = -(s_money.credit_limit() * 1.5)
s_money.last_settlement = -999
_log_start = len(s_money.log)
s_money.enforce_credit_limit(105)
_first_messages = [message for _, message in s_money.log[_log_start:] if "INSOLVENCY SETTLED" in message]
check("a first-ever settlement, with nothing to extend, says nothing about a moved date",
      bool(_first_messages) and "moves with every settlement" not in _first_messages[0], _first_messages)
# A second settlement while an earlier freeze is in force moves the date, and says so.
s_money.capital = -(s_money.credit_limit() * 1.5)
s_money.last_settlement = -999
s_money.credit_frozen_until = 110   # an earlier freeze, STILL in force at yr=105
_log_start = len(s_money.log)
s_money.enforce_credit_limit(105)
check("settling again while an earlier freeze is still in force extends the unlock date...",
      s_money.credit_frozen_until == 117, s_money.credit_frozen_until)
_freeze_messages = [message for _, message in s_money.log[_log_start:] if "INSOLVENCY SETTLED" in message]
check("...and says so in the same event, naming both the old and the new date",
      bool(_freeze_messages) and "110" in _freeze_messages[0] and "117" in _freeze_messages[0],
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
s_money = sim(capital=-4000.0)
s_money.insolvent_years = 20
s_money.wage_hours_this_year = 0
_diag_before = s_money.stall_diagnosis()
check("set-up: this household really is stalled, so stall_diagnosis returns a real diagnosis to compare",
      bool(_diag_before), _diag_before)
s_money.labour.work_for_wages("scholar", 1500)
s_money.capital = -4000.0
_diag_after = s_money.stall_diagnosis()
check("stall_diagnosis's own net is insulated from a one-year wage sale the same way net_per_year is",
      _diag_after and _diag_before and _diag_after["you_are_stuck"] == _diag_before["you_are_stuck"],
      (_diag_before, _diag_after))
