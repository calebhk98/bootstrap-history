"""Yearly allocation of a society's working hours between farm work and the
rest of the economy, through sim.world.labour_market.

Sim mixin. The state is an hours-by-trade dict on the economy state, so any
actor that owns one can be stepped with the same functions.
"""
from sim.world import agriculture
from sim.world import labour_market
from sim.world import workforce_spinup

# Farm labour is the generic unskilled trade as data/production books it;
# every other trade's starting hours come from the workforce spin-up.
FARM_TRADE = workforce_spinup.FARM_TRADE

HOURS_PER_FARM_WORKER_YEAR = agriculture.ANNUAL_LABOUR_HOURS_PER_FARM_WORKER


def farm_workers_needed(baseline_fte, current_fte, shortfall_kg,
                        marginal_product_kg_per_hour, land_hectares):
    """Farm workers (full-time equivalents) the society wants next year."""
    hectares_per_worker = agriculture.hectares_cropped_per_farm_worker()
    # Workers past what the land can employ add nothing.
    land_limit_fte = land_hectares / hectares_per_worker
    if shortfall_kg <= 0.0 or marginal_product_kg_per_hour <= 0.0:
        return min(baseline_fte, land_limit_fte)
    extra_reference_hours = shortfall_kg / marginal_product_kg_per_hour
    extra_hectares = extra_reference_hours / agriculture.REFERENCE_LABOUR_HOURS_PER_HECTARE
    wanted = max(baseline_fte, current_fte) + extra_hectares / hectares_per_worker
    return min(wanted, land_limit_fte)


def starting_hours(production, reached_nodes, total_hours, farm_hours):
    """Hours by trade at the start: the farm hours the farm logic asks for,
    and the rest split by the spun-up trade shares."""
    rest_hours = total_hours - farm_hours
    shares = workforce_spinup.cached_spin_up(production, reached_nodes).shares_by_trade
    hours = {trade: rest_hours * share for trade, share in shares.items()}
    hours[FARM_TRADE] = farm_hours
    return hours


def reallocate(hours_by_trade, total_hours, farm_hours_needed):
    """One year of labour_market.Workforce.step toward the stated farm need;
    the non-farm hours keep their current split as their need."""
    current_total = sum(hours_by_trade[trade] for trade in sorted(hours_by_trade))
    scale = total_hours / current_total if current_total > 0.0 else 0.0
    workforce = labour_market.Workforce(
        {trade: hours * scale for trade, hours in hours_by_trade.items()})
    farm_hours_needed = min(farm_hours_needed, total_hours)
    rest_now = sum(hours for trade, hours in workforce.hours_by_trade.items()
                   if trade != FARM_TRADE)
    rest_needed = total_hours - farm_hours_needed
    needs = {trade: (hours / rest_now * rest_needed if rest_now > 0.0 else 0.0)
             for trade, hours in workforce.hours_by_trade.items() if trade != FARM_TRADE}
    needs[FARM_TRADE] = farm_hours_needed
    workforce.step(needs)
    return workforce.hours_by_trade


class LabourAllocationMixin:
    """Sim method that sizes this year's farm workforce."""

    def _allocate_farm_workforce(self, adult_equivalent_population):
        """Farm FTE for this year, after the labour market reacts to last
        year's harvest."""
        economy = self.state.economy
        baseline_fte = agriculture.farm_workers_fte_for_population(
            adult_equivalent_population)
        total_hours = self.population.working_age * HOURS_PER_FARM_WORKER_YEAR
        baseline_farm_hours = min(baseline_fte * HOURS_PER_FARM_WORKER_YEAR, total_hours)
        if not economy.society_labour_hours:
            economy.society_labour_hours = starting_hours(
                labour_market.production_data(), self.civ["starting_techs"],
                total_hours, baseline_farm_hours)
        last_year = self._last_farm_year
        current_fte = economy.society_labour_hours[FARM_TRADE] / HOURS_PER_FARM_WORKER_YEAR
        if last_year is None:
            need_fte = baseline_fte
        else:
            need_fte = farm_workers_needed(
                baseline_fte, current_fte, last_year.food_shortfall_kg,
                last_year.marginal_product_last_hour_kg_per_hour,
                self.farm_land.hectares)
        economy.society_labour_hours = reallocate(
            economy.society_labour_hours, total_hours,
            need_fte * HOURS_PER_FARM_WORKER_YEAR)
        return economy.society_labour_hours[FARM_TRADE] / HOURS_PER_FARM_WORKER_YEAR
