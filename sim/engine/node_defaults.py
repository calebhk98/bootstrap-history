"""The one table of tree-node field defaults, read by the base merge and the mod overlay."""
import copy

# Optional fields every node gets when the author omits them. Capital (`cap_hours`) and upkeep
# (`up_hours`) are absent on purpose: a node that omits them has them derived from its staff and plant
# (`node_capital`, `node_upkeep`, applied by `node_revenue.apply_revenue`).
OPTIONAL_DEFAULTS = {"ph": 60, "lab": {}, "mat": {}, "risk": 0.15, "rev_hours": 0, "sch": 0, "art": 1,
                     "conf": "C", "kb": ""}

# Structural fields filled for every node (the base merge also repairs their types).
STRUCTURAL_DEFAULTS = {"pre": [], "req_any": [], "traits": [], "build_yrs": 0.0, "adopt_yrs": 0.0,
                       "sus": 0, "gov": 0, "dev_years": None, "dev_people": None}

# Fields with no default that the base merge coerces to numbers when a node states them.
STATED_NUMERIC_FIELDS = ("cap_hours", "up_hours")

# Optional fields the base merge coerces to numbers: every numeric default.
NUMERIC_FIELDS = tuple(field for field, value in OPTIONAL_DEFAULTS.items()
                       if isinstance(value, (int, float)))


def fill_defaults(node):
    """Add every missing default field to `node` in place and return it."""
    for table in (OPTIONAL_DEFAULTS, STRUCTURAL_DEFAULTS):
        for field, value in table.items():
            node.setdefault(field, copy.deepcopy(value))
    return node
