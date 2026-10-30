"""The state hazards owns: the world's output factor, the world event log, what the hazards have already told, and
each seat's last patron death."""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

OUTPUT = "output_factor"        # version channels: the output factor, and the world event log
WORLD_EVENTS = "world_events"


@dataclass
class HazardsWorld:
	output_factor: float = 1.0                                  # real output, crushed by war and plague, not by debasement
	world_events: List[Dict[str, Any]] = field(default_factory=list)   # dated records, shared by every seat
	said_output: Optional[Dict[str, int]] = None                # hazard name -> the year its output fall was last told
	said_debasement: Optional[int] = None                       # the year a debasement was last told


@dataclass
class HazardsSeat:
	last_patron_death: Optional[int] = None
	said_condition: Set[str] = field(default_factory=set)       # notices already told to this seat once (hazard conditions, the levy)
