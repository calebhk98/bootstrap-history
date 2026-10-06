"""scheduling_legibility: regression checks, run individually with `--only scheduling_legibility`."""
from .harness import *  # noqa: F401,F403
from sim.ui import protocol as _PROTO

# =============================================================================
# PROJECT SCHEDULING, MADE LEGIBLE. A player who had already won the game
# raised this in four separate places across a 500-year run: founder-hours
# reported as free while a cheap project crawled because of the active
# portfolio; one workshop stuck at 60% for a year with no visible cause;
# "waiting on your hours" hard to reconcile with the displayed free hours;
# and trade-hour demand from a shrunk staff competing invisibly across a
# dozen projects. Five things below, one per deliverable.
# =============================================================================
# render_portfolio (_RPORT) is not used in this file, only _agent_portfolio
# (_APORT) below - but it IS used by test_arrears_visibility.py, which gets
# it from harness.py's own re-export rather than importing it here.
from sim.ui.protocol import _agent_portfolio as _APORT

# --- 1. PER-PROJECT ALLOCATION, READ FROM THE ALLOCATOR ITSELF. core.py's
# step() (5. progress) now writes pool_total/rank/active_count/remaining_
# before onto each active project's own st dict AS IT DECIDES each one's
# share, and _agent_state/`portfolio` read those fields back rather than
# recomputing a share that could disagree with what was actually applied.
# Two founder-hours-only institutions (no hired trade at all, so nothing
# here is about staffing) share one pool: sc2_institution_doctorate started
# second and so sits at the front of `order` - priority #1, offered its
# full 150 hours against the WHOLE 2,000-hour pool; sc2_institution_
# curriculum is priority #2, offered its 120 against what was left AFTER
# the first one's share, 1,850.
_s_alloc = sim(civ="rome_100ad", capital=5_000_000.0)
_s_alloc.done.update({"school_founded", "fin_university",
                      "sc2_institution_examination"})
_s_alloc._done_changed()
_s_alloc.start_project("sc2_institution_curriculum")
_s_alloc.start_project("sc2_institution_doctorate")
_s_alloc.step()
_st_doc = _s_alloc.active["sc2_institution_doctorate"]
_st_cur = _s_alloc.active["sc2_institution_curriculum"]
check("the allocator stores WHY a project got its share: pool total, this "
      "project's rank in the queue, and how many active projects shared "
      "the pool, all on the same st dict step() itself decided from",
      _st_doc["pool_rank_this_year"] == 1 and _st_cur["pool_rank_this_year"] == 2
      and _st_doc["pool_active_count_this_year"] == 2
      and _st_cur["pool_active_count_this_year"] == 2
      and _st_doc["pool_total_this_year"] == 2000.0,
      (_st_doc, _st_cur))
check("the higher-priority project's own share came off the FULL pool, and "
      "the next one in line saw only what was left after it - the exact "
      "arithmetic behind 'this project is receiving N of your M available "
      "directed hours because K active projects are sharing attention'",
      _st_doc["pool_remaining_before_this_year"] == 2000.0
      and _st_cur["pool_remaining_before_this_year"]
      == 2000.0 - _st_doc["hours_offered_this_year"]
      and _st_doc["hours_offered_this_year"] == 150.0
      and _st_cur["hours_offered_this_year"] == 120.0,
      (_st_doc["pool_remaining_before_this_year"],
       _st_cur["pool_remaining_before_this_year"]))
_pf_alloc = S._agent_dispatch(_s_alloc, NODES, {"cmd": "portfolio"})
_pf_rows = {row["id"]: row for row in _pf_alloc["projects"]}
check("`portfolio` prints the SAME numbers the allocator stored - not a "
      "second guess at them: displayed share and applied share can never "
      "differ, because they are read from the identical st dict",
      _pf_rows["sc2_institution_doctorate"]["hours_offered_this_year"]
      == _st_doc["hours_offered_this_year"]
      and _pf_rows["sc2_institution_doctorate"]["hours_effective_this_year"]
      == _st_doc["hours_effective_this_year"]
      and _pf_rows["sc2_institution_doctorate"]["pool_rank_this_year"]
      == _st_doc["pool_rank_this_year"]
      and _pf_rows["sc2_institution_curriculum"]["hours_offered_this_year"]
      == _st_cur["hours_offered_this_year"],
      _pf_rows)
