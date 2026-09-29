"""Cost figures for tools, from the same pricing service the runtime uses.

Material identity never comes from here; it comes from the production
catalogue. Costs need wages and solved prices, and when either cannot be
provided the report says so instead of substituting a book value.
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


class CostsUnavailable(Exception):
    """The wage provider or the price solver could not be reached."""


class CostReport(object):
    """What price_nodes managed to cost, and what it could not."""

    def __init__(self, available, reason="", missing_materials=(), incomplete_nodes=0):
        self.available = available
        self.reason = reason
        self.missing_materials = frozenset(missing_materials)
        self.incomplete_nodes = incomplete_nodes


def load_tree_nodes():
    """{id: node} of the base tree with enabled mods applied; no price data involved."""
    from sim.engine.catalog import load_mod_tree_nodes
    return {node["id"]: node for node in load_mod_tree_nodes(ROOT)}


def runtime_wages():
    """Hourly wage per trade from the live engine's wage provider."""
    try:
        from sim.engine import data
        return dict(data.WAGES)
    except (OSError, ImportError, KeyError) as error:
        raise CostsUnavailable("wage provider unavailable (%s)" % error)


def wage_document(wages):
    """The wage-table shape the solver's wage-ratio helpers read, with the
    default civilisation's coin-anchored money per labour hour."""
    from sim.engine import data
    return {"wage_rates_denarii_per_hour": {trade: {"rate": rate} for trade, rate in wages.items()},
            "money_per_labour_hour": data.MONEY_PER_LABOUR_HOUR}


def solved_material_prices(node_ids, wages):
    """{material: denarii per unit} for every material the solver resolves with all technologies held."""
    from sim.engine import prices as price_solver
    wage_document_for_solver = wage_document(wages)
    try:
        solved = price_solver.solved_prices(frozenset(node_ids), wage_document_for_solver)
    except (OSError, KeyError) as error:
        raise CostsUnavailable("price solver unavailable (%s)" % error)
    return {material: price_solver.hours_to_denarii(hours, wage_document_for_solver)
            for material, hours in solved.prices_in_labour_hours.items()
            if material in solved.resolvable_materials}


def price_nodes(nodes):
    """Set _labour_cost, _material_cost, _total_cost and _cost_missing on every node, in place.

    A cost is a lower bound when _cost_missing is non-empty. When the providers
    are unreachable every cost is None.
    """
    try:
        wages = runtime_wages()
        material_price = solved_material_prices(nodes, wages)
    except CostsUnavailable as error:
        for node in nodes.values():
            node["_labour_cost"] = node["_material_cost"] = node["_total_cost"] = None
            node["_cost_missing"] = []
        return CostReport(False, str(error))
    missing_all = set()
    incomplete = 0
    for node in nodes.values():
        missing = sorted({material for material in node["mat"] if material not in material_price}
                         | {trade for trade in node["lab"] if trade not in wages})
        node["_labour_cost"] = sum(wages.get(trade, 0.0) * hours for trade, hours in node["lab"].items())
        node["_material_cost"] = sum(material_price.get(material, 0.0) * quantity
                                     for material, quantity in node["mat"].items())
        node["_total_cost"] = node["_labour_cost"] + node["_material_cost"] + node["cap"]
        node["_cost_missing"] = missing
        missing_all.update(missing)
        incomplete += bool(missing)
    return CostReport(True, "", missing_all, incomplete)
