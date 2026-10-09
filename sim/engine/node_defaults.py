"""The one table of tree-node field defaults, read by the base merge and the mod overlay."""
import copy

from sim.constants import declare
from sim.unit_conversions import HOURS_PER_PERSON_YEAR

DEFAULT_CAPITAL_LABOURER_YEARS = declare(
    "DEFAULT_CAPITAL_LABOURER_YEARS", 2.0, kind="temporary_heuristic",
    unit="labourer-years of work", source=None, confidence="D",
    why="Capital a node is taken to need when its author states none: about two years of one "
        "labourer's work in tools and fittings. It goes as each node states its own capital.")
DEFAULT_UPKEEP_LABOURER_YEARS = declare(
    "DEFAULT_UPKEEP_LABOURER_YEARS", 0.4, kind="temporary_heuristic",
    unit="labourer-years of work per year", source=None, confidence="D",
    why="Yearly upkeep a node is taken to need when its author states none: a fifth of its "
        "default capital in repair and replacement. It goes as each node states its own upkeep.")

# Optional fields every node gets when the author omits them.
OPTIONAL_DEFAULTS = {"ph": 60, "lab": {}, "mat": {},
                     "cap_hours": DEFAULT_CAPITAL_LABOURER_YEARS * HOURS_PER_PERSON_YEAR,
                     "up_hours": DEFAULT_UPKEEP_LABOURER_YEARS * HOURS_PER_PERSON_YEAR, "risk": 0.15, "rev_hours": 0, "sch": 0, "art": 1,
                     "conf": "C", "kb": ""}

# Structural fields filled for every node (the base merge also repairs their types).
STRUCTURAL_DEFAULTS = {"pre": [], "req_any": [], "traits": [], "build_yrs": 0.0, "adopt_yrs": 0.0,
                       "sus": 0, "gov": 0, "dev_years": None, "dev_people": None}

# Optional fields the base merge coerces to numbers: every numeric default.
NUMERIC_FIELDS = tuple(field for field, value in OPTIONAL_DEFAULTS.items()
                       if isinstance(value, (int, float)))


def fill_defaults(node):
    """Add every missing default field to `node` in place and return it."""
    for table in (OPTIONAL_DEFAULTS, STRUCTURAL_DEFAULTS):
        for field, value in table.items():
            node.setdefault(field, copy.deepcopy(value))
    return node
