"""The crew one plant of a concern needs: the technical size of a firm, whatever the market pays.

In order: a concern that earns from what it makes (`node_output`) turns out what its plant holds or its
staff can work, so the hours its lines ask in a year are the crew of one plant; a node may state the crew
of its plant (`plant_crew_people`); a concern with neither falls back to the founder's supervision rule
(`venture_hands`), which reads its typed takings and is the temporary heuristic still to replace.
A bigger market holds more firms of this size, not a bigger firm.
"""
from typing import Any, Mapping


def derived_hours(node: Mapping[str, Any]) -> float:
    """Hours a year the node's lines ask of their staff, from the plant's data; zero where none is derived."""
    if node.get("_revenue_basis") != "output":
        return 0.0
    return float(sum((node.get("_labour_hours_per_year") or {}).values()))


def uses_fallback(node: Mapping[str, Any]) -> bool:
    """True when the crew comes from the founder's takings-based rule rather than the data."""
    return derived_hours(node) <= 0.0 and not node.get("plant_crew_people")


def plant_crew(node: Mapping[str, Any], hours_per_person_year: float, fallback_people: float) -> float:
    """People one plant of this concern keeps busy; `fallback_people` is the founder's rule for it."""
    hours = derived_hours(node)
    if hours > 0.0:
        return hours / hours_per_person_year
    return float(node.get("plant_crew_people") or fallback_people)
