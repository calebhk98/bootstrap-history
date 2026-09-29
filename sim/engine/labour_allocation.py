"""Yearly allocation of a society's working hours between farm work and the
rest of the economy, through sim.world.labour_market.

Sim mixin. The state is an hours-by-trade dict on the economy state, so any
actor that owns one can be stepped with the same functions.
"""
from sim.world import agriculture
from sim.world import land
from sim.world import labour_market
from sim.world import workforce_spinup

# Farm labour is the generic unskilled trade as data/production books it;
# every other trade's starting hours come from the workforce spin-up.
FARM_TRADE = workforce_spinup.FARM_TRADE

HOURS_PER_FARM_WORKER_YEAR = agriculture.ANNUAL_LABOUR_HOURS_PER_FARM_WORKER

# temporary_heuristic: fixed pass count for the average-year food-balance search.
FOOD_BALANCE_ITERATIONS = 4


def farm_workers_needed(baseline_fte, current_fte, shortfall_kg,
                        marginal_product_kg_per_hour, land_hectares,
                        clearable_hectares=0.0):
    """Farm workers (full-time equivalents) the society wants next year.
    Workers past what the cleared land can crop clear more ground, up to
    what is still clearable."""
    hectares_per_worker = agriculture.hectares_cropped_per_farm_worker()
    land_limit_fte = land_hectares / hectares_per_worker
    clearing_fte = (clearable_hectares * agriculture.CLEARING_LABOUR_HOURS_PER_HECTARE
                    / HOURS_PER_FARM_WORKER_YEAR)
    land_limit_fte += clearing_fte
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

    def _clearable_hectares(self):
        """Arable ground held but not yet cleared."""
        ceiling = self._farm_arable_ceiling
        if ceiling is None:
            return 0.0
        return max(0.0, ceiling - self.farm_land.hectares)

    def _set_farm_area(self, hectares):
        """Cleared area and the quality of the best-first ground it covers."""
        quality = (land.ladder_quality(self._farm_ladder, hectares)
                   if self._farm_ladder else 1.0)
        self.farm_land = agriculture.Land(hectares, quality)
        self.state.economy.farm_cleared_hectares = hectares

    def _apply_land_clearing(self):
        """Hands beyond what the farm can crop spent the year clearing;
        the ground is ready for next year."""
        hours = getattr(self, "_clearing_hours_this_year", 0.0)
        cleared = min(hours / agriculture.CLEARING_LABOUR_HOURS_PER_HECTARE,
                      self._clearable_hectares())
        if cleared > 0.0:
            self._set_farm_area(self.farm_land.hectares + cleared)

    def _expected_year_farm_need(self, share_fte, adult_equivalent_population):
        """Farm workers that feed the population in an average-weather year
        on this land, found by repeating the labour market's shortfall
        response against the harvest model, starting from the population-
        share workforce."""
        fte = share_fte
        for _ in range(FOOD_BALANCE_ITERATIONS):
            fte = self._food_balance_step(fte, adult_equivalent_population)
        return fte

    def _food_balance_step(self, baseline_fte, adult_equivalent_population):
        hectares_per_worker = agriculture.hectares_cropped_per_farm_worker()
        hectares_worked = min(self.farm_land.hectares, baseline_fte * hectares_per_worker)
        worked_land = agriculture.Land(hectares_worked, quality=self.farm_land.quality)
        year = agriculture.Storage(stock_kg=0.0, seed=0).step(
            worked_land, hectares_worked * agriculture.REFERENCE_LABOUR_HOURS_PER_HECTARE,
            adult_equivalent_population, worker_count=baseline_fte,
            reserve_target_kg=agriculture.granary_capacity_kg(
                adult_equivalent_population * agriculture.annual_food_demand_kg_per_person()),
            weather_multiplier=1.0)
        return farm_workers_needed(
            baseline_fte, baseline_fte, year.food_shortfall_kg,
            year.marginal_product_last_hour_kg_per_hour, self.farm_land.hectares,
            self._clearable_hectares())

    def _allocate_farm_workforce(self, adult_equivalent_population):
        """Farm FTE for this year, after the labour market reacts to last
        year's harvest."""
        economy = self.state.economy
        baseline_fte = self._expected_year_farm_need(
            agriculture.farm_workers_fte_for_population(adult_equivalent_population),
            adult_equivalent_population)
        total_hours = self.population.working_age * HOURS_PER_FARM_WORKER_YEAR
        if not economy.society_labour_hours:
            # Start from the food balance for this land.
            farm_hours = min(baseline_fte * HOURS_PER_FARM_WORKER_YEAR, total_hours)
            economy.society_labour_hours = starting_hours(
                labour_market.production_data(), self.civ["starting_techs"],
                total_hours, farm_hours)
        last_shortfall_kg = economy.farm_last_shortfall_kg
        current_fte = economy.society_labour_hours[FARM_TRADE] / HOURS_PER_FARM_WORKER_YEAR
        if last_shortfall_kg is None:
            need_fte = current_fte
        else:
            need_fte = farm_workers_needed(
                baseline_fte, current_fte, last_shortfall_kg,
                economy.farm_last_marginal_product,
                self.farm_land.hectares, self._clearable_hectares())
        economy.society_labour_hours = reallocate(
            economy.society_labour_hours, total_hours,
            need_fte * HOURS_PER_FARM_WORKER_YEAR)
        farm_fte = economy.society_labour_hours[FARM_TRADE] / HOURS_PER_FARM_WORKER_YEAR
        crop_limit_fte = (self.farm_land.hectares
                          / agriculture.hectares_cropped_per_farm_worker())
        self._clearing_hours_this_year = max(0.0, farm_fte - crop_limit_fte) * HOURS_PER_FARM_WORKER_YEAR
        return farm_fte
