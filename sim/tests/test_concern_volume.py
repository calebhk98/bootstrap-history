"""Complaints 369, 370, 375: a concern's volume follows the production entries its society holds, its takings
follow the price its goods clear at, wider adoption lowers that price, household income follows the wage and
output per head, and a good offered after the opening becomes demand when a need it serves exists."""
from .harness import *  # noqa: F401,F403
from functools import partial

sim = partial(sim, agent_economy=False)   # these checks pin the engine's own yearly material market


import copy

from sim.engine import node_output
from sim.engine import prices as price_solver
from sim.engine.actors import SimWorld


def complete(game, node_id):
    game.state.projects.done.add(node_id)
    game._done_changed()


def run(game, node_id):
    """A producer runs the node's techniques: only then do they reach a price or a concern's volume."""
    game.state.projects.operating.add(node_id)


def close_years(game, years):
    for _year in range(years):
        game._step_market()


def staff_bound_node(game):
    """An output-derived node whose output rises with its staff (so labour per unit binds it), and its entry."""
    production = price_solver.default_production_entries()
    for node_id in sorted(game.nodes):
        node = game.nodes[node_id]
        if node.get("_revenue_basis") != "output" or not (node["sch"] + node["art"]) or node.get("annual_output_t"):
            continue
        goods = game._material_prices()
        base = node_output.output_baskets(node, production, goods)
        doubled = dict(node, sch=node["sch"] * 2, art=node["art"] * 2)
        more = node_output.output_baskets(doubled, production, goods)
        if base and more and sum(more.outputs.values()) > 1.5 * sum(base.outputs.values()) \
                and all(game.material_price_basis(material) != "mature" for material in base.outputs):
            entry = max(node_output.entries_gated_by(node_id, production),
                        key=lambda candidate: sum(candidate["outputs"].values()))
            if sorted(entry["outputs"]) == sorted(base.outputs) and not entry.get("capital"):
                return node_id, entry
    raise AssertionError("no staff-bound node")


def takings(game, node_id):
    return game.concern_takings(node_id, 1.0) * game.node_output_market_factor(game.nodes[node_id])


# --- an entry whose labour per unit halves: the same staff turn out more, and takings follow the price.
probe = sim(civ="rome_100ad", capital=1e9)
node_id, entry = staff_bound_node(probe)
original = price_solver.default_production_entries()
patched = dict(original)
improved = copy.deepcopy(entry)
improved["labour_hours"] = {trade: hours / 2.0 for trade, hours in improved["labour_hours"].items()}
unused = next(candidate for candidate in sorted(NODES) if candidate not in
              price_solver.all_gate_nodes(original) and candidate not in probe.state.projects.done
              and not NODES[candidate]["rev"])
improved["requires_node"] = unused
patched["_improved_" + node_id] = improved
price_solver.reset_caches_for_tests()
price_solver._DEFAULT_PRODUCTION_ENTRIES = patched
try:
    game, twin = sim(civ="rome_100ad", capital=1e9), sim(civ="rome_100ad", capital=1e9)
    check("a concern's volume is its opening's before the technique is held",
          game.concern_volume_ratio(node_id) == 1.0 and game.concern_value_ratio(node_id) == 1.0)
    complete(game, unused)
    check("a technique held but run by no producer changes neither volume nor any price",
          game.concern_volume_ratio(node_id) == 1.0 and game._material_prices() == twin._material_prices())
    run(game, unused)
    check("an entry whose labour per unit halves lets the same staff turn out more",
          game.concern_volume_ratio(node_id) > 1.5, game.concern_volume_ratio(node_id))
    check("...with the staff unchanged", game.nodes[node_id]["sch"] == twin.nodes[node_id]["sch"]
          and game.nodes[node_id]["art"] == twin.nodes[node_id]["art"])
    check("...and an actor's concern puts more of it on the market",
          sum(SimWorld(game).concern_output_tonnes(node_id, material, game.state.scenario.year, 1.0)
              for material in SimWorld(game).materials_made_by(node_id))
          >= SimWorld(twin).concern_output_tonnes(node_id, next(iter(game.concern_baskets_now(node_id).outputs)),
                                                  game.state.scenario.year, 1.0))
    got = takings(game, node_id) / takings(twin, node_id)
    check("a concern's takings rise with its volume, at the price the market clears at",
          got > 1.5 * game.node_output_market_factor(game.nodes[node_id]) / twin.node_output_market_factor(
              twin.nodes[node_id]), got)
    check("...and the technique run by one producer leaves the incumbents' cost of every good they make alone",
          all(game._material_prices()[material] == price for material, price in twin._material_prices().items()
              if twin.material_price_basis(material) == "solved"))
