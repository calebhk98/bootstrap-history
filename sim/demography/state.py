"""The state the demography module owns: the nation's people, and each seat's farm holding."""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class DemographyWorld:
    # the nation's three age bands (the home people the engine steps, never saved apart from these)
    pop_children: float = 0.0
    pop_working_age: float = 0.0
    pop_elderly: float = 0.0
    # the change in the nation's people over the last simulated year, as the screens report it
    population_change_last_year: Optional[float] = None
    # the nation's people-weighted food eaten over need in the economy's last closed year (food.py)
    food_eaten_over_need: Optional[float] = None
    # the same by tile, and the people by tile as [children, working_age, elderly] (regions.py)
    regional_eaten_over_need: Dict[str, float] = field(default_factory=dict)
    regions: Dict[str, List[float]] = field(default_factory=dict)
    # the share of each region's people living in town, seeded at the opening from the civilisation's typed urban share (urban.py)
    urban_share_of_people: Dict[str, float] = field(default_factory=dict)
    # one dict per simulated year: year, population, births, deaths, nutrition_ratio
    yearly_record: List[Any] = field(default_factory=list)
    # the last year the wage-cascade note was printed
    said_wage_cascade: int = -999


@dataclass
class DemographySeat:
    """A seat's farm: the land it holds, its granary and what the last farm year left (farm.py)."""
    farm_hectares: Optional[float] = None
    farm_stock_kg: float = 0.0
    farm_cleared_hectares: Optional[float] = None
    farm_last_shortfall_kg: Optional[float] = None
    # gross harvest of the last year the farm closed, in kilograms of grain (0 before the first)
    farm_last_harvest_kg: float = 0.0
    farm_last_marginal_product: Optional[float] = None
    farm_hours_needed: Optional[float] = None
