#!/usr/bin/env python3
"""Worked demonstration of the commodity framework in
sim/engine/commodities.py, against the exact cases the brief named. Read
rome/data/world/COMMODITIES.md for the design; this script is proof it
runs, not the documentation.

    python3 rome/sim/demo_commodities.py

Sections 1-6 have no dependency on Sim, a civilization, or a running game:
the standalone framework working on the tech tree and commodities.json
alone, exactly as originally written. Section 7 is the part that changed:
economy.py's wire_chain_report() now calls this SAME propagate_demand()
with a real Sim's own numbers, and that is demonstrated here too, because a
worked example that only ever ran standalone would leave "is it actually
wired in" unanswered.
"""
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))         # rome/sim
ROOT = os.path.dirname(HERE)                               # rome
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "engine"))
import commodities as C
import simulator as S


def load_nodes():
    tree = json.load(open(os.path.join(ROOT, "data", "tech_tree.json")))
    return {n["id"]: n for n in tree["nodes"]}


def rule(title):
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)


def main():
    nodes = load_nodes()
    led = C.CommodityLedger(nodes=nodes)

    rule("1. THE BRIEF'S OWN BULLET LIST, ANSWERED IN ONE CALL")
    report = led.explain("copper", built=[], own_production_t=0.0, demand_t=5.25)
    print("commodity: copper")
    print("  you produce            : %.1f t/yr" % report["you_produce_t_per_yr"])
    print("  you can buy            : %.1f t/yr (of the country's output)" % report["you_can_buy_t_per_yr"])
    print("  the country produces   : %.1f t/yr" % report["country_produces_t_per_yr"])
    print("  producers (tech)       : %s" % [p["node"] for p in report["produced_by"]])
    print("  consumers (tech, count): %d nodes reference copper_kg or copper_ore_kg" % len(report["consumed_by"]))
    print("  trade partners         : %s" % report["trade_partners"]["regions"])
    print("  market value           : %.2f den/kg (base %.2f)" % (report["price_denarii_per_kg"], report["base_price_denarii_per_kg"]))
    print("  monopoly possible       : %s" % report["monopoly_possible"])

    rule("2. AUTOMATED LOOMS MAKE CLOTH MORE AVAILABLE, WHICH DROPS ITS PRICE,")
    print("   WHICH MAKES A HOT AIR BALLOON EASIER (CHEAPER) TO BUILD")
    demand_t = 20000.0    # an illustrative economy-wide demand for cloth, not derived
                            # from any one project's bill of materials -- see COMMODITIES.md
                            # section 4.2 for why this is a separate, aggregate figure.
    cloth = led.commodities["cloth"]
    for built, label in ([], "no loom beyond the baseline"), (["tex_power_loom"], "power loom built"):
        country = led.country_output("cloth", built)
        supply = led.market_available("cloth", built)
        price = led.price("cloth", demand_t, supply)
        mult = led.best_multiplier("cloth", built)
        print("  %-28s: national capacity x%.1f -> country makes %8.0f t/yr, "
              "you can buy %7.0f t/yr, price %.2f den/kg"
              % (label, mult, country, supply, price))
        balloon_linen_kg = nodes["hot_air_balloon"]["mat"]["linen_kg"]
        print("      -> hot_air_balloon's %.0f kg of linen would cost %.1f denarii"
              % (balloon_linen_kg, balloon_linen_kg * price))
    print("   Price fell because supply rose against the same demand -- the one thing")
    print("   economy.py's material_price_factor() cannot do, since it only ever raises")
    print("   a premium above a flat catalogue price. See COMMODITIES.md section 4.1.")

    rule("3. A MONOPOLY: YOU KNOW WHERE COFFEE GROWS AND HOW TO PROCESS IT")
    print("   (coffee is deliberately anachronistic for 100 AD; see commodities.json's")
    print("   coffee.anachronism_note and COMMODITIES.md section 5 -- this proves the")
    print("   MECHANIC, it does not claim Romans drank coffee)")
    marginal_cost = 2.0     # what it actually costs you to grow, process and ship it
    # A hypothetical competitive price: what it would fetch if a rival, with
    # a similar cost of supply, existed to undercut you (monopoly_price()
    # with an alternative_price near marginal cost approximates that floor).
    competitive_price = led.monopoly_price("coffee", marginal_cost, alternative_price=marginal_cost * 1.2)
    sole_price = led.monopoly_price("coffee", marginal_cost, alternative_price=None)
    print("   marginal cost to you        : %.2f den/kg" % marginal_cost)
    print("   if a rival existed (competitive): %.2f den/kg" % competitive_price)
    print("   sole-supplier price you set : %.2f den/kg (bounded by max_margin, no rival exists)" % sole_price)
    print("   your margin                : %.1fx cost, captured because nobody else can compete" % (sole_price / marginal_cost))

    rule("4. A MINE WITH A WATER PUMP AND CHEMICAL EXTRACTION PRODUCES ~20x THE GOLD")
    print("   OF THE REST OF THE COUNTRY COMBINED")
    rest_of_country = led.country_output("gold", built=[])   # nobody else has pump or cyanidation
    your_multiplier = led.best_multiplier("gold", built=["met_mine_pumping", "mt2_cyanidation"])
    your_base_mine_t = 8.6     # a single mine's baseline capacity before either technology, t/yr
    your_output = your_base_mine_t * your_multiplier
    print("   rest of the country (no pump, no cyanidation): %.1f t/yr" % rest_of_country)
    print("   your one mine, water-pumped and cyanide-leached: %.1f t/yr (multiplier x%.1f)"
          % (your_output, your_multiplier))
    print("   your mine outproduces the rest of the country by %.1fx"
          % (your_output / rest_of_country))

    rule("5. THE REAL TEST: DEMAND FOR COPPER WIRE, PROPAGATED BACK TO COPPER ORE,")
    print("   AND FAILING PARTWAY")
    print("   el2_three_wire_distribution_system needs %.0f kg of copper_wire_kg in one build."
          % nodes["el2_three_wire_distribution_system"]["mat"]["copper_wire_kg"])

    print("\n   -- a modest order, 5 t of wire, an ordinary buyer with no mine of their own --")
    modest = led.propagate_demand("copper_wire", 5.0, built=[])
    print("      wire requested %.2f t, delivered %.2f t (%.0f%% met)"
          % (modest["requested_t"], modest["delivered_t"], 100 * modest["met_fraction"]))
    print("      copper requested %.2f t, delivered %.2f t (%.0f%% met)"
          % (modest["children"]["copper"]["requested_t"], modest["children"]["copper"]["delivered_t"],
             100 * modest["children"]["copper"]["met_fraction"]))
    print("      bottlenecks: %s" % (led.bottlenecks(modest) or "none -- fully met"))

    print("\n   -- 'kilometres of copper wire': an industrial order, 500 t/yr, same buyer --")
    big = led.propagate_demand("copper_wire", 500.0, built=[])
    print("      wire requested %.1f t, delivered %.1f t (%.0f%% met)"
          % (big["requested_t"], big["delivered_t"], 100 * big["met_fraction"]))
    copper_node = big["children"]["copper"]
    print("      copper requested %.1f t, delivered %.1f t (%.0f%% met)"
          % (copper_node["requested_t"], copper_node["delivered_t"], 100 * copper_node["met_fraction"]))
    print("      copper's own reachable supply (your share of national output): %.1f t/yr"
          % copper_node["own_capacity_t"])
    print("      bottlenecks: %s" % led.bottlenecks(big))
    print("      -- the smiths' wire-drawing bench is NOT the problem (its own capacity is")
    print("         %.0f t/yr, well above what's asked); there is simply not enough copper" % big["own_capacity_t"])
    print("         being mined to meet the demand. This is the distinction resource_throttle()")
    print("         cannot draw: it would report ONE flat shortage, not say which link broke.")

    print("\n   -- open your own copper mine (100 t/yr) and ask again --")
    fixed = led.propagate_demand("copper_wire", 500.0, built=[], own_production={"copper": 100.0})
    print("      wire delivered %.1f t (%.0f%% met), bottlenecks: %s"
          % (fixed["delivered_t"], 100 * fixed["met_fraction"], led.bottlenecks(fixed) or "none"))

    rule("6. MARKET VALUE, +/- FLUCTUATION")
    rng = random.Random(7)
    series = led.price_series("iron", demand_t=2000.0, supply_t=2475.0, years=10, rng=rng)
    print("   ten years of iron price around its supply/demand fundamental (%.2f den/kg base):"
          % led.commodities["iron"]["base_price_denarii_per_kg"])
    print("   " + ", ".join("%.2f" % p for p in series))

    rule("7. THE SAME MECHANISM, NOW WIRED IN: A REAL SIM'S OWN COPPER NUMBERS")
    print("   economy.py's wire_chain_report() calls THIS SAME propagate_demand(),")
    print("   handed a live Sim's reachable copper instead of commodities.json's own")
    print("   separate national estimate (CommodityLedger's supply_override). Rome")
    print("   and the Norse do not share one number, because they do not share one coastline.")
    _TREE, _PRICES, S_NODES, _WAGES, _GOODS = S.load()
    GOAL = _TREE["meta"]["goal_node"]
    _LAB, ORDER, _B = S.load_strategy("recommended", S_NODES, GOAL)
    for civ in ("rome_100ad", "norse_900ad"):
        sim_s = S.Sim(S_NODES, ORDER, random.Random(1), events=False, manual=True,
                      civ=S.load_civ(civ))
        report = sim_s.wire_chain_report(500.0)
        print("   %-14s: reachable copper %7.1f t/yr -> wire delivered %6.1f t/yr "
              "(%3.0f%% met), bottleneck %s"
              % (civ, report["children"]["copper"]["own_capacity_t"],
                 report["delivered_t"], 100 * report["met_fraction"],
                 C.CommodityLedger().bottlenecks(report) or "none"))
    print("   Unlike section 5's standalone figure, these two numbers come from")
    print("   resource_throttle()'s OWN live accounting (mine_capacity, MARKET_SHARE,")
    print("   mineral_scale) for the actual civilization in play, not a second guess.")

    rule("DONE")
    print("See rome/data/world/COMMODITIES.md for the design, and")
    print("rome/sim/test_regressions.py for the same claims as enforced checks.")


if __name__ == "__main__":
    main()
