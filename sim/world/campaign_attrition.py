"""What wears an army down between fights: hunger, the tile's disease, and desertion when pay is owed.

Each cause is a yearly or daily hazard turned into the share of the force lost over the days it was exposed
(survival is an exponential of rate times days), so a long stay costs more than a short one and no cause can
take more than the force there is. The disease rate is the tile's own endemic loss, read by the engine from
geography and handed in; the figures below only scale it to a camp."""
from typing import Dict
import math

from sim.constants import declare
from sim.unit_conversions import CIVIL_DAYS_PER_YEAR as DAYS_PER_YEAR


STARVATION_LOSS_PER_UNFED_DAY = declare(
    "STARVATION_LOSS_PER_UNFED_DAY", 0.01, kind="temporary_heuristic", unit="share of the force a day, fully unfed",
    source=None, confidence="D",
    why="Soldiers who die, fall out or run when the ration fails, per day of a wholly unmet ration, in proportion "
        "to the share unmet. Engels (ch. 1) shows that a force cannot be carried on short rations for more than a "
        "few days but gives no loss rate; a nutrition and morale model would give one.",
    retire="Complaints/486: morale, hunger and flight of soldiers from the strata rules")

CAMP_DISEASE_MULTIPLIER = declare(
    "CAMP_DISEASE_MULTIPLIER", 30.0, kind="temporary_heuristic", unit="ratio of a camp's disease loss to the "
    "tile's endemic loss of working-age people", source=None, confidence="D",
    why="Crowded, travelling men meet more disease than the people who live on a tile and are partly immune. "
        "The tile's own working-age excess death rate is read through geography; this scales it to a camp. "
        "Contagion in crowds from the disease model would replace the factor.",
    retire="contagion in camps and armies from the disease model (sim/disease)")

DESERTION_PER_YEAR_OF_PAY_OWED = declare(
    "DESERTION_PER_YEAR_OF_PAY_OWED", 0.5, kind="temporary_heuristic",
    unit="share of the force a year per year of its pay owed", source=None, confidence="D",
    why="Soldiers owed pay leave in proportion to how much is owed. No source gives the rate; the army's loyalty "
        "and mutiny rule (group_servants.py) acts on the standing army by year, not on a force in the field.",
    retire="Complaints/486: the army as a faction with loyalty and arrears")


def lost_share(rate_per_day: float, days: float) -> float:
    """Share of a force lost to a hazard of `rate_per_day` over `days` of exposure."""
    return 1.0 - math.exp(-max(0.0, rate_per_day) * max(0.0, days))


def losses(soldiers: float, days: float, fed_share: float, disease_per_year: float,
           pay_owed_years: float) -> Dict[str, float]:
    """Soldiers lost to hunger, disease and desertion over `days`: each cause takes its share of those still there,
    one after another, so the three together never exceed the force. `disease_per_year` is the tile's endemic loss
    of working-age people; `pay_owed_years` the years of its pay the army is owed."""
    remaining = max(0.0, soldiers)
    causes = (("hunger", STARVATION_LOSS_PER_UNFED_DAY * (1.0 - max(0.0, min(1.0, fed_share)))),
              ("disease", max(0.0, disease_per_year) * CAMP_DISEASE_MULTIPLIER / DAYS_PER_YEAR),
              ("desertion", DESERTION_PER_YEAR_OF_PAY_OWED * max(0.0, pay_owed_years) / DAYS_PER_YEAR))
    result: Dict[str, float] = {}
    for cause, rate in causes:
        taken = remaining * lost_share(rate, days)
        result[cause] = taken
        remaining -= taken
    return result