finally:
    price_solver.reset_caches_for_tests()

# --- wider adoption lowers the price: more sellers of a good push its clearing price down.
game = sim(civ="rome_100ad", capital=1e9)
material = "iron_bar_kg"
commodity = game._material_tag(material)[0]
price_before = game.market_price_ratio(material)
game.goods_market.note_sale("another_operator", commodity, game._market_entry(commodity)["reference_tonnes"])
price_after = game.market_price_ratio(material)
check("more operators selling a good lower the price it clears at", price_after < price_before,
      (price_before, price_after))

# --- household income follows productivity and the wage; they buy more.
original = price_solver.default_production_entries()
patched = dict(original)
source_key = next(key for key, candidate in original.items() if "fat_kg" in (candidate.get("outputs") or {}))
cheaper_entry = copy.deepcopy(original[source_key])
cheaper_entry["labour_hours"] = {trade: hours / 2.0 for trade, hours in cheaper_entry["labour_hours"].items()}
cheaper_entry["requires_node"] = unused
patched["_cheaper_fat"] = cheaper_entry
price_solver.reset_caches_for_tests()
price_solver._DEFAULT_PRODUCTION_ENTRIES = patched
try:
    game = sim(civ="rome_100ad", capital=1e9)
    check("household real income is the opening's before any technique",
          abs(game.household_real_income_ratio() - 1.0) < 1e-9, game.household_real_income_ratio())
    demand_before = game.household_demand_ratio("fat_kg")
    complete(game, unused)
    check("household real income does not rise with a technique nobody runs",
          abs(game.household_real_income_ratio() - 1.0) < 1e-9)
    run(game, unused)
    check("household real income does not rise because one producer runs a cheaper entry: the incumbents' "
          "cost is not repriced", abs(game.household_real_income_ratio() - 1.0) < 1e-9)
    commodity = game._material_tag("fat_kg")[0]
    traded_before = game._market_outcome(commodity)[1].quantity_traded_tonnes
    game.goods_market.note_sale("cheap_firm", commodity, game._market_entry(commodity)["reference_tonnes"] * 0.5,
                                game.entry_cost_ratio("_cheaper_fat", "fat_kg"))
    check("...but the market sells more of what that producer makes cheaper",
          game._market_outcome(commodity)[1].quantity_traded_tonnes > traded_before)
    income_before = game.household_income_hours_per_capita()
    demand_before = game.household_demand_ratio("fat_kg")
    game._apply_population_mortality_shock(0.3)
    check("a wage that rises with the scarcity of hands raises household income",
          game.household_income_hours_per_capita() > income_before,
          (income_before, game.household_income_hours_per_capita()))
    income_before = game.household_income_hours_per_capita()
    game.LABOUR_PAY_SHARE_OF_OUTPUT_GAIN = 1.0
    game.state.economy.output_per_head = 1.2
    check("...and so does pay that follows output per head",
          game.household_income_hours_per_capita() > 1.19 * income_before,
          (income_before, game.household_income_hours_per_capita()))
finally:
    price_solver.reset_caches_for_tests()

# --- a good offered after the opening becomes demand when a need it serves exists and it is priced.
GATE = "cn_portland_cement"
HEAT = "cap_heat_3000"      # the clinker needs a heat only this reaches
NEW_GOOD = "cement_portland_kg"
game = sim(civ="rome_100ad", capital=1e9)
check("a good nothing offers at the opening draws no household demand",
      NEW_GOOD not in game.household_new_goods_units() and NEW_GOOD not in game.base_basket()["units"])
complete(game, HEAT)
complete(game, GATE)
run(game, HEAT)
run(game, GATE)
check("once it is priced, households want it", game.household_new_goods_units().get(NEW_GOOD, 0.0) > 0.0)
close_years(game, 2)
check("...it is valued at its introduction price", game.state.economy.introduction_prices.get(NEW_GOOD, 0.0) > 0.0)
twin = sim(civ="rome_100ad", capital=1e9)
close_years(twin, 2)
lines = {material: (quantity, price) for material, quantity, price in game.real_output_lines()}
check("...and counts in real output once the market sells it, at that price, and not before",
      lines.get(NEW_GOOD, (0.0, 0.0))[0] > 0.0
      and lines[NEW_GOOD][1] == game.state.economy.introduction_prices[NEW_GOOD]
      and NEW_GOOD not in {line[0] for line in twin.real_output_lines()}, lines.get(NEW_GOOD))
check("...and real output is the sum of its lines, the new good among them",
      abs(game.real_output_hours() - sum(quantity * price for quantity, price in lines.values()))
      <= 1e-9 * game.real_output_hours())
