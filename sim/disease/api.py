"""The only door into sim/disease/: what code outside the package may import.

Stage 1 of the disease model (Complaints/reports/epidemic-model-research.md section 11): one patch of people and
one pathogen, stepped at sub-year resolution. Not wired into `Sim` yet. The package draws only from its own
seeded random generators (a `Patch` carries one), never from `Sim.rng`.
"""
WALL = "two-way"  # nothing here reaches sim/engine/; the engine will hand it what it needs (a future disease_port)

from .loader import (CONFIDENCE_TAGS, check_pathogen_data, load_pathogen_plain, load_pathogens, pathogen_ids,
                     pathogen_problems)
from .network import herd_immunity_threshold, reproduction_number, step_length_in_days
from .step import advance_patch, step_patch
from .types import Patch, Pathogen

__all__ = [
    "Pathogen", "Patch", "step_patch", "advance_patch", "reproduction_number", "herd_immunity_threshold",
    "step_length_in_days", "load_pathogens", "load_pathogen_plain", "pathogen_ids", "pathogen_problems",
    "check_pathogen_data", "CONFIDENCE_TAGS",
]
