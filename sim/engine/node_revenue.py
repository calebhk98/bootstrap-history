"""Node revenue, upkeep and capital against solved costs.

A node earns only from what it makes: one named in an entry's `operated_by` earns that output at solved
prices less what it buys (`node_output`, energy at the price graded to each entry, `energy_prices`), and
its upkeep is its entries' staff at the civilisation's wages plus the upkeep of its plant (`node_upkeep`).
A node that makes nothing earns nothing directly; its value is what its mechanics change.

Upkeep of a node that earns from no output is, in order: the figure it states (a mod), the bill of the
programme it runs (labour and consumables stated on the node), a science's staff, or a labelled share of
its build bill. Capital is derived for every node (`node_capital`): the plant its entries state plus
tooling for its named staff places; a node that states `cap_hours` (a mod) keeps that figure.

The figures are derived against one civilisation's prices and wages: `for_civilisation`
re-derives them for the civilisation playing, cached on what they depend on.
"""
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

from sim.constants import declare

from . import energy_prices, node_capital, node_output, node_upkeep

# fields `apply_revenue` sets on a node: what a civilisation's derivation replaces
DERIVED_FIELDS = ("rev_hours", "up_hours", "_revenue_basis", "_upkeep_basis", "_output_per_year",
                  "_purchases_per_year", "_energy_sold_per_year", "_energy_bought_per_year",
                  "_labour_hours_per_year", "_upkeep_hours_parts", "cap_hours", "_capital_basis")

# one entry per derivation actually run, so a test can see a cache hit
derivation_calls: List[Tuple[Any, ...]] = []
# {key: {node id: derived fields}}
_DERIVED_FOR_CIVILISATION: Dict[Tuple[Any, ...], Dict[str, Dict[str, Any]]] = {}


def apply_revenue(nodes: Iterable[dict], goods: Mapping[str, float],
                  wages: Mapping[str, float], money_per_labour_hour: float,
                  energy: Optional[energy_prices.EnergyPrices] = None) -> None:
    """Set each node's `cap_hours`, `rev_hours`, `up_hours` and their bases."""
    from sim.labour.api import production_data
    production = production_data()
    energy = energy or energy_prices.pool_only(goods)
    for node in nodes:
        node["_cap_hours_authored"] = node.get("_cap_hours_authored", node.get("cap_hours"))
        for field in DERIVED_FIELDS[2:]:
            node.pop(field, None)
        node["_rev_hours_authored"] = node.get("_rev_hours_authored", node.get("rev_hours", 0.0))
        node["_up_hours_authored"] = node.get("_up_hours_authored", node.get("up_hours"))
        node["rev_hours"] = 0.0
        gated = node_output.entries_gated_by(node["id"], production)
        operated = any(node["id"] in (entry.get("operated_by") or []) for entry in gated)
        baskets = node_output.output_baskets(node, production, goods, energy, wages) if operated else None
        plant_build_hours = 0.0
        if baskets is not None:
            plant_build_hours = _apply_output(node, baskets, goods, wages, money_per_labour_hour)
        node["cap_hours"], node["_capital_basis"] = node_capital.resolve(node, plant_build_hours)
        if node.get("_revenue_basis") != "output":
            _apply_unlisted_upkeep(node, goods, wages, money_per_labour_hour)


def _apply_unlisted_upkeep(node: dict, goods: Mapping[str, float], wages: Mapping[str, float],
                           money_per_labour_hour: float) -> None:
    """Upkeep of a node that earns from no output (see the module docstring for the order)."""
    stated = node["_up_hours_authored"]
    if stated is not None:
        node["up_hours"] = float(stated)
        basis = "authored"
    else:
        build_bill = (sum(wages[trade] * hours for trade, hours in node["lab"].items()) / money_per_labour_hour
                      + node.get("_material_hours", 0.0) + node["cap_hours"])
        if node_upkeep.is_programme(node):
            node["up_hours"] = (node_upkeep.programme_spending_hours(node, goods, wages, money_per_labour_hour)
                                + node_upkeep.maintenance_hours(node, build_bill))
            basis = "programme"
        elif node.get("kind") == "SCIENCE":
            node["up_hours"] = node_upkeep.staff_places_hours_cost(node, wages, money_per_labour_hour)
            basis = "staff"
        else:
            node["up_hours"] = node_upkeep.unstated_upkeep_hours(node, build_bill)
            basis = "default"
    if node["up_hours"] > 0.0:
        node["_upkeep_basis"] = basis


