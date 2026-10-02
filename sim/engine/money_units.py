"""Where labour hours become a civilisation's money.

Tree capital, upkeep and revenue are authored in labour hours (`cap_hours`,
`up_hours`, `rev_hours`) and priced here in each civilisation's own coin. The
book goods table and the remaining declared money constants are still written
in the book's denarii and take the path
    book denarii -> labour hours -> civilisation money
and nothing else converts.
"""
from sim.constants import declare
from typing import Iterable, Mapping

BOOK_LABOURER_WAGE_DENARII_PER_HOUR = declare(
    "BOOK_LABOURER_WAGE_DENARII_PER_HOUR", 0.049598551373284096,
    kind="temporary_heuristic", unit="book denarii per labour hour", source=None,
    confidence="D",
    why="The unskilled wage of the book's own reference schedule, which every "
        "authored denarii figure was calibrated against and which the starting "
        "kits were stated in labourer-years from. It goes when authored money "
        "is derived from labour and materials.")

class PricedInLabourHours:
    """A cost declared as labour hours, read as money in the reader's coin.

    The hours live in a declared constant on the class; reading the attribute
    from a `Sim` multiplies them by what one unskilled hour is worth in that
    civilisation's coin, so no authored money is involved.
    """

    def __init__(self, hours_name: str):
        self.hours_name = hours_name

    def __get__(self, sim, owner=None):
        hours = getattr(owner if sim is None else sim, self.hours_name)
        return hours if sim is None else hours * sim.money_per_labour_hour()


def _book_to_hours(denarii: float) -> float:
    return denarii / BOOK_LABOURER_WAGE_DENARII_PER_HOUR


def book_to_money(denarii: float, money_per_labour_hour: float) -> float:
    return _book_to_hours(denarii) * money_per_labour_hour


def book_money_factor(money_per_labour_hour: float) -> float:
    """Civilisation money per book denarius."""
    return book_to_money(1.0, money_per_labour_hour)




def price_nodes(nodes: Iterable[dict], schedule_wages: Mapping[str, float],
                money_per_labour_hour: float) -> None:
    """Express every node's capital, upkeep, revenue and derived costs in a
    coin, in place, from its authored hour fields."""
    for node in nodes:
        for field in ("rev", "up", "cap"):
            node[field] = node[field + "_hours"] * money_per_labour_hour
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
