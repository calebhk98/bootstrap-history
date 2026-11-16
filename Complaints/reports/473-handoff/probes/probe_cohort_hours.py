"""Usage: python3 probe_decomp.py <civ> <first_years> <trimmed_years> <out.jsonl>
Per year: output by good, hired hours by trade, per-recipe producer figures, prices."""
import json, random, sys
from sim.economy import api as economy_api
from sim.economy import economy as economy_module
from sim.economy.api import EconomyYearInputs
from sim.engine.ui_port import Sim, load, load_civ
from sim.markets import port_sites
import numpy

civ, first_years, trimmed_years, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
captured = {}
from sim.economy import household_offers_year as hoy
_orig_ppc = hoy.plot_parameters_by_cohort
def _ppc(setup, record, view, rows, options, hectares_held):
    out = _orig_ppc(setup, record, view, rows, options, hectares_held)
    captured["plot"] = {k: tuple(v) for k, v in out.items() if "sweden_01" in k}
    return out
hoy.plot_parameters_by_cohort = _ppc

import sim.economy.household_work_year as hwy
_orig_gp = hwy.grinding_plan
def _gp(setup, record, view, cohort, hour_value):
    out = _orig_gp(setup, record, view, cohort, hour_value)
    if cohort.tile == "sweden_01":
        captured.setdefault("grind", {})[cohort.agent_id] = [round(hour_value, 4), round(out[1], 4), [[g, round(x, 3)] for g, x in out[0]]]
    return out
hwy.grinding_plan = _gp
from sim.economy import labour_supply as ls
_orig_settle = ls.HourSupply.settle
def _settle(self, wages):
    captured["plan"] = {k: round(v) for k, v in self.plan_hours.items() if "sweden_01" in k}
    captured["work"] = {k: round(v) for k, v in self.work_hours.items() if "sweden_01" in k}
    captured["whole"] = {k: round(v) for k, v in self._hours.items() if "sweden_01" in k}
    out = _orig_settle(self, wages)
    captured["kept"] = {k: round(v) for k, v in self.kept.items() if "sweden_01" in k}
    return out
ls.HourSupply.settle = _settle
WATCH = {'fish_kg', 'peat_kg', 'firewood_kg'}
import sys as _s
original = economy_module.Economy._outcome
def patched(self, ledger, level, extraction, stocks_at_start):
    results = ledger.labour_results
    hired_by_trade, idle_by_trade = {}, {}
    for result in results:
        hired_by_trade[result.trade] = hired_by_trade.get(result.trade, 0.0) + result.hours_hired
        idle_by_trade[result.trade] = idle_by_trade.get(result.trade, 0.0) + result.idle_hours
    by_agent_good = {}
    for (agent, good), quantity in ledger.output.items():
        by_agent_good[agent] = by_agent_good.get(agent, {}); by_agent_good[agent][good] = by_agent_good[agent].get(good, 0.0) + quantity
    recipes = {}
    for producer in self.record.producers.values():
        r = recipes.setdefault(producer.recipe_id, {"n": 0, "last_runs": 0.0, "capacity": 0.0, "staffed": 0.0, "idle_years": 0, "expected": {}, "output": {}})
        r["n"] += 1; r["last_runs"] += max(producer.last_runs, 0.0); r["capacity"] += producer.capacity_runs
        r["staffed"] += producer.staffed_runs or 0.0; r["idle_years"] += producer.idle_years
        for g, p in producer.expected_prices.items():
            r["expected"].setdefault(g, []).append(p)
        for g, q in by_agent_good.get(producer.agent_id, {}).items():
            r["output"][g] = r["output"].get(g, 0.0) + q
    for r in recipes.values():
        r["expected"] = {g: sum(v) / len(v) for g, v in r["expected"].items()}
    mk = {}
    for result in results:
        if result.trade in ("fisher",):
            mk[result.area] = {"wage": result.wage, "hired": result.hours_hired, "vacant": result.vacant_hours, "idle": result.idle_hours,
                               "buyers": {f.agent[-12:]: f.quantity for f in result.fills if f.side == "buy"}}
    cash = {a: self.record.book.balance_by_agent([a], self.setup.currency_id)[a] for a in [p.agent_id for p in self.record.producers.values() if p.recipe_id == "fish_kg"]}
    captured.update(fisher_markets=mk, fish_cash=cash)
    from sim.economy.labour_state import PeopleByTile
    pbt = PeopleByTile(self.record.labour.workforce)
    captured.update(people={t: {k: round(v, 1) for k, v in pbt[t].items() if v > 0} for t in ("sweden_01", "sweden_02", "finland_03")})
    detail = {}
    for producer in self.record.producers.values():
        if producer.recipe_id in WATCH:
            recipe = self.setup.recipes[producer.recipe_id]
            detail[producer.agent_id] = {"recipe": producer.recipe_id, "tile": producer.tile, "capacity": producer.capacity_runs, "last_runs": producer.last_runs,
                "expected_sales": producer.expected_sales, "expected_prices": dict(producer.expected_prices), "yield": producer.yield_factor, "loss": producer.years_of_loss,
                "workshops": producer.workshops, "stock": {g: self.record.book.stock(producer.agent_id, g, producer.tile) for g in recipe.outputs},
                "made": by_agent_good.get(producer.agent_id, {}), "labour": dict(recipe.labour_hours), "rent": producer.land_rent_per_run}
    captured.update(detail=detail)
    captured.update(hired_by_trade=hired_by_trade, idle_by_trade=idle_by_trade, recipes=recipes)
    return original(self, ledger, level, extraction, stocks_at_start)
economy_module.Economy._outcome = patched

_t, _p, nodes, _w, _g = load()
game = Sim(nodes, [], random.Random(1), events=False, manual=True, civ=load_civ(civ))
setup = game.view("agent_opening_setup")()
economy = economy_api.blank_economy(setup)
economy_api.begin_spin_up(economy)
inputs = EconomyYearInputs(year=0, population_by_tile={}, yield_factor_by_producer=port_sites.crop_yields(economy), engine_orders={})
with open(out, "w") as handle:
    for stage, years in (("first", first_years), ("trimmed", trimmed_years)):
        if stage == "trimmed":
            economy_api.trim_workforce_to_expected_hours(economy)
        for year in range(years):
            outcome = economy.step(inputs)
            state = economy_api.spin_up_state(economy, outcome)
            row = {"stage": stage, "year": year, "real_output": state["real_output"], "hired_hours": state["hired_hours"],
                   "output": outcome.output, "prices": outcome.prices, "wages": outcome.wages, "weight": dict(setup.opening_prices)}
            row.update(captured); captured.pop("grind", None)
            handle.write(json.dumps(row, default=float) + "\n"); handle.flush()
