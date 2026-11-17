"""One producer's money through the years: every per-agent figure the year's ledger holds for it, its cash, capacity and runs.
Usage: python3 agent_flow_probe.py <civ> <producer key> <years>"""
import random, sys
from sim.economy import api as economy_api
from sim.economy import economy as economy_module
from sim.economy.api import EconomyYearInputs
from sim.engine.ui_port import Sim, load, load_civ
from sim.markets import port_sites

civ, key, years = sys.argv[1], sys.argv[2], int(sys.argv[3])
original = economy_module.Economy._outcome
seen = {}


def patched(self, ledger, level, extraction, stocks_at_start):
    producer = self.record.producers.get(key)
    seen.clear()
    if producer is not None:
        agent = producer.agent_id
        for name in sorted(vars(ledger)):
            value = getattr(ledger, name)
            if isinstance(value, dict):
                if agent in value:
                    entry = value[agent]
                    seen[name] = entry if not isinstance(entry, dict) else {k: round(v, 1) if isinstance(v, float) else v for k, v in list(entry.items())[:6]}
                else:
                    hits = {k: v for k, v in value.items() if isinstance(k, tuple) and agent in k}
                    if hits:
                        seen[name] = {str(k): (round(v, 1) if isinstance(v, float) else v) for k, v in list(hits.items())[:6]}
        seen["_cash"] = self.record.book.balance(agent, self.setup.currency_id)
        seen["_capacity"], seen["_runs"], seen["_expected_sales"] = producer.capacity_runs, producer.last_runs, producer.expected_sales
        seen["_cash_target"] = producer.cash_target
        seen["_fields"] = {name: getattr(producer, name) for name in ("staffed_runs", "idle_years", "crew_runs", "land_run_cap") if hasattr(producer, name)}
    return original(self, ledger, level, extraction, stocks_at_start)


economy_module.Economy._outcome = patched
_t, _p, nodes, _w, _g = load()
game = Sim(nodes, [], random.Random(1), events=False, manual=True, civ=load_civ(civ))
setup = game.view("agent_opening_setup")()
economy = economy_api.blank_economy(setup)
economy_api.begin_spin_up(economy)
inputs = EconomyYearInputs(year=0, population_by_tile={}, yield_factor_by_producer=port_sites.crop_yields(economy), engine_orders={})
for year in range(years):
    economy.step(inputs)
    print("year", year, {name: (round(value, 1) if isinstance(value, float) else value) for name, value in seen.items()})
