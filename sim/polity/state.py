"""The state polity owns: one seat's standing with its society and with the state."""
from dataclasses import dataclass, field
from typing import Dict, Optional

STANDING = "standing"     # version channel: the seat's reputation, scandal, eminence, familiarity and protection
VALUES = "values"         # version channel: the society's value weights


@dataclass
class PolityWorld:
	value_weights: Dict[str, float] = field(default_factory=dict)   # the society's, from its civilisation, moved by ShiftValueWeight


@dataclass
class PolitySeat:
	reputation: float = 5.0
	scandal: float = 0.0
	scandal_last_year: Optional[float] = None   # the year's opening mark of the scandal
	eminence: float = 0.0
	familiarity: float = 0.0
	protection: float = 0.0
	gov: float = 0.0                            # how far the state's own interests the seat's works have served
	# how the household answers the state's demands: "comply", "refuse", "negotiate" or "conceal" (sim/agents/demand_answer.py)
	demand_stance: str = "comply"
	# money's worth of service offered the state when negotiating; wealth held out of its sight; and how far the state
	# holds the household's refusals against it (0..1)
	service_offer: float = 0.0
	concealed: float = 0.0
	defiance: float = 0.0
	bribes_ytd: float = 0.0
	atrocity: int = 0
	last_withdrawal: Optional[int] = None
	last_military_demand: int = -999
	said_eminence: int = -999
	said_scandal: int = 0
	said_requisition: int = -999
	said_notice_approach: int = 0
	said_confiscation_band: int = -1
