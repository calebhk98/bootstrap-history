"""The need that plays a role in the economy's books, read from the `role` field of data/world/needs.json (as
`trade_of_role` reads a trade's role): hunger (its unmet floor counts as hunger), fuel (a hearth's cooking fuel is
added to its floor) and household_work (met by hours of household work)."""
from typing import Any, Mapping

HUNGER_ROLE = "hunger"
FUEL_ROLE = "fuel"
HOUSEHOLD_WORK_ROLE = "household_work"


def need_of_role(need_data: Mapping[str, Any], role: str) -> str:
    """The id of the need that plays `role` (the first by id that names it) in the needs data ({"needs": {...}});
    raises ValueError when no need has it."""
    found = sorted(need_id for need_id, spec in need_data["needs"].items() if spec.get("role") == role)
    if not found:
        raise ValueError("no need in the needs data has the role %r" % role)
    return found[0]
