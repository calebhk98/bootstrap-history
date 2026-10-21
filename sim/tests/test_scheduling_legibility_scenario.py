"""Project scheduling made legible, through running games (the rules are test_scheduling_legibility): (1) the
allocator stores why each active project got its share and `portfolio` prints those same numbers; (2) `portfolio`
reads the trade demand the aggregate computes, and `start` says an oversubscription in its confirmation without
blocking the start; (3) a multi-year `step` warns before wasting hours, can be silenced, and still runs."""
from .harness import *  # noqa: F401,F403
from sim.ui.protocol import _agent_portfolio as _APORT

# --- 1. per-project allocation, read from the allocator itself. Two founder-hours-only institutions share one pool:
# the doctorate started second and so sits at the front of `order` (priority 1, offered its 150 hours against the whole
# pool); the curriculum is priority 2, offered its 120 against what was left after the first one's share.
_s_alloc = sim(civ="rome_100ad", capital=5_000_000.0, surveyed=())
_s_alloc.done.update({"school_founded", "fin_university", "sc2_institution_examination"})
_s_alloc._done_changed()
_s_alloc.end_year = _s_alloc.cfg["start_year"] + _s_alloc.cfg["horizon_years"]
_s_alloc.start_project("sc2_institution_curriculum")
_s_alloc.start_project("sc2_institution_doctorate")
_s_alloc._run_seat_work()    # the year's project work (start, materials, progress) without the economy around it
_st_doc = _s_alloc.active["sc2_institution_doctorate"]
_st_cur = _s_alloc.active["sc2_institution_curriculum"]
check("the allocator stores WHY a project got its share: the pool total, the project's rank in the queue and how many "
      "projects shared the pool",
      _st_doc["pool_rank_this_year"] == 1 and _st_cur["pool_rank_this_year"] == 2
      and _st_doc["pool_active_count_this_year"] == 2 and _st_cur["pool_active_count_this_year"] == 2
      and _st_doc["pool_total_this_year"] == 2000.0, (_st_doc, _st_cur))
check("the higher-priority project's share came off the FULL pool, and the next in line saw only what was left after it",
      _st_doc["pool_remaining_before_this_year"] == 2000.0
      and _st_cur["pool_remaining_before_this_year"] == 2000.0 - _st_doc["hours_offered_this_year"]
      and _st_doc["hours_offered_this_year"] == 150.0 and _st_cur["hours_offered_this_year"] == 120.0,
      (_st_doc["pool_remaining_before_this_year"], _st_cur["pool_remaining_before_this_year"]))
_pf_alloc = S._agent_dispatch(_s_alloc, NODES, {"cmd": "portfolio"})
_pf_rows = {row["id"]: row for row in _pf_alloc["projects"]}
_pf_parsed_rows = {row["id"]: row for row in json.loads(json.dumps(_pf_alloc))["projects"]}
check("`portfolio` prints the SAME numbers the allocator stored, also through a json round trip",
      all(_pf_rows[node_id][key] == state[key] == _pf_parsed_rows[node_id][key]
          for node_id, state in (("sc2_institution_doctorate", _st_doc), ("sc2_institution_curriculum", _st_cur))
          for key in ("hours_offered_this_year", "pool_rank_this_year")), _pf_rows)

# --- 2. portfolio reads the aggregate, and `start` warns of an oversubscription without blocking it
_s_dem = unopened_sim(civ="rome_100ad", capital=5_000_000.0)
_dem_targets = sorted(node_id for node_id in NODES if (NODES[node_id].get("lab") or {}).get("chemist"))[:6]
for _k in _dem_targets:
    _s_dem.active[_k] = dict(ph_left=float(NODES[_k]["ph"]), yrs=0.0, spent=0.0, cost_left=_s_dem.project_cost(_k),
                             lab_left=dict(NODES[_k]["lab"]))
