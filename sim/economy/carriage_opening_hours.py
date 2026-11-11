"""The crew hours the merchants' carriage will bid in the opening year, by labour area and trade: the opening's bound on
the people seeded into the trades only carriage hires (Complaint 556).

A merchant opens carrying what its capital is worth (the same tonnes the opening fleet is sized to, carriage_fleet_book.opening_fleet)
the average haul from its home tile to the populous tiles; each tonne spends the crew hours that haul needs. The year's
real bids replace this once merchants have shipped (carriage_hours.bid_figures).
"""
from typing import Dict, List, Mapping, Sequence

from .carriage_fleet_book import FLEET_OPENING_TILES
from .carriage_hours import Crew, hires
from .setup import labour_area


def mean_hours_per_tonne(hauls: Sequence[Mapping[str, float]]) -> Dict[str, float]:
    """The crew hours of each trade a tonne needs on the average of `hauls` (one {trade: hours} per haul); none for no hauls."""
    if not hauls:
        return {}
    trades = sorted({trade for haul in hauls for trade in haul})
    return {trade: sum(haul.get(trade, 0.0) for haul in hauls) / len(hauls) for trade in trades}


def crew_hours_by_area(tonnes_by_area: Mapping[str, float],
                       hours_per_tonne_by_area: Mapping[str, Mapping[str, float]]) -> Dict[str, Dict[str, float]]:
    """{area: {trade: hours}}: the tonnes carried from each labour area times the crew hours a tonne needs there."""
    found: Dict[str, Dict[str, float]] = {}
    for area in sorted(tonnes_by_area):
        for trade, per_tonne in sorted(hours_per_tonne_by_area.get(area, {}).items()):
            hours = tonnes_by_area[area] * per_tonne
            if hours > 0.0:
                found.setdefault(area, {})[trade] = hours
    return found


def of_merchants(setup, record, carriage, tonnes_per_unit_capital: float) -> Dict[str, Dict[str, float]]:
    """The opening crew hours of every merchant's carriage by (labour area, trade), a merchant carrying its capital times
    `tonnes_per_unit_capital` tonnes and hiring where it is based. Empty where the setup's carriage hires no crew."""
    if not hires(setup) or tonnes_per_unit_capital <= 0.0:
        return {}
    crew = Crew(setup, carriage, record.carriage.area_imbalance)
    tiles = sorted(setup.opening_population_by_tile, key=lambda tile: (-setup.opening_population_by_tile[tile], tile))[:FLEET_OPENING_TILES]
    tonnes: Dict[str, float] = {}
    per_tonne_rows: Dict[str, List[Mapping[str, float]]] = {}
    for merchant in sorted(record.merchants.values(), key=lambda each: each.agent_id):
        area = labour_area(merchant.home_tile)
        hauls = [crew.hours_by_trade(merchant.home_tile, tile) for tile in tiles if tile != merchant.home_tile]
        if not hauls:
            continue
        tonnes[area] = tonnes.get(area, 0.0) + merchant.capital_base * tonnes_per_unit_capital
        mean = mean_hours_per_tonne(hauls)
        # merchants of one area share its figure: the mean of their own
        row = per_tonne_rows.setdefault(area, [])
        row.append({trade: hours for trade, hours in mean.items()})
    return crew_hours_by_area(tonnes, {area: mean_hours_per_tonne(rows) for area, rows in per_tonne_rows.items()})
