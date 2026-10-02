"""Node revenue and upkeep against solved costs.

Each node with authored revenue is one of:
- "output": it gates production entries and the data gives it a physical yearly
  output (`node_output`); it earns that output at solved prices less what it buys
  (energy at the price graded to each entry, `energy_prices`), and its upkeep is its
  staff at the civilisation's wages plus the upkeep of its plant (`node_upkeep`).
- "knowledge": a science that makes nothing; it earns nothing.
- "authored": equipment, institutions and services whose product the tree does not
  yet state (what each would physically earn: fees from the people served, a share
  of the trade it enables, the work its machine does). The authored revenue stays,
  held under a payback floor so that cheaper solved inputs cannot turn it into a
  money pump; the authored upkeep stays.

The figures are derived against one civilisation's prices and wages: `for_civilisation`
re-derives them for the civilisation playing, cached on what they depend on.
"""
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

from sim.constants import declare

from . import energy_prices, node_output, node_upkeep

MINIMUM_PAYBACK_YEARS = declare(
    "MINIMUM_PAYBACK_YEARS", 0.25, kind="temporary_heuristic", unit="years", source=None,
    confidence="D",
    why="Authored revenue hours were written against older, higher material costs. "
        "A node whose revenue is neither derived from output nor nil is held to at "
        "most its whole cost divided by this payback, standing for competitors "
        "entering any activity that repays its cost faster. It goes when the tree "
        "states what services, institutions and equipment produce.")

# fields `apply_revenue` sets on a node: what a civilisation's derivation replaces
DERIVED_FIELDS = ("rev_hours", "up_hours", "_revenue_basis", "_upkeep_basis", "_output_per_year",
                  "_purchases_per_year", "_energy_sold_per_year", "_energy_bought_per_year",
                  "_labour_hours_per_year", "_upkeep_hours_parts")

# one entry per derivation actually run, so a test can see a cache hit
derivation_calls: List[Tuple[Any, ...]] = []
# {key: {node id: derived fields}}
_DERIVED_FOR_CIVILISATION: Dict[Tuple[Any, ...], Dict[str, Dict[str, Any]]] = {}


def apply_revenue(nodes: Iterable[dict], goods: Mapping[str, float],
                  wages: Mapping[str, float], money_per_labour_hour: float,
                  energy: Optional[energy_prices.EnergyPrices] = None) -> None:
    """Set each node's `rev_hours`, `up_hours`, `_revenue_basis` and `_upkeep_basis`."""
    from sim.world.labour_market import production_data
    production = production_data()
    energy = energy or energy_prices.pool_only(goods)
    for node in nodes:
        for field in DERIVED_FIELDS[2:]:
            node.pop(field, None)
        authored = node.get("_rev_hours_authored", node.get("rev_hours", 0.0))
        node["_rev_hours_authored"] = authored
        node["_up_hours_authored"] = node.get("_up_hours_authored", node.get("up_hours", 0.0))
        node["up_hours"] = node["_up_hours_authored"]
        if node["_up_hours_authored"] > 0.0:
            node["_upkeep_basis"] = "authored"
        if authored <= 0.0:
            continue
        gated = node_output.entries_gated_by(node["id"], production)
        baskets = node_output.output_baskets(node, production, goods, energy, wages) if gated else None
        if baskets is not None:
            _apply_output(node, baskets, goods, wages, money_per_labour_hour)
        elif node.get("kind") == "SCIENCE" and not gated:
            node["rev_hours"] = 0.0
            node["_revenue_basis"] = "knowledge"
        else:
            node["_revenue_basis"] = "authored"
            node["rev_hours"] = _held_under_floor(node, authored, wages, money_per_labour_hour)


def _apply_output(node: dict, baskets: node_output.Baskets, goods: Mapping[str, float],
                  wages: Mapping[str, float], money_per_labour_hour: float) -> None:
    sold = sum(quantity * goods[material] for material, quantity in baskets.outputs.items())
    sold += sum(basket["value"] for basket in baskets.energy_sold.values())
    bought = sum(quantity * goods.get(material, 0.0) for material, quantity in baskets.purchases.items())
    bought += sum(basket["value"] for basket in baskets.energy_bought.values())
    node["_output_per_year"], node["_purchases_per_year"] = baskets.outputs, baskets.purchases
    node["_energy_sold_per_year"], node["_energy_bought_per_year"] = baskets.energy_sold, baskets.energy_bought
    node["_labour_hours_per_year"] = baskets.labour_hours
    node["rev_hours"] = max(0.0, sold - bought) / money_per_labour_hour
    node["_revenue_basis"] = "output"
    if node["_up_hours_authored"] > 0.0:
        staff = node_upkeep.staff_hours_cost(baskets.labour_hours, wages, money_per_labour_hour)
        build_hours = node_upkeep.plant_build_hours(baskets.plant, goods, wages, money_per_labour_hour)
        wear_hours = node_upkeep.plant_wear_hours(baskets.plant, goods, wages, money_per_labour_hour)
        plant = node_upkeep.maintenance_hours(node, build_hours, wear_hours)
        node["_upkeep_hours_parts"] = {"staff": staff, "plant": plant, "plant_build_hours": build_hours,
                                     "plant_wear_hours": wear_hours}
        node["up_hours"] = staff + plant
        node["_upkeep_basis"] = "derived"


def _build_cost_hours(node: Mapping, wages: Mapping[str, float], money_per_labour_hour: float) -> float:
    return (sum(wages[trade] * hours for trade, hours in node["lab"].items()) / money_per_labour_hour
            + node["_material_hours"] + node["cap_hours"])


def _held_under_floor(node: dict, authored: float, wages: Mapping[str, float],
                      money_per_labour_hour: float) -> float:
    cost_hours = _build_cost_hours(node, wages, money_per_labour_hour)
    if cost_hours <= 0.0:
        return authored
    return min(authored, cost_hours / MINIMUM_PAYBACK_YEARS * (1.0 - 1e-9))


def for_civilisation(nodes: Mapping[str, dict], civ: Mapping[str, Any], schedule: Any) -> Dict[str, dict]:
    """Copies of `nodes` with revenue and upkeep derived at this civilisation's prices and wages, in its
    coin. Cached on what the figures depend on: the civilisation, the gate technologies it holds, its
    wages and the nodes."""
    from sim import solve_prices
    from . import prices as price_solver
    civilization_id = civ["id"]
    document = schedule.document()
    rate = schedule.money_per_labour_hour
    key = (civilization_id, frozenset(civ["starting_techs"]),
           tuple(sorted(solve_prices.wage_ratios_by_trade(document).items())), rate, _what_nodes_state(nodes),
           float(civ["starting_interest_rate"]), price_solver.territory_fingerprint(civ))
    cached = _DERIVED_FOR_CIVILISATION.get(key)
    if cached is None:
        derivation_calls.append(key)
        interest_rate = float(civ["starting_interest_rate"])
        goods, _provenance = price_solver.priced_goods_table(
            civ["starting_techs"], document, civilization_id=civilization_id, civilization=civ)
        energy = energy_prices.graded(civ["starting_techs"], document, goods, civilization_id, interest_rate,
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
                       node.get("_up_hours_authored", node.get("up_hours")), node.get("cap_hours"),
                       node.get("_material_hours"), tuple(sorted(node["lab"].items())))
                      for node_id, node in nodes.items()))