# THE SAME INVARIANT, THROUGH A JSON ROUND-TRIP - what an agent parsing
# `portfolio json` actually receives, not the live Python dict.
_pf_parsed = json.loads(json.dumps(_pf_alloc))
_pf_parsed_rows = {row["id"]: row for row in _pf_parsed["projects"]}
check("the same equality survives a real json.dumps/json.loads round trip",
      _pf_parsed_rows["sc2_institution_doctorate"]["hours_offered_this_year"]
      == _st_doc["hours_offered_this_year"],
      _pf_parsed_rows["sc2_institution_doctorate"])

# --- 2a. PER-TRADE DEMAND VS SUPPLY, AGGREGATED, BEFORE COMMITTING. "With
# only one active chemist remaining after attrition, numerous projects
# reached ~60% founder work but then stalled because their chemist-hours
# were all competing for the same 3,000 annual trade-hours." Six chemist-
# using projects, one shared trade, supply pinned to 1,500 - well under
# what six projects each wanting hundreds of hours would want at once.
_s_dem = sim(civ="rome_100ad", capital=5_000_000.0)
_dem_targets = sorted(node_id for node_id in NODES
                      if (NODES[node_id].get("lab") or {}).get("chemist"))[:6]
for _k in _dem_targets:
    _n = NODES[_k]
    _s_dem.active[_k] = dict(ph_left=float(_n["ph"]), yrs=0.0, spent=0.0,
                             cost_left=_s_dem.project_cost(_k),
                             lab_left=dict(_n["lab"]))
_dem_real_hycco = _s_dem.labour.hours_you_can_call_on
_s_dem.labour.hours_you_can_call_on = (
    lambda trade, _fallback=_dem_real_hycco: 1500.0 if trade == "chemist" else _fallback(trade))
# INDEPENDENTLY DERIVED, from trade_draw_plan (the same read-only formula
# lab_year_draw itself uses for the demand side) called once per project -
# not the aggregate function under test - so a break in the aggregation
# loop shows up as a mismatch here.
_expect_demand = sum(
    _s_dem.trade_draw_plan(_node_id, None).get("chemist", {}).get("desired", 0.0)
    for _node_id in _dem_targets)
_dvs = _s_dem.trade_demand_vs_supply()
check("trade_demand_vs_supply sums each active project's own read-only "
      "demand for the trade, not a second, independently-guessed total",
      abs(_dvs["chemist"]["demand_hours_this_year"] - _expect_demand) < 0.5,
      (_dvs["chemist"]["demand_hours_this_year"], _expect_demand))
check("...against what the trade can actually supply this year, and flags "
      "the portfolio as oversubscribed on it when demand exceeds supply",
      _dvs["chemist"]["supply_hours_this_year"] == 1500.0
      and _dvs["chemist"]["oversubscribed"] is True
      and _expect_demand > 1500.0, _dvs["chemist"])
check("...and names every project actually drawing on it, so a player can "
      "see which of their own projects are competing, not only that some "
      "of them are",
      set(_dvs["chemist"]["projects_drawing_on_it"]) == set(_dem_targets),
      _dvs["chemist"]["projects_drawing_on_it"])
_port_dem = _APORT(_s_dem, NODES)
_port_dem_row = next(row for row in _port_dem["trade_hours_demand_vs_supply"]
                     if row["trade"] == "chemist")
check("`portfolio`'s own trade-demand table reads the identical numbers, "
      "never a re-derived estimate that could disagree with them",
      _port_dem_row["demand_hours_this_year"]
      == _dvs["chemist"]["demand_hours_this_year"]
      and _port_dem_row["oversubscribed"] == _dvs["chemist"]["oversubscribed"],
      _port_dem_row)

# --- 2b. THE SAME OVERSUBSCRIPTION, VISIBLE AT `start` ITSELF. "The first
# workshop/lab sat at 60% until I stopped adding new work for a year" - a
# player should not have to discover this 60% in. One chemist-needing
# project already active and holding 80 of a pinned 150-hour chemist
# supply; starting a second that alone would fit (100 <= 150) but not
# alongside the first (80 + 100 > 150) must say so AT the moment of
# commitment, not merely let it start silently and crawl.
_s_over = sim(civ="rome_100ad", capital=5_000_000.0)
_s_over.trades_created.add("chemist")
_s_over.employees["chemist"] = 20.0
_s_over.labour._resync_pools()
_over_real_hycco = _s_over.labour.hours_you_can_call_on
_s_over.labour.hours_you_can_call_on = (
    lambda trade, _fallback=_over_real_hycco: 150.0 if trade == "chemist" else _fallback(trade))
