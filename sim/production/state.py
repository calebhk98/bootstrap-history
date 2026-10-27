"""The state production owns: one seat's stock of industry experience, kept in the labour core's tenure record."""
from dataclasses import dataclass, field
from typing import Dict


@dataclass
class ProductionSeat:
	# trade -> technique -> retained worker-years of anyone running it (sim/labour/tenure.py, depth.py)
	tenure: Dict[str, Dict[str, float]] = field(default_factory=dict)
	tenure_headcount: Dict[str, float] = field(default_factory=dict)
	industry_seeded: bool = False
	# technique -> worker-years a year the society's opening producers put in (depth.py)
	industry_opening_rate: Dict[str, float] = field(default_factory=dict)
