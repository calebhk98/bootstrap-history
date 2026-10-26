"""The state the resources module owns."""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ResourcesWorld:
    # tile -> tonnes of standing timber felled below the tile's full stock; a missing tile is untouched
    forest_felled: Dict[str, float] = field(default_factory=dict)


@dataclass
class ResourcesSeat:
    # standing workings, each {material, capacity, opened_year, capex_paid, order, intensity_yrs, deposit}, in commission order
    mines: List[Dict[str, Any]] = field(default_factory=list)
    mine_pending: Dict[str, float] = field(default_factory=dict)    # material -> tonnes a year being sunk
    mine_ready: Dict[str, int] = field(default_factory=dict)
    mine_cost_paid: float = 0.0                                     # running costs of the workings paid so far
    # workings being sunk: [material, tonnes a year, year ready, cost paid, order id, deposit id]; None until one is sunk
    mine_tranches: Optional[List[Any]] = None
    # hidden deposits the seat's prospecting found (as geography's prospect returns them), the tonnes drawn from each
    # deposit by id, and the person-days spent prospecting each "tile:resource"
    deposits_found: List[Dict[str, Any]] = field(default_factory=list)
    deposit_drawn: Dict[str, float] = field(default_factory=dict)
    prospected_person_days: Dict[str, float] = field(default_factory=dict)
    forest_ha: float = 0.0
    nitre_bed_m2: float = 0.0
