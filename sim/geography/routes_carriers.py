"""The carriers a mode wears out: what one working team is made of and the tonne-km it moves in a day.

A team is the set of carrier things that work together: a cart and the oxen that pull it, a string of mules
each with a pack saddle, a hull. Each entry is (kind, name, count) where kind is `vehicle` or `animal` (the
name the mode's `carrier` gives) or `model` (the mode's own model, for a carrier that is the hull or rig itself).
The economy turns these into the wear a tonne-km does (sim/economy/carriage_wear.py).

Standalone: `transport`, `sea_freight` and the map's route modes.
"""
from typing import Any, Dict, Optional, Tuple

from sim.geography import sea_freight, transport
from sim.geography.routes_rates import _named

Team = Tuple[Tuple[Tuple[str, str, float], ...], float, float]    # (carriers, tonne-km per team-day, payload tonnes)


def team_of(mode: Dict[str, Any]) -> Optional[Team]:
    """The team a mode works with on level ground and a dirt track or calm water, or None for a mode whose
    carrier is not worn here (people on foot, herds that walk themselves, rail, steam)."""
    model, carrier = mode["model"], mode.get("carrier", {})
    try:
        if model == "pack":
            inputs = transport.pack_freight_physical_inputs(_named(carrier["animal"]), carrier["string_size"])
            count = float(carrier["string_size"])
            carriers = (("animal", carrier["animal"], count), ("model", "pack", count))
        elif model == "draught":
            inputs = transport.draught_freight_physical_inputs(
                _named(carrier["animal"]), carrier["team_size"], _named(carrier["vehicle"]),
                _named(carrier["surface"]), 0.0)
            carriers = (("animal", carrier["animal"], float(carrier["team_size"])), ("vehicle", carrier["vehicle"], 1.0))
        elif model == "barge":
            inputs = transport.barge_freight_physical_inputs(
                _named(carrier["animal"]), carrier["team_size"], _named(carrier["vehicle"]))
            carriers = (("animal", carrier["animal"], float(carrier["team_size"])), ("vehicle", carrier["vehicle"], 1.0))
        elif model == "sailing":
            inputs = sea_freight.sailing_freight_physical_inputs()
            carriers = (("model", "sailing", 1.0),)
        else:
            return None
    except ValueError:
        return None
    return carriers, inputs.tonne_km_per_day, inputs.cargo_tonnes
