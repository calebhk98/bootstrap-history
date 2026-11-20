"""One spin-up, year by year: output by good, hours hired/offered/wanted and wage by (trade, area), prices, and per
producer and cohort figures. Usage: python3 series_probe.py <civ> <out.jsonl> [first_years] [trimmed_years]"""
import json, random, sys
from sim.economy import api as economy_api
from sim.economy import economy as economy_module
from sim.economy.api import EconomyYearInputs
from sim.engine.ui_port import Sim, load, load_civ
from sim.markets import port_sites
from sim.markets.spin_up import spin_up_years

civ, out = sys.argv[1], sys.argv[2]
first_years, trimmed_years = spin_up_years()
if len(sys.argv) > 3:
    first_years, trimmed_years = int(sys.argv[3]), int(sys.argv[4])
captured = {}
original = economy_module.Economy._outcome


def patched(self, ledger, level, extraction, stocks_at_start):
    markets = {}
    for result in ledger.labour_results:
        markets["%s|%s" % (result.trade, result.area)] = {
            "hired": result.hours_hired, "offered": getattr(result, "hours_offered", None), "wanted": getattr(result, "hours_wanted", None),
            "wage": result.wage, "idle": getattr(result, "idle_hours", None)}
    produced = {}
    for (agent, good), quantity in ledger.output.items():
        produced.setdefault(agent, {})[good] = produced.get(agent, {}).get(good, 0.0) + quantity
    money = self.setup.currency_id
    producers = {}
    for key, producer in self.record.producers.items():
        producers[key] = {"last_runs": producer.last_runs, "capacity": producer.capacity_runs, "staffed": producer.staffed_runs,
                          "expected_sales": producer.expected_sales, "cash": self.record.book.balance(producer.agent_id, money),
                          "expected_prices": dict(producer.expected_prices), "output": produced.get(producer.agent_id, {}),
                          "idle_years": producer.idle_years}
    cohorts = {}
    for key, cohort in self.record.cohorts.items():
        cohorts[key] = {"cash": self.record.book.balance(cohort.agent_id, money), "people": cohort.people, "working": cohort.working_people,
                        "income": cohort.last_year_income, "sold": ledger.hours_sold.get(cohort.agent_id, 0.0),
                        "planned": cohort.planned_spending, "expected": cohort.expected_spending, "target": cohort.cash_target,
                        "shares": cohort.share_wealth or 0.0, "floor_cost": cohort.expected_floor_cost,
                        "work": self._work_hours.get(cohort.agent_id, 0.0),
                        "plot": sum(ledger.own_plot_hours.get(cohort.agent_id, {}).values()) if cohort.agent_id in ledger.own_plot_hours else 0.0}
    held = {}
    weight = self.setup.opening_prices
    for agent in self.record.producers:
        for good, by_tile in self.record.book.holdings(agent)["goods"].items():
            if good in weight:
                held[good] = held.get(good, 0.0) + weight[good] * sum(by_tile.values())
    household_goods = {}
    for key in self.record.cohorts:
        for good, by_tile in self.record.book.holdings(key)["goods"].items():
            if good in weight:
                household_goods[good] = household_goods.get(good, 0.0) + weight[good] * sum(by_tile.values())
    captured.clear()
    captured.update(labour=markets, producers=producers, cohorts=cohorts, held=held, household_goods=household_goods)
    return original(self, ledger, level, extraction, stocks_at_start)


economy_module.Economy._outcome = patched
_t, _p, nodes, _w, _g = load()
game = Sim(nodes, [], random.Random(1), events=False, manual=True, civ=load_civ(civ))
setup = game.view("agent_opening_setup")()
economy = economy_api.blank_economy(setup)
economy_api.begin_spin_up(economy)
inputs = EconomyYearInputs(year=0, population_by_tile={}, yield_factor_by_producer=port_sites.crop_yields(economy), engine_orders={})
with open(out, "w") as handle:
    handle.write(json.dumps({"weight": dict(setup.opening_prices), "unskilled": setup.unskilled_trade}, default=float) + "\n")
    for stage, years in (("first", first_years), ("trimmed", trimmed_years)):
        if stage == "trimmed":
            economy_api.trim_workforce_to_expected_hours(economy)
        for year in range(years):
            outcome = economy.step(inputs)
            state = economy_api.spin_up_state(economy, outcome)
            row = {"stage": stage, "year": year, "state": state, "price_level": outcome.basket_price_level,
                   "rate": economy_api.interest_rate(economy), "output": outcome.output, "prices": outcome.prices, "wages": outcome.wages}
            row.update(captured)
            handle.write(json.dumps(row, default=float) + "\n")
            handle.flush()
print("done")