_dem_real_hycco = _s_dem.labour.hours_you_can_call_on
_s_dem.labour.hours_you_can_call_on = lambda trade, _fallback=_dem_real_hycco: 1500.0 if trade == "chemist" else _fallback(trade)
_dvs = _s_dem.trade_demand_vs_supply()
_expect_demand = sum(_s_dem.trade_draw_plan(node_id, None).get("chemist", {}).get("desired", 0.0) for node_id in _dem_targets)
_port_dem_row = next(row for row in _APORT(_s_dem, NODES)["trade_hours_demand_vs_supply"] if row["trade"] == "chemist")
check("six chemist-using projects against a pinned 1,500-hour supply: the game's demand is each project's own plan summed, "
      "oversubscribed, naming all six; and `portfolio` reads the identical numbers",
      abs(_dvs["chemist"]["demand_hours_this_year"] - _expect_demand) < 0.5 and _expect_demand > 1500.0
      and _dvs["chemist"]["oversubscribed"] is True and set(_dvs["chemist"]["projects_drawing_on_it"]) == set(_dem_targets)
      and _port_dem_row["demand_hours_this_year"] == _dvs["chemist"]["demand_hours_this_year"],
      (_dvs["chemist"], _port_dem_row))

_s_over = unopened_sim(civ="rome_100ad", capital=5_000_000.0)
_s_over.trades_created.add("chemist")
_s_over.employees["chemist"] = 20.0
_s_over.labour._resync_pools()
_over_real_hycco = _s_over.labour.hours_you_can_call_on
_s_over.labour.hours_you_can_call_on = lambda trade, _fallback=_over_real_hycco: 150.0 if trade == "chemist" else _fallback(trade)
_s_over.done.update(NODES["md2_local_anaesthesia"]["pre"])
_s_over.done.update(NODES["md2_staining_methylene"]["pre"])
_ok_over, _why_over = _s_over.start_project("md2_local_anaesthesia")
_resp_over = S._agent_dispatch(_s_over, NODES, {"cmd": "start", "id": "md2_staining_methylene"})
check("a second chemist-needing project that fits alone but not alongside the first starts, says so in the confirmation "
      "(trade, new total, supply), and is not blocked",
      _ok_over and _resp_over.get("ok") is True and "chemist" in (_resp_over.get("this_oversubscribes_a_trade") or "")
      and "180" in _resp_over["this_oversubscribes_a_trade"] and "150" in _resp_over["this_oversubscribes_a_trade"]
      and "md2_staining_methylene" in _s_over.active, (_why_over, _resp_over.get("this_oversubscribes_a_trade")))

# --- 3. a multi-year step warns before wasting hours, can be silenced, and still runs
_s_idle = _s_alloc            # the two-project game of section 1, whose project work has already run once
assert S._agent_state(_s_idle, NODES).get("free_hours_going_unused"), \
    "the idle-hours condition must be live or 'no warning' would hold for the wrong reason"
_real_step = _s_idle.step
_s_idle.step = lambda: None
try:
    _resp_1yr = S._agent_dispatch(_s_idle, NODES, {"cmd": "step", "years": 1})
finally:
    _s_idle.step = _real_step
_pre_idle_hours = max(0.0, _s_idle.labour.director_pool() - _s_idle.labour.director_hours_committed())
_warning_config_path = os.path.join(tempfile.mkdtemp(), "cfg.json")
_previous_config_env = os.environ.get("ROME_SIM_CONFIG")
os.environ["ROME_SIM_CONFIG"] = _warning_config_path
try:
    json.dump({"multi_year_step_warning": False}, open(_warning_config_path, "w"))
    _quiet_years_run = []
    _s_idle.step = lambda: _quiet_years_run.append(1)
    _resp_quiet = S._agent_dispatch(_s_idle, NODES, {"cmd": "step", "years": 2})
finally:
    _s_idle.step = _real_step
    if _previous_config_env is None:
        os.environ.pop("ROME_SIM_CONFIG", None)
    else:
        os.environ["ROME_SIM_CONFIG"] = _previous_config_env
_year_before = _s_idle.year
_resp_idle = S._agent_dispatch(_s_idle, NODES, {"cmd": "step", "years": 2})
check("a single-year step carries no warning; with the setting off a multi-year step does not warn and still runs",
      _resp_1yr.get("multi_year_hours_warning") is None
      and _resp_quiet.get("ok") is True and not _resp_quiet.get("multi_year_hours_warning") and len(_quiet_years_run) == 2,
      (_resp_1yr.get("multi_year_hours_warning"), _resp_quiet.get("multi_year_hours_warning")))
check("a multi-year step warns up front with the founder-hours at stake read from the same figure `state` reports, "
      "and proceeds",
      bool(_resp_idle.get("multi_year_hours_warning")) and "{:,.0f}".format(_pre_idle_hours) in _resp_idle["multi_year_hours_warning"]
      and _resp_idle.get("ok") is True and _resp_idle["year"] > _year_before,
      (_pre_idle_hours, _resp_idle.get("multi_year_hours_warning")))
