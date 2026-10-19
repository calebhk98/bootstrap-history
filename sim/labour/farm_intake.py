"""Which farm hands stay on the land once the food they grow passes what the people need (Complaint 513).

Farmers work until an hour of farm work on the land they have is worth no more than an hour of the wage elsewhere, and food
is still wanted: people eat beyond need up to the satiation level (data/world/needs.json, held equal to
agriculture.MAXIMUM_INTAKE_MULTIPLE_OF_SUBSISTENCE). Where food is cheap against the wage, or there is no
price yet, no hand stays for the surplus's sake and the farm is sized to need alone.
"""
from typing import Optional


def kept_farm_workers(current_fte: float, satiation_fte: float, land_limit_fte: float,
                      farm_hour_value_over_wage: Optional[float], labour_elasticity: float) -> float:
    """Farm workers (full-time equivalents) who stay on the land beyond what need asks. Extra hands on
    the cleared land earn a marginal product that falls as labour to the power (elasticity - 1), so hands
    are kept where a farm hour's food at the staple's price equals the unskilled wage: today's hands times
    the value-over-wage ratio to the power 1 / (1 - elasticity). A ratio below one lets hands go; at or above one
    today's hands stay (joining is the labour market's work, not this rule's); the hands that feed the
    people to satiation and the cleared land cap it. None
    (no price or wage yet) keeps none."""
    if farm_hour_value_over_wage is None or farm_hour_value_over_wage <= 0.0:
        return 0.0
    wanted = current_fte * farm_hour_value_over_wage ** (1.0 / (1.0 - labour_elasticity))
    return max(0.0, min(wanted, current_fte, satiation_fte, land_limit_fte))
