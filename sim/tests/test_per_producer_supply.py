"""Complaints 375, 338, 135: each producer offers at the cost of the entry it runs, the market clears the offers
against demand, a technique nobody runs changes nothing, and one coin stock moves every price.

The pure clearing and the structural test (the market knows nothing of the tech tree) are in
test_producer_market.py; these run the engine."""
from .harness import *  # noqa: F401,F403
from functools import partial

sim = partial(sim, agent_economy=False)   # these checks pin the engine's own yearly material market


import copy

from sim.engine import prices as price_solver

MATERIAL = "fat_kg"


def complete(game, node_id):
    game.state.projects.done.add(node_id)
    game._done_changed()


def run(game, node_id):
    game.state.projects.operating.add(node_id)


original = price_solver.default_production_entries()
patched = dict(original)
probe = sim(civ="rome_100ad", capital=1e9)
source_key = next(key for key, candidate in sorted(original.items())
                  if MATERIAL in (candidate.get("outputs") or {}) and not candidate.get("requires_node"))
cheaper_entry = copy.deepcopy(original[source_key])
cheaper_entry["labour_hours"] = {trade: hours / 2.0 for trade, hours in cheaper_entry["labour_hours"].items()}
unused = next(candidate for candidate in sorted(NODES) if candidate not in price_solver.all_gate_nodes(original)
              and candidate not in probe.state.projects.done and not NODES[candidate]["rev"])
cheaper_entry["requires_node"] = unused
patched["_cheaper_" + MATERIAL] = cheaper_entry
price_solver.reset_caches_for_tests()
price_solver._DEFAULT_PRODUCTION_ENTRIES = patched
try:
    game, twin = sim(civ="rome_100ad", capital=1e9), sim(civ="rome_100ad", capital=1e9)
    commodity = game._material_tag(MATERIAL)[0]
    reference = game._market_entry(commodity)["reference_tonnes"]

    # --- two producers of one good run different entries: different costs.
    own_cost = game.entry_cost_ratio(source_key, MATERIAL)
    cheap_cost = game.entry_cost_ratio("_cheaper_" + MATERIAL, MATERIAL)
    check("an entry costs what the incumbents' route does, at the prices they face", abs(own_cost - 1.0) < 1e-6,
          own_cost)
    check("an entry that needs half the labour costs less", cheap_cost < own_cost - 0.01, (cheap_cost, own_cost))

    # --- the price clears between the producers' costs.
    start = game.market_price_ratio(MATERIAL)
    game.goods_market.note_sale("cheap_firm", commodity, 0.5 * reference, cheap_cost)
    with_cheap = game.market_price_ratio(MATERIAL)
    game.goods_market.note_sale("dear_firm", commodity, 0.5 * reference, 4.0 * own_cost)
    with_both = game.market_price_ratio(MATERIAL)
    check("a cheaper producer entering lowers the price the market clears at", with_cheap < start,
          (start, with_cheap))
    check("...to no less than its own cost", with_cheap >= cheap_cost - 1e-9, (with_cheap, cheap_cost))
    check("a producer whose cost is above the clearing price sells nothing and moves nothing",
          abs(with_both - with_cheap) < 1e-9, (with_cheap, with_both))
    check("the cheaper producer expanded supply", game.goods_market.others_sold_tonnes(commodity) > 0.5 * reference)

    # --- the entrant does not reprice anyone's cost.
    check("a cheaper producer entering does not reprice the incumbents' cost of the good",
          game._material_prices() == twin._material_prices())
    check("...nor another producer's cost", game.entry_cost_ratio(source_key, MATERIAL) == own_cost)

    # --- a held technique nobody runs changes nothing; one producer running it does not reprice the rest.
    held_only = sim(civ="rome_100ad", capital=1e9)
    complete(held_only, unused)
    check("a technique held but run by no producer changes no price",
          held_only._material_prices() == twin._material_prices())
    check("...and no price the market clears at",
          all(held_only.market_price_ratio(material) == twin.market_price_ratio(material)
              for material in ("fat_kg", "wheat_kg", "iron_bar_kg")))
    check("...and no producer's cost", held_only.entry_cost_ratio("_cheaper_" + MATERIAL, MATERIAL) == cheap_cost)
    run(held_only, unused)
    check("one producer running a technique does not reprice every other producer's good",
          held_only._material_prices()[MATERIAL] == twin._material_prices()[MATERIAL])
finally:
    price_solver.reset_caches_for_tests()

# --- the founder's own running concern is a producer: it offers at its own cost.
game = sim(civ="rome_100ad", capital=1e9)
venture = next((node_id for node_id in sorted(game.nodes)
                if game.is_venture(node_id) and game.nodes[node_id].get("_revenue_basis") == "output"
                and game.concern_baskets_now(node_id) is not None and game.concern_baskets_now(node_id).outputs
                and not any(game.material_price_basis(material) == "mature"
                            for material in game.concern_baskets_now(node_id).outputs)), None)
check("a concern whose revenue is its output exists", venture is not None)
if venture is not None:
    material = sorted(game.concern_baskets_now(venture).outputs)[0]
    made_in = game._material_tag(material)[0]
    before = game.founder_concern_offers(made_in)
    run(game, venture)
    after = game.founder_concern_offers(made_in)
    check("a concern the founder runs puts its output on the market", len(after) > len(before), (before, after))
    check("...each offer at the cost of the entry it runs", all(offer.reservation_ratio > 0.0 for offer in after))

# --- one coin stock moves every price, traded or not (Complaint 338).
game, twin = sim(civ="rome_100ad"), sim(civ="rome_100ad")
before_prices, before_wage = dict(game._material_prices()), game.wage_per_hour("labourer")
game._foreign_ledger("probe_partner", create=True)["home_coin_units"] += game.home_coin_stock_units()
after_prices = game._material_prices()
check("the coin stock has doubled", abs(game.home_price_level() - 2.0) < 1e-9, game.home_price_level())
check("doubling the coin stock with goods fixed doubles every price",
      all(abs(after_prices[material] / before_prices[material] - 2.0) < 1e-9 for material in before_prices))
check("...a good that crosses no border included",
      abs(after_prices["hectare_land"] / before_prices["hectare_land"] - 2.0) < 1e-9)
check("...and the wage", abs(game.wage_per_hour("labourer") / before_wage - 2.0) < 1e-9)
check("...while what households buy in real terms does not change",
      all(abs(game.household_demand_ratio(c) - twin.household_demand_ratio(c)) < 1e-9
          for c in ("fat_kg", "wheat_kg")))
game._foreign_ledger("probe_partner")["home_coin_units"] = -0.5 * twin.home_coin_stock_units()
check("a drained coin stock lowers every price",
      all(game._material_prices()[material] < before_prices[material] for material in before_prices))
