"""SCENARIO (allocate): in a whole game the real allocator (`_run_seat_work`) gives a directed project its hours first, a
standing order survives a save and a load, and a standing work order tops up hours already sold by hand and resets for
the next year. The queue, the offer and the `allocate` command are in test_allocate."""

from .harness import *  # noqa: F401,F403

def _zero_lab(node):
    return {trade: 0.0 for trade in node.get("lab", {})}


# --- scenario: the real allocator gives a directed project its hours first, and `portfolio` reads them back
s = unopened_sim(capital=1e7)
_kA, _kB = "academy_network", "corpus_written"
s.order = [_kA, _kB]
s.project_resource_throttle = lambda node_id: 1.0   # the order of hours is under test, not what the market has in stock
for _k in (_kA, _kB):
    _n = NODES[_k]
    s.active[_k] = dict(ph_left=float(_n["ph"]), yrs=0.0, spent=0.0, cost_left=0.0, lab_left=_zero_lab(_n))
s.hour_allocations[_kB] = 500.0
s._run_seat_work()
check("scenario: the allocator offers a directed project its hours first, the higher-ranked one what is left of the "
      "pool, and the state reads the directive back from the field step wrote",
      s.active[_kB]["hours_offered_this_year"] == 500.0
      and s.active[_kA]["hours_offered_this_year"] == s.labour.director_pool() - 500.0
      and s.active[_kB].get("hours_directed_this_year") == 500.0 and s.active[_kA].get("hours_directed_this_year") is None,
      (s.active[_kB]["hours_offered_this_year"], s.active[_kA]["hours_offered_this_year"]))

# --- scenario: a standing order persists across a save and a load, the same as `policy` does
s = unopened_sim(capital=1e7)
s.hour_allocations["academy_network"] = 321.0
s.hour_allocations["work"] = 77.0
s.work_trade = "scribe"
_save_dir = tempfile.mkdtemp()
_save_path = os.path.join(_save_dir, "rome_allocate_save_test.json")
_protocol.save_state(s, _save_path)
s2 = unopened_sim(capital=1e7)
_protocol.load_state(s2, _save_path)
os.remove(_save_path)
os.rmdir(_save_dir)
check("scenario: standing project and work-for-wages directives, and the work trade, survive a save and a load",
      s2.hour_allocations.get("academy_network") == 321.0 and s2.hour_allocations.get("work") == 77.0
      and s2.work_trade == "scribe", (s2.hour_allocations, s2.work_trade))

# --- scenario: the standing "work" directive tops up hours already sold by hand, then resets for the next year
s = unopened_sim(capital=1e7)   # legacy: the earnings are compared with the engine's own wage-table rate
# Fed by its own farm, so no hunger reprices wages during the step.
s.farm_land.quality, s.farm_land.hectares = 1.3, s.farm_land.hectares * 2.0
_r = S._agent_dispatch(s, NODES, {"cmd": "allocate", "id": "work", "hours": 100, "trade": "labourer"})
_rate_per_hour = (S.ANNUAL_WAGE.get("labourer", 375.0) / s.HOURS_PER_PERSON_YEAR
                  * s.price_index * s.wage_index
                  * (1.0 + min(0.5, s.reputation / 200.0)))
_pay_by_hand, _err = s.labour.work_for_wages("labourer", 40.0)
s.step()
check("scenario: a standing work order naming a trade tops up to the full directive rather than selling it twice, "
      "and its hour tally resets for the next year",
      _r["ok"] and _r.get("trade") == "labourer"
      and abs(s.wages_earned - 100.0 * _rate_per_hour) < 0.01 * 100.0 * _rate_per_hour and s.wage_hours_this_year == 0.0,
      (_r, s.wages_earned, 100.0 * _rate_per_hour, s.wage_hours_this_year))