def _apply_output(node: dict, baskets: node_output.Baskets, goods: Mapping[str, float],
                  wages: Mapping[str, float], money_per_labour_hour: float) -> float:
    """Derive the node's revenue and upkeep from its baskets; returns the build hours of its plant."""
    sold = sum(quantity * goods[material] for material, quantity in baskets.outputs.items())
    sold += sum(basket["value"] for basket in baskets.energy_sold.values())
    bought = sum(quantity * goods.get(material, 0.0) for material, quantity in baskets.purchases.items())
    bought += sum(basket["value"] for basket in baskets.energy_bought.values())
    node["_output_per_year"], node["_purchases_per_year"] = baskets.outputs, baskets.purchases
    node["_energy_sold_per_year"], node["_energy_bought_per_year"] = baskets.energy_sold, baskets.energy_bought
    node["_labour_hours_per_year"] = baskets.labour_hours
    node["rev_hours"] = max(0.0, sold - bought) / money_per_labour_hour
    node["_revenue_basis"] = "output"
    staff = node_upkeep.staff_hours_cost(baskets.labour_hours, wages, money_per_labour_hour)
    build_hours = node_upkeep.plant_build_hours(baskets.plant, goods, wages, money_per_labour_hour)
    wear_hours = node_upkeep.plant_wear_hours(baskets.plant, goods, wages, money_per_labour_hour)
    plant = node_upkeep.maintenance_hours(node, build_hours, wear_hours)
    node["_upkeep_hours_parts"] = {"staff": staff, "plant": plant, "plant_build_hours": build_hours,
                                 "plant_wear_hours": wear_hours}
    node["up_hours"] = staff + plant
    node["_upkeep_basis"] = "derived"
    return build_hours


def for_civilisation(nodes: Mapping[str, dict], civ: Mapping[str, Any], schedule: Any,
                     held_techs: Optional[Iterable[str]] = None) -> Dict[str, dict]:
    """Copies of `nodes` with revenue and upkeep derived at this civilisation's prices and wages, in its
    coin, for the techniques held (default: its starting techniques). Cached on what the figures depend
    on: the civilisation, the gate technologies held, its wages and the nodes."""
    from sim.engine import solve_prices
    from . import prices as price_solver
    civilization_id = civ["id"]
    held = list(civ["starting_techs"] if held_techs is None else held_techs)
    held_gates = frozenset(price_solver.all_gate_nodes()) & frozenset(held)
    document = schedule.document()
    rate = schedule.money_per_labour_hour
    key = (civilization_id, held_gates,
           tuple(sorted(solve_prices.wage_ratios_by_trade(document).items())), rate, _what_nodes_state(nodes),
           float(civ["starting_interest_rate"]), price_solver.territory_fingerprint(civ))
    cached = _DERIVED_FOR_CIVILISATION.get(key)
    if cached is None:
        derivation_calls.append(key)
        interest_rate = float(civ["starting_interest_rate"])
        goods, _provenance = price_solver.priced_goods_table(
            held, document, civilization_id=civilization_id, civilization=civ)
        energy = energy_prices.graded(held, document, goods, civilization_id, interest_rate,
                                      civilization=civ)
        copies = {node_id: dict(node) for node_id, node in nodes.items()}
        apply_revenue(copies.values(), goods, schedule.wages_per_hour(), rate, energy)
        cached = {node_id: {field: node[field] for field in DERIVED_FIELDS if field in node}
                  for node_id, node in copies.items()}
        _DERIVED_FOR_CIVILISATION[key] = cached
    derived = {}
    for node_id, node in nodes.items():
        copy = {field: value for field, value in node.items() if field not in DERIVED_FIELDS}
        copy.update(cached[node_id])
        copy["_derived_for"] = civilization_id
        derived[node_id] = copy
    return derived


def _what_nodes_state(nodes: Mapping[str, dict]) -> int:
    """A signature of the node fields the derivation reads, so equal trees share a derivation."""
    return hash(tuple((node_id, node.get("kind"), node.get("sch"), node.get("art"), node.get("annual_output_t"),
                       node.get("_rev_hours_authored", node.get("rev_hours")),
                       node.get("_up_hours_authored", node.get("up_hours")),
                       node.get("_cap_hours_authored", node.get("cap_hours")),
                       node.get("sch"), node.get("art"),
                       node.get("_material_hours"), tuple(sorted(node["lab"].items())))
                      for node_id, node in nodes.items()))
