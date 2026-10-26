"""The coin module's rules as plain functions of plain values: keeping, carriage and the revaluation of a coin metal."""
from typing import Any, Dict, Iterable, Mapping, Optional

from sim.world import coin_metal

from .constants import CREDIT_PURPOSES, KEEPING_BASIS


def room_under_credit_line(capital, credit_limit, revenue, upkeep, living_cost, mine_cost):
    """Money the year can still spend without capital ending below the negative of the credit limit."""
    return max(0.0, capital + credit_limit + revenue - upkeep - living_cost - mine_cost)


def coin_guard_paid(owed, room):
    """The guard is paid only to the room; the rest of what is owed goes unguarded."""
    return min(owed, room)


def hoard(metal: str, money: float, kg_per_unit: float, keeping_cost_per_year: float) -> Dict[str, Any]:
    """The money held as physical coin: its metal, mass and the yearly cost of keeping it."""
    return {"metal": metal, "tonnes": coin_metal.coin_tonnes(money, kg_per_unit),
            "keeping_cost_per_year": keeping_cost_per_year, "basis": KEEPING_BASIS}


def hoard_report(held: Mapping[str, Any]) -> Dict[str, Any]:
    """A hoard rounded for a screen."""
    return {"metal": held["metal"], "tonnes": round(held["tonnes"], 3),
            "keeping_cost_per_year": round(held["keeping_cost_per_year"], 1), "basis": held["basis"]}


def keeping_due(keeping_owed: float, capital: float, credit_limit: float, revenue: float, upkeep: float,
                living_cost: float, mine_cost: float):
    """(what keeping the household's coin under guard costs this year, what the household pays of it): the guard is
    paid from what the purse and the credit line can bear after the year's other costs, like any other spending."""
    room = room_under_credit_line(capital, credit_limit, revenue, upkeep, living_cost, mine_cost)
    return keeping_owed, coin_guard_paid(keeping_owed, room)


def carriage_money(amount: float, kg_per_unit: float, money_per_tonne: float) -> float:
    """Carriage on `amount` of coin: its mass times the haul's price per tonne, never more than is moved."""
    tonnes = max(0.0, amount) * kg_per_unit / 1000.0
    return min(max(0.0, amount), tonnes * max(0.0, money_per_tonne))


def is_credit(purpose: Any) -> bool:
    """Whether a payment's purpose is a claim on a debtor (interest, a loan), which moves no coin."""
    labels = purpose.keys() if hasattr(purpose, "keys") else (purpose,)
    return all(label in CREDIT_PURPOSES for label in labels)


def abroad(parties: Iterable[Any], home_country: Optional[str]) -> bool:
    """Whether any party stands in another country than home (a party with no record or no country is at home)."""
    for party in parties:
        record = getattr(party, "record", None)
        if record is not None and getattr(record, "country", None) not in (None, home_country):
            return True
    return False

