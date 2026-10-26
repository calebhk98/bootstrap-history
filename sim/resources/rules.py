"""Workings, depletion and deposits as plain functions of plain values."""
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


def capacity_by_material(workings: Iterable[Dict[str, Any]]) -> Dict[str, float]:
    """Rated capacity of the workings summed by material, in the order the materials were first worked."""
    totals: Dict[str, float] = {}
    for working in workings:
        totals[working["material"]] = totals.get(working["material"], 0.0) + working["capacity"]
    return totals


def depletion_factor(intensity_years: float, floor: float, half_life_years: float) -> float:
    """Share of day-one yield a working still gets after `intensity_years` of working at the pace its ground allows."""
    return max(floor, 1.0 - intensity_years / half_life_years)


def average_depletion(capacities: Sequence[float], factors: Sequence[float]) -> float:
    """The capacity-weighted mean of the workings' depletion factors; 1.0 where no capacity stands."""
    total = sum(capacity for capacity in capacities)
    if total <= 0:
        return 1.0
    return sum(factor * capacity for factor, capacity in zip(factors, capacities)) / total


def cost_scale(depletion: float, floor: float, ceiling: float) -> float:
    """What sinking or running a tonne costs against the derived figure: the same effort recovers less from a worked
    deposit, so it costs more per tonne, bounded."""
    return max(floor, min(ceiling, 1.0 / depletion))


def next_intensity(intensity_years: float, capacity: float, ceiling: float) -> float:
    """A working's intensity-years after one more year at `capacity` against the material's land ceiling."""
    return intensity_years + capacity / max(1.0, ceiling)


def working_yield(capacity: float, depletion: float, deposit_remaining: Optional[float]) -> float:
    """Tonnes a year a working raises: its capacity after depletion, never more than its deposit has left."""
    tonnes = capacity * depletion
    return tonnes if deposit_remaining is None else min(tonnes, deposit_remaining)


def depletion_note(depletion: float) -> Optional[str]:
    """Why a working yields less than the tonnage sunk into it; None when there is nothing to explain."""
    if abs(depletion - 1.0) < 0.01:
        return None
    return ("the easy ore here is %d%% worked out, so the same shaft "
            "yields %d%% of its first-year tonnage; techniques that cut "
            "the labour of the works (drainage, hoisting, blasting, "
            "haulage) lower what the ore costs, not how much a shaft yields"
            % (round((1.0 - depletion) * 100), round(depletion * 100)))


def catalog_hint(materials: Iterable[str]) -> str:
    """The hint naming the materials whose workings are priced from deposits, and the generic fallback."""
    return ("well-known workings: %s - or any other material key the "
            "tree uses (for example aluminium_kg), priced from its own "
            "book price if nothing more specific is known about it"
            % ", ".join(sorted(materials)))


def tranche_fields(tranche: Sequence[Any]) -> Tuple[str, float, float, float, str, Optional[str]]:
    """(material, tonnes a year, year ready, cost paid, order id, deposit id) of a tranche; a missing field is 0.0, "" or None."""
    return (tranche[0], tranche[1], tranche[2], tranche[3] if len(tranche) > 3 else 0.0,
            tranche[4] if len(tranche) > 4 else "", tranche[5] if len(tranche) > 5 else None)


def commission_due(tranches: Iterable[Sequence[Any]], pending: Dict[str, float], year: float
                   ) -> Tuple[List[Dict[str, Any]], List[Sequence[Any]], Dict[str, float]]:
    """(new workings, tranches still being sunk, tonnes still pending by material) once every tranche ready by `year`
    has become exactly one working, commissioned in the year it came on stream."""
    pending = dict(pending)
    commissioned, still = [], []
    for tranche in tranches:
        material, amount, ready, capex_paid, order, deposit_id = tranche_fields(tranche)
        if year >= ready:
            commissioned.append({"material": material, "capacity": amount, "opened_year": ready,
                                 "capex_paid": capex_paid, "order": order, "intensity_yrs": 0.0, "deposit": deposit_id})
            pending[material] = max(0.0, pending.get(material, 0.0) - amount)
            if pending.get(material, 0.0) <= 0:
                pending.pop(material, None)
        else:
            still.append(tranche)
    return commissioned, still, pending


def capacity_naming(workings: Iterable[Dict[str, Any]], tranches: Iterable[Sequence[Any]], deposit_id: str) -> float:
    """Tonnes a year of workings, standing and being sunk, that name this deposit."""
    standing = sum(working["capacity"] for working in workings if working.get("deposit") == deposit_id)
    sinking = sum(tranche[1] for tranche in tranches if len(tranche) > 5 and tranche[5] == deposit_id)
    return standing + sinking


def priced_row(row: Dict[str, Any], size: float, worked_before: float, drawn: float, working_rate: float,
               historical_rate: float, naming: float) -> Dict[str, Any]:
    """A deposit row with its size, what is left of it, the most it yields a year and the room left under that rate."""
    remaining = max(0.0, size * (1.0 - worked_before) - drawn)
    rate = min(max(working_rate, historical_rate), remaining)
    return dict(row, size_tonnes=size, remaining_tonnes=remaining, rate_tonnes_per_year=rate,
                room_tonnes_per_year=max(0.0, rate - naming))


def room_in_deposits(rows: Iterable[Dict[str, Any]], deposit: Optional[str] = None) -> float:
    """Tonnes a year the named deposit, else every row, has room for."""
    return sum(row["room_tonnes_per_year"] for row in rows if deposit is None or row["id"] == deposit)


def allocation_plan(rows: Iterable[Dict[str, Any]], tonnes: float, deposit: Optional[str] = None) -> List[Tuple[str, float]]:
    """[(deposit id, tonnes a year)] naming where `tonnes` of new capacity goes: the named deposit, else the deposits with
    most room first."""
    ranked = sorted((row for row in rows if deposit is None or row["id"] == deposit),
                    key=lambda row: (-row["room_tonnes_per_year"], row["id"]))
    plan, left = [], tonnes
    for row in ranked:
        take = min(left, row["room_tonnes_per_year"])
        if take > 0.0:
            plan.append((row["id"], take))
            left -= take
    return plan
