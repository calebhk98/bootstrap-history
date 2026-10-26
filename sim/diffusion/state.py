"""The state diffusion owns."""
from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class DiffusionWorld:
    technique_first_run: Dict[str, int] = field(default_factory=dict)   # node -> the year some producer was first seen running it
    technique_record_started: bool = False   # False until the opening's techniques have been stamped
    literacy_said: int = -999                # last year a literacy-census note was printed


@dataclass
class DiffusionSeat:
    # node id -> what the seat chose to do with the invention: {"mode", "published_year", "licensees": {actor id ->
    # {"fee", "royalty", "year"}}}; a node absent from it is on the default
    disclosures: Dict[str, Dict[str, Any]] = field(default_factory=dict)
