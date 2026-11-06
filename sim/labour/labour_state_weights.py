"""How a society reacts to a technology: the weight the state gives each tag a technology carries."""
from sim.constants import declare

STATE_WEIGHT_INFRASTRUCTURE = declare(
    "STATE_WEIGHT_INFRASTRUCTURE", 0.5, kind="temporary_heuristic",
    unit="dimensionless state-interest weight", source=None,
    confidence="D",
    why="How favourably the state views a technology tagged "
        "'infrastructure', on the scale state_interest() combines "
        "these weights with. Roughly ordered by plausible period "
        "attitude (infrastructure and food welcomed, a status- or "
        "weapon-democratising technology resisted) but the specific "
        "magnitudes are tuned game balance, not derived from any "
        "state's actual recorded policy.")
STATE_WEIGHT_FOOD = declare(
    "STATE_WEIGHT_FOOD", 0.7, kind="temporary_heuristic",
    unit="dimensionless state-interest weight", source=None,
    confidence="D", why="See STATE_WEIGHT_INFRASTRUCTURE.")
STATE_WEIGHT_MEDICAL = declare(
    "STATE_WEIGHT_MEDICAL", 0.5, kind="temporary_heuristic",
    unit="dimensionless state-interest weight", source=None,
    confidence="D", why="See STATE_WEIGHT_INFRASTRUCTURE.")
STATE_WEIGHT_LUXURY = declare(
    "STATE_WEIGHT_LUXURY", 0.1, kind="temporary_heuristic",
    unit="dimensionless state-interest weight", source=None,
    confidence="D", why="See STATE_WEIGHT_INFRASTRUCTURE.")
STATE_WEIGHT_SPECTACLE = declare(
    "STATE_WEIGHT_SPECTACLE", 0.1, kind="temporary_heuristic",
    unit="dimensionless state-interest weight", source=None,
    confidence="D", why="See STATE_WEIGHT_INFRASTRUCTURE.")
STATE_WEIGHT_INEXPLICABLE = declare(
    "STATE_WEIGHT_INEXPLICABLE", 0.0, kind="temporary_heuristic",
    unit="dimensionless state-interest weight", source=None,
    confidence="D",
    why="A technology the state has no framework to react to earns "
        "neither favour nor suspicion by default. See "
        "STATE_WEIGHT_INFRASTRUCTURE for the rest of this table.")
STATE_WEIGHT_STATUS_THREATENING = declare(
    "STATE_WEIGHT_STATUS_THREATENING", -0.6, kind="temporary_heuristic",
    unit="dimensionless state-interest weight", source=None,
    confidence="D", why="See STATE_WEIGHT_INFRASTRUCTURE.")
STATE_WEIGHT_WEAPON_DEMOCRATISING = declare(
    "STATE_WEIGHT_WEAPON_DEMOCRATISING", -0.5, kind="temporary_heuristic",
    unit="dimensionless state-interest weight", source=None,
    confidence="D", why="See STATE_WEIGHT_INFRASTRUCTURE.")
STATE_WEIGHTS = {"infrastructure": STATE_WEIGHT_INFRASTRUCTURE,
                 "food": STATE_WEIGHT_FOOD, "medical": STATE_WEIGHT_MEDICAL,
                 "luxury": STATE_WEIGHT_LUXURY, "spectacle": STATE_WEIGHT_SPECTACLE,
                 "inexplicable": STATE_WEIGHT_INEXPLICABLE,
                 "status_threatening": STATE_WEIGHT_STATUS_THREATENING,
                 "weapon_democratising": STATE_WEIGHT_WEAPON_DEMOCRATISING}
