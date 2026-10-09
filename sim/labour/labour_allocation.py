"""Yearly split of a society's working hours between farm work and the other trades.

Labour mixin. The farm's hours follow the food balance, moving toward what the farm is needed for
at the occupational mobility rate. The other trades share the rest in proportion to the people the
labour core holds in them (agent economy on), else to the need the recipe graph puts on them.
Nothing here moves people between trades: the labour core does that (sim/labour/market/DESIGN.md).
"""
from sim.world import agriculture
from sim.world import farming_technique
from sim.world import land
from sim.labour import labour_market
from sim.labour import trade_data
from sim.labour import workforce_spinup

# Farm labour is the generic unskilled trade as data/production books it;
# every other trade's starting hours come from the workforce spin-up.
FARM_TRADE = workforce_spinup.FARM_TRADE

HOURS_PER_FARM_WORKER_YEAR = agriculture.ANNUAL_LABOUR_HOURS_PER_FARM_WORKER

# temporary_heuristic: fixed pass count for the average-year food-balance search.
FOOD_BALANCE_ITERATIONS = 6

# temporary_heuristic: years over which the workforce is kept producing enough
# beyond subsistence to refill a depleted granary reserve.
RESERVE_REBUILD_YEARS = 25.0


def net_marginal_product_kg_per_hour(gross_kg_per_hour, technique):
    """Food an extra farm hour adds once the seed its hectares need is
    taken out; at or below zero, more hands on that land cannot help.
    The harvest model's marginal product holds the land fixed; an hour that
    brings its own hectares earns the harvest per hour, which is that
    marginal product over the labour elasticity."""
    seed_kg_per_hour = (technique.crop.planting_material_kg_per_ha
                        / farming_technique.hours_per_hectare(technique))
    return gross_kg_per_hour / agriculture.LABOUR_OUTPUT_ELASTICITY - seed_kg_per_hour


def farm_workers_needed(baseline_fte, current_fte, shortfall_kg,
                        marginal_product_kg_per_hour, land_hectares,
                        clearable_hectares=0.0, surplus_kg=0.0,
                        technique=farming_technique.DEFAULT_TECHNIQUE):
    """Farm workers (full-time equivalents) the society wants next year.
    A shortfall calls for more hands, clearing more ground once the cleared
    land is fully cropped; a surplus lets hands go, one marginal hour at a
    time. Sized on the marginal product net of seed."""
    marginal_product_kg_per_hour = net_marginal_product_kg_per_hour(
        marginal_product_kg_per_hour, technique)
    hectares_per_worker = agriculture.hectares_cropped_per_farm_worker(
        technique.crop, technique.toolkit)
    land_limit_fte = land_hectares / hectares_per_worker
    clearing_fte = (clearable_hectares * agriculture.CLEARING_LABOUR_HOURS_PER_HECTARE
                    / HOURS_PER_FARM_WORKER_YEAR)
    if marginal_product_kg_per_hour > 0.0:
        land_limit_fte += clearing_fte
    hours_per_hectare = farming_technique.hours_per_hectare(technique)
    if shortfall_kg <= 0.0 and surplus_kg > 0.0 and marginal_product_kg_per_hour > 0.0:
        freed_hectares = surplus_kg / marginal_product_kg_per_hour / hours_per_hectare
        return max(0.0, min(baseline_fte, land_limit_fte) - freed_hectares / hectares_per_worker)
    if shortfall_kg <= 0.0 or marginal_product_kg_per_hour <= 0.0:
        return min(baseline_fte, land_limit_fte)
    extra_hectares = shortfall_kg / marginal_product_kg_per_hour / hours_per_hectare
    wanted = max(baseline_fte, current_fte) + extra_hectares / hectares_per_worker
    return min(wanted, land_limit_fte)


def hours_needed_by_trade(need_shares, total_hours, farm_hours_needed):
    """Hours each trade is needed for: the farm need, and the rest of the
    society's hours split by each trade's share of non-farm need."""
    farm_hours_needed = min(farm_hours_needed, total_hours)
    rest_hours = total_hours - farm_hours_needed
    needed = {trade: share * rest_hours for trade, share in need_shares.items()}
    needed[FARM_TRADE] = farm_hours_needed
    return needed


def society_hours(total_hours, farm_hours, shares):
    """The society's hours by trade: the farm's, and the rest shared by `shares` of non-farm work."""
    farm_hours = min(max(farm_hours, 0.0), total_hours)
    rest_hours = total_hours - farm_hours
    hours = {trade: rest_hours * share for trade, share in sorted(shares.items())}
    hours[FARM_TRADE] = farm_hours
    return hours


def farm_hours_after(current_hours, needed_hours, total_hours):
    """Farm hours a year on: toward what the farm is needed for, no faster than the occupational
    mobility rate (larger gaps move faster, up to its ceiling) lets hours leave or join it."""
    gap = needed_hours - current_hours
    basis = max(current_hours, labour_market.WALKABLE_TRADE_SEED_SHARE_OF_ECONOMY_HOURS * total_hours)
    rate = labour_market.gap_responsive_mobility_rate(
        labour_market.OCCUPATIONAL_MOBILITY_RATE_PER_YEAR, labour_market.relative_gap_size(gap, basis))
    moved = max(-rate * basis, min(rate * basis, gap))
    return min(total_hours, max(0.0, current_hours + moved))


