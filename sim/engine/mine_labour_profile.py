"""Labour a typical working of one metal takes, output-weighted across its deposits."""

from sim.unit_conversions import KILOGRAMS_PER_TONNE
from sim.world import deposits as deposit_model


def mine_labour_hours_per_tonne(weighted_deposits, effects):
    """(build hours per tonne/year of capacity, running hours per tonne of ore) of the (deposit, weight) pairs,
    under the running techniques' effects on the works."""
    build = sum(weight * deposit_model.build_cost_labour_hours_per_tonne_year(deposit, effects)
                for deposit, weight in weighted_deposits)
    running = sum(weight * KILOGRAMS_PER_TONNE * deposit_model.extraction_cost_labour_hours_per_kg(deposit, effects)
                  for deposit, weight in weighted_deposits)
    return build, running
