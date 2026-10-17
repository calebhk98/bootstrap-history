"""Which farm hands stay on the land once the food they grow passes what the people need (Complaint 513).

A farmer keeps working while an hour of farm work is worth at least an hour of the wage elsewhere, and food
is still wanted: people eat beyond need up to the satiation level (data/world/needs.json, held equal to
agriculture.MAXIMUM_INTAKE_MULTIPLE_OF_SUBSISTENCE). Where food is cheap against the wage, or there is no
price yet, no hand stays for the surplus's sake and the farm is sized to need alone.
"""
from typing import Optional


def kept_farm_workers(current_fte: float, satiation_fte: float, land_limit_fte: float,
                      farm_hour_value_over_wage: Optional[float]) -> float:
    """Farm workers (full-time equivalents) who stay on the land beyond what need asks: today's, no more
    than feed the people to satiation and no more than the cleared land can use; none unless a farm
    hour's food, at the staple's price, is worth at least one hour of the unskilled wage."""
    if farm_hour_value_over_wage is None or farm_hour_value_over_wage < 1.0:
        return 0.0
    return max(0.0, min(current_fte, satiation_fte, land_limit_fte))
