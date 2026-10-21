"""The engine's yearly demographic step: the farm model's year, then each region's people fed and stepped."""
from sim.world import farm_year as farm_year_model

YEARLY_RECORD_LIMIT = 300


class DemographicRecoveryMixin:

    def _demographic_recovery(self, year):
        """Advance `self.population` by one year, from a REAL harvest: the
        age-cohort model handles the population half, the agriculture model
        the food half, through this society's own farming technique.

        Food availability comes from an actual harvest: one year of
        `self._agriculture.Storage.step` (land, labour and an independent weather
        draw), whose `food_available_kcal_per_day` feeds `Population.step`
        directly - never an assumed nutrition_ratio == 1.0 computed
        straight from cohort counts, which would make "is there enough
        food" an assumption rather than a simulated fact. A bad weather
        draw (or, later, a hazard that damages farmland or labour) can
        leave `food_demand_kg` short, which lowers `nutrition_ratio` below
        1.0, which raises mortality and lowers fertility through
        `Population.step`'s own, already-existing machinery - no separate
        "famine" code path, exactly as self._demography.py's own module
        docstring requires (CLAUDE.md SS3.1).

        THE GRANARY CARRIES OVER BETWEEN YEARS (Complaints/44-no-granary-
        so-the-baseline-collapses.md). This matters more than it looks:
        mortality and fertility both floor at nutrition_ratio == 1.0
        (self._demography.py's own `NUTRITION_YEAR_TO_YEAR_NOISE_STD` declaration
        names the failure mode - Jensen's inequality on a one-sided
        response curve), so a good year's excess calories buy nothing while
        a bad year's shortfall costs real people in full. Averaging weather
        that is symmetric around 1.0 over a population that responds
        asymmetrically to it manufactures a ONE-DIRECTIONAL decline with no
        scripted cause, unless a granary lets a population bank a good
        year's surplus against a future bad one (see `self._agriculture.Storage`'s
        own class docstring). This engine's own per-year weather draw
        (`_farm_year_weather_seed`) produces exactly this year-to-year swing
        independently of self._demography.py's `jitter` flag (which this engine
        never sets), so the granary is not optional insurance against a
        feature this engine has turned off: real agrarian societies damp
        exactly this with grain storage, and this wiring has it.

        `self.farm_stock_kg` (`SAVE_FIELDS`, sim/engine/saveload.py)
        is the persisted state: each year's `Storage` is constructed at
        THAT stock, not zero, and whatever it holds after this year's
        sowing/harvest/consumption/spoilage/reseeding is written back to it
        - capped at `self._agriculture.granary_capacity_kg` (see that function
        and GRANARY_CAPACITY_YEARS_OF_DEMAND's own declaration in
        self._agriculture.py for the physical basis of the cap: a granary is a
        built structure with a finite floor area, not an unlimited ledger,
        and the cap is sized off documented historical grain-reserve
        targets, not off whatever makes the population curve look right -
        CLAUDE.md SS3.1). The cap is applied HERE, at the engine boundary,
        never inside `Storage.step` itself, so that class's own one-year
        conservation identity (sim/tests/test_self._agriculture.py's own check)
        is untouched: what changes is how much of one year's `stock_after_
        kg` the civilisation's actual storage infrastructure lets survive
        into next year's opening stock, not anything about how one year's
        flows balance.

        WHAT THIS DOES NOT CLAIM TO FIX (Complaints/44's follow-up: "with 0
        large events, you shouldn't have a population decline over a
        century"). self._demography.py's `_fertility_multiplier` DOES ramp
        fertility up above nutrition_ratio == 1.0 (a bounded,
        Hutterite-anchored ceiling - see its own docstring and
        FERTILITY_SURPLUS_CEILING_MULTIPLIER's declaration; checked against
        the stakeholder's own biological growth-rate ceiling in
        sim/tests/test_self._demography.py's `GrowthCeilingTests`, which measures
        ~2.1%/year under literally unlimited food against a ~9.06%/year
        ceiling). `_excess_mortality_multiplier` remains floored at 1.0 -
        no sourced biological limit on how far mortality can fall below an
        already-observed subsistence baseline was found; see that
        function's own docstring for what was checked and why it came up
        empty.

        `reserve_target_kg`, passed to `farm_storage.step` below, lets a
        population eat beyond subsistence once its granary holds more than
        its own reserve target (see that call's own comment for the
        mechanism), so nutrition_ratio CAN and DOES exceed 1.0 in a good
        year with a full granary, and the fertility ramp above is live, not
        dead code.

        Pooling weather across home regions (see `_pooled_farm_weather_
        multiplier`'s own docstring) lowers the EFFECTIVE variance a granary
        actually experiences, compared to one wide (0.20 relative stdev)
        civilisation-wide draw: a granary sits above its reserve target far
        more of the time, so "eating well" is common rather than rare. This
        is the direct mechanism by which pooled weather raises an unshocked
        century's ending population above its starting one: it is not only
        that catastrophic province-wide famines become rarer, it is also
        that a pooled empire's surplus years actually get to feed people.

        LABOUR AND LAND UNIT DECISIONS (WIRING_MILESTONE_4.md SS4.1/4.2),
        MADE HERE RATHER THAN LEFT IMPLICIT. The farm workforce is sized
        every year as `self._agriculture.farm_workers_fte_for_population` of
        THIS YEAR'S adult-equivalent population (see
        `_adult_equivalent_population` - resolves SS4.1: no separate
        dependency-ratio correction is needed at this boundary because
        that helper's numerator and denominator are already anchored to
        the same convention once an adult-equivalent count, not a flat
        headcount, is what goes in).

        THE TWO LABOUR CONVENTIONS AGRICULTURE.PY USES ARE KEPT APART.
        `gross_harvest_kg` reads `labour_hours` for two purposes:
        `_max_hectares_harvestable_by_labour` divides it by `ANNUAL_LABOUR_
        HOURS_PER_FARM_WORKER` to recover a worker count for the harvest-
        window cap, while the Cobb-Douglas labour term is calibrated against
        `REFERENCE_LABOUR_HOURS_PER_HECTARE` (hours worked per hectare, not
        hours per worker-year). Where a worker's year and the window ceiling
        differ, a single pool built to satisfy one convention misstates the
        other, so the pool is built below from hectares and the worker count
        is passed separately.

        `gross_harvest_kg`'s `worker_count` parameter decides the harvest-
        window cap directly, from the actual number this engine already
        computed (`worker_count=farm_workers_fte`), so `labour_hours` never
        needs to be back-derived from a worker count. `labour_hours` itself
        is built the OTHER function's way instead - REFERENCE_LABOUR_
        HOURS_PER_HECTARE times `hectares_worked`, the hectares this many
        workers can actually crop (capped at whatever `farm_land` physically
        holds). The two agree by construction: at the population `farm_land`
        was originally sized for, `hectares_worked == farm_land.hectares`
        exactly, reproducing `fraction_of_population_that_must_farm`'s own
        reference yield bit for bit (before weather is applied) - the
        "right-different" identity the module's own calibration function
        implies. `self._agriculture.py`'s `ANNUAL_LABOUR_HOURS_PER_FARM_WORKER`
        (1,400) still governs `hectares_cropped_per_farm_worker` internally
        (and so still decides whether the harvest window or the annual-
        hours ceiling binds); NEITHER it nor economy.py's own
        `HOURS_PER_PERSON_YEAR` (2,000) is used to build the `labour_hours`
        crossing this boundary - only a worker COUNT crosses it, and
        self._agriculture.py's own functions decide, on their own terms, how many
        hours that implies for each of the two different things it is used
        for. `farm_land` itself is NOT resized here - see its own
        construction comment in `__init__` for why fixed land, not fixed
        workforce share, is what is allowed to be a hard constraint: once
        `farm_workers_fte` implies more hectares than `farm_land` holds,
        `hectares_worked` saturates at `farm_land.hectares` and additional
        population stops buying this civilisation any more food from
        agriculture at all - a harder ceiling than ordinary diminishing
        returns would give, and an honest consequence of not (yet) modelling
        within-hectare labour intensification beyond reference technique.
        """
        adult_equivalent_population = self._adult_equivalent_population(self.population)
        farm_workers_fte = self.labour.allocate_farm_workforce(adult_equivalent_population)
        self._last_farm_workers_fte = farm_workers_fte
        # the weather is drawn once per home region and pooled (`_pooled_farm_weather_multiplier`)
        seed = self._farm_year_weather_seed(year)
        result = farm_year_model.run_farm_year(
            self.farm_land, self._farm_technique_this_year, self.farm_stock_kg, adult_equivalent_population,
            farm_workers_fte, seed, self._pooled_farm_weather_multiplier(year))
        farm_year = result.farm_year
        self.farm_stock_kg = result.stock_kg
        self.labour.apply_land_clearing()
        # Kept for tests and diagnostics only (e.g. `state`'s founder-facing
        # reply never reads this) - NOT a SAVE_FIELDS member and does not
        # need to be one: it is recomputed fresh every year from state that
        # already round-trips (self.population, self.farm_land, self.civ),
        # so a stale or missing value right after a fresh `Sim()` (before
        # this method has run once) costs nothing correctness-sensitive.
        self._last_farm_year = farm_year
        self.state.holdings.farm_last_shortfall_kg = farm_year.food_shortfall_kg
        self.state.holdings.farm_last_harvest_kg = farm_year.gross_harvest_kg
        self.state.holdings.farm_last_marginal_product = (
            farm_year.marginal_product_last_hour_kg_per_hour)
        self.labour.update_wages()

        # Same diagnostic-only status as `_last_farm_year` just above (not a
        # SAVE_FIELDS member, recomputed fresh every year) - kept so a test
        # or a future player-facing message can read THIS year's
        # nutrition_ratio without re-deriving it from the cohort counts by
        # hand a second time.
        # the nation eats what its households ate in the economy's last year; the farm model's harvest feeds
        # demography only before an economy year has closed
        # each region eats what its households ate in the economy's last year (the farm model's harvest only
        # before an economy year has closed), steps on its own, and the nation is their sum (regional_people.py)
        regions = self.regions_of_people()
        kcal_by_region = self.regional_kcal_per_day(regions, farm_year.food_available_kcal_per_day)
        self._last_demographic_step = self.step_regions_of_people(regions, kcal_by_region, year)
        flows = self._last_demographic_step
        record = self.state.population.yearly_record
        record.append({"year": year, "population": round(self.population.total, 1),
                       "births": round(flows.births), "deaths": round(flows.deaths),
                       "nutrition_ratio": round(flows.nutrition_ratio, 4)})
        del record[:-YEARLY_RECORD_LIMIT]
        self.advance_colonies(year)
        self._refresh_demographic_indexes(year)

