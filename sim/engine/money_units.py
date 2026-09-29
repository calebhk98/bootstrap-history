"""The one place book denarii become a civilisation's money.

Authored money (tree revenue, upkeep and capital, the book goods table,
declared money constants) is written in the book's denarii. Money in play is
each civilisation's own coin. The path between them is always
    book denarii -> labour hours -> civilisation money
and nothing else converts.
"""
from sim.constants import declare
from typing import Dict, Iterable, Mapping

BOOK_LABOURER_WAGE_DENARII_PER_HOUR = declare(
    "BOOK_LABOURER_WAGE_DENARII_PER_HOUR", 0.049598551373284096,
    kind="temporary_heuristic", unit="book denarii per labour hour", source=None,
    confidence="D",
    why="The unskilled wage of the book's own reference schedule, which every "
        "authored denarii figure was calibrated against and which the starting "
        "kits were stated in labourer-years from. It goes when authored money "
        "is derived from labour and materials.")

# Node fields authored in book denarii.
NODE_MONEY_FIELDS = ("rev", "up", "cap")


def book_to_hours(denarii: float) -> float:
    return denarii / BOOK_LABOURER_WAGE_DENARII_PER_HOUR


def book_to_money(denarii: float, money_per_labour_hour: float) -> float:
    return book_to_hours(denarii) * money_per_labour_hour


def book_money_factor(money_per_labour_hour: float) -> float:
    """Civilisation money per book denarius."""
    return book_to_money(1.0, money_per_labour_hour)


def convert_book_table(table: Mapping[str, float], money_per_labour_hour: float) -> Dict[str, float]:
    factor = book_money_factor(money_per_labour_hour)
    return {key: value * factor for key, value in table.items()}


def stamp_nodes(nodes: Iterable[dict], schedule_wages: Mapping[str, float],
                money_per_labour_hour: float) -> None:
    """Fill each node's hour fields once from its authored book figures, then
    express its money fields and derived costs in the given coin."""
    for node in nodes:
        for field in NODE_MONEY_FIELDS:
            node["_%s_hours" % field] = book_to_hours(node[field])
    price_nodes(nodes, schedule_wages, money_per_labour_hour)


def price_nodes(nodes: Iterable[dict], schedule_wages: Mapping[str, float],
                money_per_labour_hour: float) -> None:
    """Express every node money field and derived cost in a coin, in place,
    from the hour fields `stamp_nodes` wrote."""
    for node in nodes:
        for field in NODE_MONEY_FIELDS:
            node[field] = node["_%s_hours" % field] * money_per_labour_hour
        node["_labour_cost"] = sum(schedule_wages[trade] * hours
                                   for trade, hours in node["lab"].items())
        node["_material_cost"] = node["_material_hours"] * money_per_labour_hour
        node["_total_cost"] = node["_labour_cost"] + node["_material_cost"] + node["cap"]
        node["_money_per_labour_hour"] = money_per_labour_hour


def rebased_nodes(nodes: Mapping[str, dict], schedule_wages: Mapping[str, float],
                  money_per_labour_hour: float) -> Mapping[str, dict]:
    """The same tree in another coin. Nodes already in that coin are returned
    as they are; otherwise each is copied so a shared tree is never mutated."""
    first = next(iter(nodes.values()), None)
    if first is None or first.get("_money_per_labour_hour") == money_per_labour_hour:
        return nodes
    copies = {node_id: dict(node) for node_id, node in nodes.items()}
    price_nodes(copies.values(), schedule_wages, money_per_labour_hour)
    return copies