_s_over.done.update(NODES["md2_local_anaesthesia"]["pre"])
_s_over.done.update(NODES["md2_staining_methylene"]["pre"])
_ok_over, _why_over = _s_over.start_project("md2_local_anaesthesia")
check("(setup) the first chemist-needing project starts cleanly on its own",
      _ok_over, _why_over)
_resp_over = S._agent_dispatch(_s_over, NODES,
                               {"cmd": "start", "id": "md2_staining_methylene"})
check("a `start` that would oversubscribe a trade says so in the "
      "confirmation itself, naming the trade, the portfolio's new total "
      "demand and what the trade can actually supply",
      _resp_over.get("ok") is True
      and "chemist" in (_resp_over.get("this_oversubscribes_a_trade") or "")
      and "180" in _resp_over["this_oversubscribes_a_trade"]
      and "150" in _resp_over["this_oversubscribes_a_trade"],
      _resp_over.get("this_oversubscribes_a_trade"))
check("...and it does not block the start - overcommitting is still the "
      "player's call, only an informed one now",
      "md2_staining_methylene" in _s_over.active, sorted(_s_over.active))

# --- 3. FIVE PRECISE REASONS, NOT A BLURRED "NOBODY TO DO THE WORK". The
# weak spot the player named was specifically the labour cases: an absolute
# staffing shortage and a trade your OWN other work has booked used to
# share one label and one remedy-less sentence.
from sim.ui.protocol import _portfolio_constraint as _PCON
_s_staff = sim(civ="rome_100ad", capital=1e9)
_staff_k = next(node_id for node_id in NODES if (NODES[node_id].get("lab") or {}).get("chemist"))
_n_staff = NODES[_staff_k]
_s_staff.active[_staff_k] = dict(ph_left=float(_n_staff["ph"]), yrs=0.0,
                                 spent=0.0, cost_left=_s_staff.project_cost(_staff_k),
                                 lab_left=dict(_n_staff["lab"]))
_w_staff = _WO(_s_staff, NODES, _staff_k, _s_staff.active[_staff_k],
              _s_staff.active[_staff_k]["cost_left"])
check("an ABSOLUTE staffing shortage (this society can field none of the "
      "trade at all) is its own precise reason",
      _w_staff.startswith("nobody to do the work") and _PCON(_w_staff) == "staffing",
      _w_staff)

_s_book = _s_staff
_s_book.trades_created.add("chemist")
_s_book.employees["chemist"] = 0.8
_s_book.labour._resync_pools()
_n_book = NODES[_staff_k]
_s_book.active[_staff_k] = dict(ph_left=float(_n_book["ph"]), yrs=0.0,
                                spent=0.0, cost_left=_s_book.project_cost(_staff_k),
                                lab_left=dict(_n_book["lab"]))
# A real competing project, so the portfolio view and the per-project reason
# are testing the same allocation data rather than an invented used-hours
# counter that could equally have been this project's own successful draw.
_other_book = next(node_id for node_id in NODES
                   if node_id != _staff_k and (NODES[node_id].get("lab") or {}).get("chemist")
                   and (NODES[node_id]["lab"]["chemist"] / max(1.0, NODES[node_id]["yrs"])
                        + NODES[_staff_k]["lab"]["chemist"]
                        / max(1.0, NODES[_staff_k]["yrs"])
                        > _s_book.labour.hours_you_can_call_on("chemist")))
_n_other_book = NODES[_other_book]
_s_book.active[_other_book] = dict(
    ph_left=float(_n_other_book["ph"]), yrs=0.0, spent=0.0,
    cost_left=_s_book.project_cost(_other_book),
    lab_left=dict(_n_other_book["lab"]))
_w_book = _WO(_s_book, NODES, _staff_k, _s_book.active[_staff_k],
             _s_book.active[_staff_k]["cost_left"])
check("a trade your OWN other active work has already booked - the society "
      "CAN field it - is a DIFFERENT, distinctly-worded reason with a "
      "different remedy (stop something else, do not go hire or teach)",
      _w_book.startswith("trade hours already booked") and _PCON(_w_book) == "trade_hours"
      and _w_book != _w_staff, _w_book)

_s_mat = sim(civ="rome_100ad", capital=1e9)
_s_mat.active["gunpowder"] = dict(
    ph_left=float(NODES["gunpowder"]["ph"]), yrs=0.0, spent=0.0,
    cost_left=_s_mat.project_cost("gunpowder"), lab_left=dict(NODES["gunpowder"]["lab"]))
