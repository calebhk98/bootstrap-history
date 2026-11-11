"""The hours a society's workers give in a year, by trade, from the labour core's people."""
from typing import Dict, Mapping, Optional


def society_hours_by_trade(people_by_trade: Optional[Mapping[str, float]], hours_per_person_year: Optional[float]) -> Dict[str, float]:
    """{trade: people * the hours a person-year counts}, every hour a trade's workers can give in a year. Empty while the
    agent economy opens (no people or no hours per person-year yet), which readers take as nothing booked."""
    if not people_by_trade or not hours_per_person_year:
        return {}
    return {trade: people * hours_per_person_year for trade, people in people_by_trade.items() if people > 0.0}
