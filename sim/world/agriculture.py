"""The farming domain under one name: `agriculture_core` holds the constants, tables and types; the sibling modules
hold the yield, the granary and the labour demand. Every name resolves as `agriculture.<name>`."""
from .agriculture_core import *  # noqa: F401,F403
from .agriculture_yield import (  # noqa: F401
    Land, _max_hectares_harvestable_by_labour, draw_weather_multiplier, gross_harvest_kg,
    marginal_product_of_labour_kg_per_hour, max_hectares_reapable_by_crew,
)
from .agriculture_storage import (  # noqa: F401
    Storage, annual_food_demand_kg_per_person, granary_capacity_kg, stock_to_carry_forward_kg,
)
from .agriculture_labour import (  # noqa: F401
    farm_workers_fte_for_population,
    farmland_for_population,
    fraction_of_population_that_must_farm,
    hectares_cropped_per_farm_worker,
    hectares_per_worker_annual_hours_ceiling,
    hectares_per_worker_harvest_window_ceiling,
    holding_hectares_required_per_farm_worker,
)
