"""What a mode's working team is made of, and the carrier-days a tonne-km works.

Standalone: the map's mode data only.
"""
from typing import Any, Dict, Optional, Tuple


def composition(mode: Dict[str, Any]) -> Optional[Tuple[Tuple[str, str, float], ...]]:
    """The carriers one working team of the mode is made of, or None for a mode whose carrier is not worn."""
    model, carrier = mode["model"], mode.get("carrier", {})
    try:
        if model == "pack":
            count = float(carrier["string_size"])
            return (("animal", carrier["animal"], count), ("model", "pack", count))
        if model in ("draught", "barge"):
            return (("animal", carrier["animal"], float(carrier["team_size"])), ("vehicle", carrier["vehicle"], 1.0))
        if model == "sailing":
            return (("model", "sailing", 1.0),)
    except KeyError:
        return None
    return None


def carrier_days(carriers: Tuple[Tuple[str, str, float], ...], team_days: float) -> Tuple[Tuple[str, str, float], ...]:
    """(kind, name, carrier-days) a tonne-km works when it takes `team_days` team-days."""
    return tuple((kind, name, count * team_days) for kind, name, count in carriers)
