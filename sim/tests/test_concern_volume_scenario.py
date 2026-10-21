"""SCENARIO (Complaints 369, 370, 375): in a real game a cheaper entry raises the concern's volume and takings, the market buys
from the cheaper producer, and a good offered after the opening becomes demand and real output. The wage rules are in
test_concern_volume."""
from .harness import *  # noqa: F401,F403

opened_sim = sim    # the default game of the suite, its economy open on the cached spin-up
sim = unopened_sim   # legacy: pins concern takings through the engine's yearly material market

import copy

from sim.agents.api import imitation
from sim.engine import node_output
from sim.engine import prices as price_solver


# a plant may bind before the staff do, so a clear gain is well short of the doubling the labour allows
CLEAR_GAIN = 1.25


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
        if base and more and sum(more.outputs.values()) > CLEAR_GAIN * sum(base.outputs.values()):
            entry = max(node_output.entries_gated_by(node_id, production),
                        key=lambda candidate: sum(candidate["outputs"].values()))
            if sorted(entry["outputs"]) == sorted(base.outputs):
                halved = dict(entry, labour_hours={trade: hours / 2.0 for trade, hours in entry["labour_hours"].items()})
                faster = node_output.output_baskets(node, production, goods, entries=[halved])
                if (faster and sum(faster.outputs.values()) > CLEAR_GAIN * sum(base.outputs.values())   # the plant does not bind first
                        and game.concern_takings(node_id, 1.0) > 0.0):   # and the opening earns from it
                    return node_id, entry
    raise AssertionError("no staff-bound node")


def takings(game, node_id):
    return game.concern_takings(node_id, 1.0) * game.node_output_market_factor(game.nodes[node_id])


# --- SCENARIO: an entry whose labour per unit halves: the same staff turn out more, and takings follow the price.
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
improved["operated_by"] = []       # only the node that gates it brings it in; a copy would be run by the original's operators
patched["_improved_" + node_id] = improved
# the games open on the catalogue as it stands (one economy for all of them, cached); the patched entry is added
# to the catalogue afterwards, and the concern's volume and the entry's cost are read from it at the time
game, twin = sim(civ="rome_100ad", capital=1e9), sim(civ="rome_100ad", capital=1e9)
price_solver.reset_caches_for_tests()
price_solver._DEFAULT_PRODUCTION_ENTRIES = patched
try:
    for veteran in (game, twin):
        veteran.add_industry_years(node_id, 1.0e6)    # a settled concern: its takings follow its volume, not a new plant's learning
    complete(game, unused)
    run(game, unused)
    game.techniques_spread()       # a technique's first sighting is stamped when the society's techniques are read
    game.state.scenario.year += imitation.copy_years(NODES[unused]) + 1
    check("scenario: an entry whose labour per unit halves lets the same staff turn out more",
          game.concern_volume_ratio(node_id) > CLEAR_GAIN, game.concern_volume_ratio(node_id))
    got = takings(game, node_id) / takings(twin, node_id)
    check("scenario: a concern's takings rise with its volume, at the price the market clears at",
          got > CLEAR_GAIN * game.node_output_market_factor(game.nodes[node_id]) / twin.node_output_market_factor(
              twin.nodes[node_id]), got)
    check("...and the technique run by one producer leaves the incumbents' cost of every good they make alone",
          all(game._material_prices()[material] == price for material, price in twin._material_prices().items()
              if twin.material_price_basis(material) == "solved"))
finally:
    price_solver.reset_caches_for_tests()

# (more operators selling a good lowers its price: held by one_goods_market, "a sale by the founder lowers the price the year would close at")

# --- SCENARIO: the market buys from the cheaper producer, which sells at its own cost.
original = price_solver.default_production_entries()
patched = dict(original)
probe = sim(civ="rome_100ad", capital=1e9)
game = sim(civ="rome_100ad", capital=1e9)
cheap_material, source_key = next(
    (material, key) for key, candidate in sorted(original.items()) for material in sorted(candidate.get("outputs") or {})
    if candidate.get("labour_hours") and probe._material_tag(material)[0] == material
    and probe._market_entry(material) is not None and probe.household_demand_ratio(material) > 0.0)
cheaper_entry = copy.deepcopy(original[source_key])
cheaper_entry["labour_hours"] = {trade: hours / 2.0 for trade, hours in cheaper_entry["labour_hours"].items()}
cheaper_entry["requires_node"] = unused
cheaper_entry["operated_by"] = []
patched["_cheaper_good"] = cheaper_entry
price_solver.reset_caches_for_tests()
price_solver._DEFAULT_PRODUCTION_ENTRIES = patched
try:
    commodity = game._material_tag(cheap_material)[0]
    cheap_sold_before = game._market_outcome(commodity)[1].offers_sold_tonnes
    game.goods_market.note_sale("cheap_firm", commodity, game._market_entry(commodity)["reference_tonnes"] * 0.5,
                                game.entry_cost_ratio("_cheaper_good", cheap_material))
    check("...but the market buys more from the producer whose entry is cheaper, which sells at its own cost",
          game._market_outcome(commodity)[1].offers_sold_tonnes > cheap_sold_before)
finally:
    price_solver.reset_caches_for_tests()

# --- SCENARIO: a good offered after the opening becomes demand when a need it serves exists and it is priced.
GATE = "cn_portland_cement"
HEAT = "cap_heat_3000"      # the clinker needs a heat only this reaches
NEW_GOOD = "cement_portland_kg"
game = opened_sim(civ="rome_100ad", capital=1e9)   # opened first, so the good is offered after the opening
check("scenario: a good nothing offers at the opening draws no household demand",
      NEW_GOOD not in game.household_new_goods_units() and NEW_GOOD not in game.base_basket()["units"])
complete(game, HEAT)
complete(game, GATE)
run(game, HEAT)
run(game, GATE)
check("scenario: once it is priced, households want it", game.household_new_goods_units().get(NEW_GOOD, 0.0) > 0.0)
close_years(game, 3)       # the first close values the new good; producers take some years to enter and the economy to trade it
check("...it is valued at its introduction price", game.state.economy.introduction_prices.get(NEW_GOOD, 0.0) > 0.0)
twin = opened_sim(civ="rome_100ad", capital=1e9)
close_years(twin, 3)
lines = {material: (quantity, price) for material, quantity, price in game.real_output_lines()}
check("...and counts in real output once the market sells it, at that price, and not before",
      lines.get(NEW_GOOD, (0.0, 0.0))[0] > 0.0
      and lines[NEW_GOOD][1] == game.state.economy.introduction_prices[NEW_GOOD]
      and NEW_GOOD not in {line[0] for line in twin.real_output_lines()}, lines.get(NEW_GOOD))
check("...and real output is the sum of its lines, the new good among them",
      abs(game.real_output_hours() - sum(quantity * price for quantity, price in lines.values()))
      <= 1e-9 * game.real_output_hours())