class LabourAllocationMixin:
    """Labour method that sizes this year's farm workforce."""

    def _non_farm_need_shares(self):
        """Each non-farm trade's share of need from household demand through
        the recipe graph; with no recipe available, the current split."""
        reached = frozenset(self._world.civ["starting_techs"]) | frozenset(self._world.state.projects.done)
        cached = getattr(self, "_need_shares_cache", None)
        if cached is None or cached[0] != reached:
            shares = workforce_spinup.need_shares_by_trade(
                labour_market.production_data(), reached, self._world.techniques_available_to)
            cached = self._need_shares_cache = (reached, shares)
        if cached[1]:
            return cached[1]
        hours = self._world.state.economy.society_labour_hours
        rest = sum(value for trade, value in hours.items() if trade != FARM_TRADE)
        return {trade: value / rest for trade, value in hours.items()
                if trade != FARM_TRADE and rest > 0.0}

    def _non_farm_shares(self):
        """Each non-farm trade's share of the hours the society gives them: the labour core's people in
        it while the agent economy runs, else the need the recipe graph puts on it."""
        people = self._world.economy.agent_people_by_trade()
        if people:
            held = {trade: count for trade, count in people.items() if trade != FARM_TRADE and count > 0.0}
            total = sum(held.values())
            if total > 0.0:
                return {trade: count / total for trade, count in held.items()}
        return self._non_farm_need_shares()

    def _hours_needed_by_trade(self, total_hours=None):
        """Hours each trade is needed for out of the society's hours (the labour allocation)."""
        economy = self._world.state.economy
        holdings = self._world.state.holdings
        hours = economy.society_labour_hours
        if total_hours is None:
            total_hours = sum(hours.values())
        farm_now = hours.get(FARM_TRADE, 0.0)
        farm_needed = farm_now if holdings.farm_hours_needed is None else holdings.farm_hours_needed
        return hours_needed_by_trade(self._non_farm_need_shares(), total_hours, farm_needed)

    def _hours_needed_for_wages(self):
        """What the wage rule weighs against the hours worked: the allocation's need, plus the people
        under arms as demand on the unskilled pool that the society's hours no longer cover."""
        needed = self._hours_needed_by_trade()
        fallback = trade_data.fallback_trade(self.wage_schedule().training_years, self._world.trade_family)
        needed[fallback] = needed.get(fallback, 0.0) + self._people_under_arms() * HOURS_PER_FARM_WORKER_YEAR
        return needed

    def _clearable_hectares(self):
        """Arable ground held but not yet cleared."""
        ceiling = self._world.farm_arable_ceiling
        if ceiling is None:
            return 0.0
        return max(0.0, ceiling - self._world.farm_land.hectares)

    def _set_farm_area(self, hectares):
        """Cleared area and the quality of the best-first ground it covers."""
        quality = (land.ladder_quality(self._world.farm_ladder, hectares)
                   if self._world.farm_ladder else 1.0)
        self._world.farm_land = agriculture.Land(hectares, quality)
        self._world.state.holdings.farm_cleared_hectares = hectares

    def _apply_land_clearing(self):
        """Hands beyond what the farm can crop spent the year clearing;
        the ground is ready for next year."""
        hours = getattr(self, "_clearing_hours_this_year", 0.0)
        cleared = min(hours / agriculture.CLEARING_LABOUR_HOURS_PER_HECTARE,
                      self._clearable_hectares())
        if cleared > 0.0:
            self._set_farm_area(self._world.farm_land.hectares + cleared)

    def _farming_technique(self):
        """This society's farming technique from the technologies it holds,
        each weighted by how far it has spread."""
        projects = self._world.state.projects
        year = self._world.state.scenario.year
        starting = set(self._world.civ.get("starting_techs", ()))
        adoption = {}
        declarations = {node_id: self._world.mechanic(node_id, "farming_technique")
                        for node_id in self._world.nodes_with_mechanic("farming_technique")}
        for node_id in declarations:
            if node_id not in projects.done:
                continue
            if node_id in projects.granted or node_id in starting:
                adoption[node_id] = 1.0
            else:
                age = year - (projects.done_year or {}).get(node_id, year)
                adoption[node_id] = farming_technique.adoption_share(age)
        return farming_technique.technique_from_adoption(adoption, declarations)

    def farm_share_of_hours(self):
        """Share of the society's working hours spent farming."""
        hours = self._world.state.economy.society_labour_hours
        if hours:
            return hours[FARM_TRADE] / sum(hours.values())
        adult_equivalent = self._world.adult_equivalent_population(self._world.population)
        technique = self._farming_technique()
        farm_fte = self._expected_year_farm_need(
            self._share_farm_fte(adult_equivalent, technique), adult_equivalent, technique)
        return min(1.0, farm_fte / max(1e-9, self._world.population.working_age))

    @staticmethod
    def _share_farm_fte(adult_equivalent_population, technique):
        """Population-share farm workforce: the search's starting guess."""
        return agriculture.farm_workers_fte_for_population(
            adult_equivalent_population, technique.crop, None,
            technique.rotation, technique.toolkit)

    def _expected_year_farm_need(self, share_fte, adult_equivalent_population, technique):
        """Farm workers that just feed the population in an average-weather
        year on this land, found by repeating the food balance (shortfall
        calls for hands, surplus frees them) from the population-share
        workforce."""
        fte = share_fte
        for _ in range(FOOD_BALANCE_ITERATIONS):
            fte = self._food_balance_step(fte, adult_equivalent_population, technique)
        return fte

    def _food_balance_step(self, baseline_fte, adult_equivalent_population, technique):
        hectares_per_worker = agriculture.hectares_cropped_per_farm_worker(
            technique.crop, technique.toolkit)
        hectares_worked = min(self._world.farm_land.hectares, baseline_fte * hectares_per_worker)
        worked_land = agriculture.Land(hectares_worked, quality=self._world.farm_land.quality)
        reserve_kg = agriculture.granary_capacity_kg(
            adult_equivalent_population
            * agriculture.annual_food_demand_kg_per_person(technique.crop))
        stock_kg = self._world.farm_stock_kg
        year = agriculture.Storage(stock_kg=stock_kg, seed=0).step(
            worked_land, hectares_worked * farming_technique.hours_per_hectare(technique),
            adult_equivalent_population, crop=technique.crop,
            rotation=technique.rotation, toolkit=technique.toolkit,
            worker_count=baseline_fte, reserve_target_kg=reserve_kg,
            weather_multiplier=1.0)
        rebuild_kg = max(0.0, reserve_kg - stock_kg) / RESERVE_REBUILD_YEARS
        balance_kg = (year.gross_harvest_kg - year.seed_sown_kg - year.spoilage_kg
                      - year.food_demand_kg - rebuild_kg)
        return farm_workers_needed(
            baseline_fte, baseline_fte, max(0.0, -balance_kg),
            year.marginal_product_last_hour_kg_per_hour, self._world.farm_land.hectares,
            self._clearable_hectares(), surplus_kg=max(0.0, balance_kg),
            technique=technique)

    def _people_under_arms(self):
        """People nationwide of trades drawn from the unskilled pool that actors hold on staff: they
        have left production and farming while they serve."""
        world = self._world
        return sum(world.actors_staff_nationwide(trade) for trade in sorted(world.wages)
                   if trade_data.drawn_from_unskilled_pool(trade))

    def _society_hours_available(self):
        """Hours the society can put into farm work and trades: the working age
        less the people standing staff hold."""
        people = max(0.0, self._world.population.working_age - self._people_under_arms())
        return people * HOURS_PER_FARM_WORKER_YEAR

    def _allocate_farm_workforce(self, adult_equivalent_population):
        """Farm FTE for this year, after the labour market reacts to last
        year's harvest."""
        economy = self._world.state.economy
        holdings = self._world.state.holdings
        technique = self._farming_technique()
        baseline_fte = self._expected_year_farm_need(
            self._share_farm_fte(adult_equivalent_population, technique),
            adult_equivalent_population, technique)
        total_hours = self._society_hours_available()
        held_hours = sum(economy.society_labour_hours.values())
        if held_hours > 0.0:
            current_farm_hours = economy.society_labour_hours[FARM_TRADE] * total_hours / held_hours
        else:
            current_farm_hours = min(baseline_fte * HOURS_PER_FARM_WORKER_YEAR, total_hours)   # the food balance
        last_shortfall_kg = holdings.farm_last_shortfall_kg
        current_fte = current_farm_hours / HOURS_PER_FARM_WORKER_YEAR
        if last_shortfall_kg is None:
            need_fte = current_fte
        else:
            need_fte = farm_workers_needed(
                baseline_fte, current_fte, last_shortfall_kg,
                holdings.farm_last_marginal_product,
                self._world.farm_land.hectares, self._clearable_hectares(),
                technique=technique)
        holdings.farm_hours_needed = need_fte * HOURS_PER_FARM_WORKER_YEAR
        economy.society_labour_hours = society_hours(
            total_hours,
            farm_hours_after(current_farm_hours, min(holdings.farm_hours_needed, total_hours), total_hours),
            self._non_farm_shares())
        farm_fte = economy.society_labour_hours[FARM_TRADE] / HOURS_PER_FARM_WORKER_YEAR
        crop_limit_fte = (self._world.farm_land.hectares / agriculture.hectares_cropped_per_farm_worker(
            technique.crop, technique.toolkit))
        self._clearing_hours_this_year = max(0.0, farm_fte - crop_limit_fte) * HOURS_PER_FARM_WORKER_YEAR
        self._world.farm_technique_this_year = technique
        return farm_fte
