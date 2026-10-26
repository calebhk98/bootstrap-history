"""The state the disease module owns: who is susceptible, infected or immune, by pathogen and age band."""
from dataclasses import dataclass, field
from typing import Any, Dict, List

EPIDEMICS = "epidemics"   # version channel: the last disease year's deaths by tile


@dataclass
class DiseaseWorld:
    records: Dict[str, Any] = field(default_factory=dict)            # pathogen id -> tile -> age band -> saved Patch
    introduced: Dict[str, List[int]] = field(default_factory=dict)   # pathogen id -> years it arrived
    deaths: Dict[str, int] = field(default_factory=dict)             # pathogen id -> deaths so far
