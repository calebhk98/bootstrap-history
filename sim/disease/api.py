"""The only door into sim/disease/: what code outside the package may import.

The disease model (Complaints/reports/epidemic-model-research.md section 11): patches of people (age bands that
mix as one) against a pathogen, stepped at sub-year resolution; `sim/engine/disease_port.py` wires it into
`Sim`. The package draws only from its own seeded random generators (a `Patch` carries one), never from `Sim.rng`.
"""
WALL = "two-way"  # nothing here reaches sim/engine/; the engine hands it what it needs (sim/engine/disease_port.py)

from .loader import (CONFIDENCE_TAGS, check_pathogen_data, load_pathogen_plain, load_pathogens, pathogen_ids,
                     pathogen_problems)
from .network import herd_immunity_threshold, reproduction_number, step_length_in_days
from .step import advance_groups, advance_patch, step_groups, step_patch, wane_idle
from .year import YearResult, advance_year, is_circulating
from .types import Patch, Pathogen

__all__ = [
    "Pathogen", "Patch", "step_patch", "advance_patch", "step_groups", "advance_groups", "wane_idle", "advance_year",
    "is_circulating", "YearResult", "reproduction_number", "herd_immunity_threshold",
    "step_length_in_days", "load_pathogens", "load_pathogen_plain", "pathogen_ids", "pathogen_problems",
    "check_pathogen_data", "CONFIDENCE_TAGS",
]