_w_mat = _WO(_s_mat, NODES, "gunpowder", _s_mat.active["gunpowder"],
            _s_mat.active["gunpowder"]["cost_left"])
check("a project short of nothing - staff, money, calendar - can still be "
      "waiting on MATERIALS: one economy-wide shortage (here, saltpetre for "
      "gunpowder) scales every project's hours down by the same factor, and "
      "that is now a fifth, distinct, named reason",
      _w_mat.startswith("materials:") and "saltpetre" in _w_mat
      and _PCON(_w_mat) == "materials", _w_mat)
check("calendar and money, the two the player already called clear, are "
      "untouched by any of this",
      _PCON("the calendar") == "calendar"
      and _PCON("money: 40 still owed and this year's instalment of 10 is "
               "more than you can raise") == "money", None)
check("'your hours', enriched with the allocator's own rank/pool figures "
      "(deliverable 1), still classifies as the founder-hours bucket",
      _PCON("your hours") == "founder_hours"
      and _PCON("your hours: priority #1 of 2 active projects sharing "
               "this year's 2,000 directed hours; more") == "founder_hours",
      None)

# --- 4. WARN BEFORE A MULTI-YEAR STEP WASTES HOURS. "Founder-hours do not
# bank. A player can have long calendar-floor projects running, use `step
# 5`, and unintentionally throw away thousands of usable founder-hours if
# they did not fill the portfolio first." Verified against step() itself,
# not assumed: core.py computes `pool` fresh every year from director_pool()
# minus this year's commitments (core.py step(), "4b. start new projects"),
# and nothing on `self` ever carries a leftover balance into the next call -
# it does not partly bank, it does not bank at all, which is exactly the
# player's own assumption, so the warning below says so plainly rather than
# hedging on a partial-banking case that does not exist.
_s_idle = sim(civ="rome_100ad", capital=5_000_000.0)
_s_idle.done.update({"school_founded", "fin_university",
                     "sc2_institution_examination"})
_s_idle._done_changed()
_s_idle.end_year = _s_idle.cfg["start_year"] + _s_idle.cfg["horizon_years"]
_s_idle.start_project("sc2_institution_curriculum")
_s_idle.start_project("sc2_institution_doctorate")
_s_idle.step()
# The warning is computed before any year runs, so the single-year reply is read with the step itself
# turned off; the guard shows the idle-hours condition the warning keys on is live, or "no warning"
# would hold for the wrong reason.
assert S._agent_state(_s_idle, NODES).get("free_hours_going_unused"), \
    "the single-year check needs hours going unused, or it proves nothing"
_real_step = _s_idle.step
_s_idle.step = lambda: None
try:
    _resp_1yr = S._agent_dispatch(_s_idle, NODES, {"cmd": "step", "years": 1})
finally:
    _s_idle.step = _real_step
check("a single-year step never carries this warning - it exists only to "
      "protect a MULTI-year request from spending the same idle year "
      "more than once unnoticed",
      _resp_1yr.get("multi_year_hours_warning") is None, _resp_1yr)
_year_before_multi_step = _s_idle.year
# CAPTURED BEFORE THE STEP RUNS. Once step(years=5) executes it changes the
# pool this year's idle-hours figure was about; the warning has to be
# checked against what the pool was BEFORE any of the five years ran.
_pre_idle_hours = max(0.0, _s_idle.labour.director_pool()
                      - _s_idle.labour.director_hours_committed())
_resp_idle = S._agent_dispatch(_s_idle, NODES, {"cmd": "step", "years": 2})
check("a multi-year step warns, up front, when this year alone already has "
      "substantial founder-hours going to waste and something is genuinely "
      "startable that could use them",
      bool(_resp_idle.get("multi_year_hours_warning"))
      and "founder-hours" in _resp_idle["multi_year_hours_warning"], _resp_idle.get("multi_year_hours_warning"))
check("...names the actual number of hours at stake, read from the same "
      "founder-hours-available figure `state` itself reports, not a second "
      "guess at it",
      "{:,.0f}".format(_pre_idle_hours) in (_resp_idle.get("multi_year_hours_warning") or ""),
      (_pre_idle_hours, _resp_idle.get("multi_year_hours_warning")))
check("it warns and proceeds - the years still actually run",
      _resp_idle.get("ok") is True and _resp_idle["year"] > _year_before_multi_step,
      _resp_idle.get("year"))
