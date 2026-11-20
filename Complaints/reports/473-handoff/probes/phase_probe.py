"""Phase probe: twin spin-ups differing by households' cash times (1 + eps); in year `watch_year` the year's phases are
wrapped, and after each phase the twins' captured figures are compared.

Usage: python3 phase_probe.py <civ> <eps> <watch_year>
"""
import json
import random
import sys

from sim.economy import api as economy_api
from sim.economy import economy as economy_module
from sim.economy.api import EconomyYearInputs
from sim.engine.ui_port import Sim, load, load_civ
from sim.markets import port_sites
from sim.markets.spin_up_ensemble import perturb_household_cash

civ, eps, watch_year = sys.argv[1], float(sys.argv[2]), int(sys.argv[3])
captures = [{}, {}]
active = [None]          # which twin is stepping, or None when not watched


def money_of(record, setup):
    book = record.book
    return {agent: book.balance(agent, setup.currency_id) for agent in sorted(record.producers.keys())}


def wrap(module, name, before=None, after=None):
    original = getattr(module, name)

    def wrapped(*args, **kwargs):
        if active[0] is not None and before is not None:
            before(captures[active[0]], *args, **kwargs)
        result = original(*args, **kwargs)
        if active[0] is not None and after is not None:
            after(captures[active[0]], result, *args, **kwargs)
        return result
    setattr(module, name, wrapped)


def before_lend(capture, setup, record, view):
    capture["0 money before working-capital lending"] = money_of(record, setup)
    capture["0 expected sales at year start"] = {key: producer.expected_sales for key, producer in sorted(record.producers.items())}
    capture["0 capacity at year start"] = {key: producer.capacity_runs for key, producer in sorted(record.producers.items())}
    capture["0 last runs at year start"] = {key: producer.last_runs for key, producer in sorted(record.producers.items())}


def after_lend(capture, result, setup, record, view):
    capture["1 money after working-capital lending"] = money_of(record, setup)


def after_plans(capture, plans, setup, record, view, arrays, money):
    capture["2 planned runs"] = {key: plans.wanted_runs_by_id().get(key, 0.0) for key in plans.ids}
    capture["2 plan runs (affordable)"] = dict(zip(plans.ids, [float(value) for value in plans.runs]))


def before_labour(capture, setup, record, labour_bids, everyone, ledger, context, supply=None):
    wanted, caps = {}, {}
    for bid in labour_bids.objects():
        key = "%s|%s|%s" % (bid.employer, bid.trade, bid.area)
        wanted[key] = wanted.get(key, 0.0) + bid.hours
        caps[key] = max(caps.get(key, 0.0), bid.maximum_wage)
    capture["3 labour hours bid"] = wanted
    capture["3 labour highest cap"] = caps


def after_labour(capture, report, setup, record, labour_bids, everyone, ledger, context, supply=None):
    hired = {}
    for employer, by_trade in sorted(record.labour.hours_paid_by_employer.items()) if hasattr(record.labour, "hours_paid_by_employer") else []:
        for trade, hours in by_trade.items():
            hired["%s|%s" % (employer, trade)] = hours
    capture["4 labour hours hired (last record)"] = hired
    plain = ledger.hours_hired.as_plain()
    capture["4 ledger hours hired"] = {"%s|%s" % (employer, trade): hours for employer, by_trade in sorted(plain.items())
                                       for trade, hours in sorted(by_trade.items())}
    capture["4 wages"] = {"%s|%s" % (area, trade): wage for area, by_trade in sorted(record.labour.workforce.wages.items())
                          for trade, wage in sorted(by_trade.items())}


wrap(economy_module.lending, "lend_working_capital", before_lend, after_lend)
wrap(economy_module.plan_year, "plans_of", None, after_plans)
wrap(economy_module, "clear_labour", before_labour, after_labour)

_tree, _prices, nodes, _wages, _goods = load()
game = Sim(nodes, [], random.Random(1), events=False, manual=True, civ=load_civ(civ))
setup = game.view("agent_opening_setup")()
twins = []
for factor in (1.0, 1.0 + eps):
    economy = economy_api.blank_economy(setup)
    economy_api.begin_spin_up(economy)
    if factor != 1.0:
        perturb_household_cash(economy, factor)
    twins.append(economy)
inputs = [EconomyYearInputs(year=0, population_by_tile={}, yield_factor_by_producer=port_sites.crop_yields(economy), engine_orders={})
          for economy in twins]
for year in range(watch_year + 1):
    for number, (economy, year_inputs) in enumerate(zip(twins, inputs)):
        active[0] = number if year == watch_year else None
        economy.step(year_inputs)
        active[0] = None


def relative(first, second):
    scale = max(abs(first), abs(second))
    return abs(first - second) / scale if scale > 0.0 else 0.0


for name in sorted(captures[0]):
    first, second = captures[0][name], captures[1].get(name, {})
    shared = sorted(first.keys() & second.keys())
    differences = sorted(((relative(first[key], second[key]), key) for key in shared
                          if max(abs(first[key]), abs(second[key])) > 1e-6), reverse=True)
    values = [difference for difference, _key in differences]
    print("== %s: %d shared, %d on one side; differ>1e-6: %d, largest %.3g, median %.3g" % (
        name, len(shared), len(first.keys() ^ second.keys()), sum(1 for value in values if value > 1e-6),
        values[0] if values else 0.0, values[len(values) // 2] if values else 0.0))
    for difference, key in differences[:int(sys.argv[4]) if len(sys.argv) > 4 else 8]:
        if difference > 1e-7:
            print("     %.3g  %s  %.9g  %.9g" % (difference, key, first[key], second[key]))
