"""The yearly demographic step: the farm model's year, then each region's people fed and stepped.

Food availability comes from an actual harvest: one year of the farm model (land, labour and a pooled weather draw), whose
calories a day feed the regions only before an economy year has closed. A bad draw leaves the food short, which lowers the
nutrition ratio, which raises mortality and lowers fertility through `Population.step`: there is no separate famine path.

The granary carries over between years, capped at the farm model's own granary capacity (Complaints/44): mortality and
fertility both floor at a nutrition ratio of one, so averaging weather that is symmetric around one over a people that
responds asymmetrically to it would manufacture a one-directional decline with no scripted cause, unless a granary banks a
good year's surplus against a bad one. The farm workforce is sized every year for this year's adult-equivalent people, the
same weighting the farm land was first sized with and the cohort model feeds on."""
from sim.land.api import AdvanceColonies
from sim.workforce.api import AllocateFarmWorkforce, ApplyLandClearing, UpdateWages
from sim.world import farm_year as farm_year_model

from . import rules
from .constants import YEARLY_RECORD_LIMIT


class Recovery:

    def step_population(self, command):
        year = command.year
        adult_equivalent_population = self._bands().adult_equivalents
        farm_workers_fte = self.needs.send(AllocateFarmWorkforce(adult_equivalent_population))
        # the weather is drawn once per home region and pooled
        seed = self.needs.weather_seed(year, None)
        seat = self.seat
        result = farm_year_model.run_farm_year(
            self.needs.farm_land(), self.needs.farm_technique_this_year(), seat.farm_stock_kg, adult_equivalent_population,
            farm_workers_fte, seed, self.needs.harvest_weather(year, None, True))
        farm_year = result.farm_year
        seat.farm_stock_kg = result.stock_kg
        self.needs.send(ApplyLandClearing())
        seat.farm_last_shortfall_kg = farm_year.food_shortfall_kg
        seat.farm_last_harvest_kg = farm_year.gross_harvest_kg
        seat.farm_last_marginal_product = farm_year.marginal_product_last_hour_kg_per_hour
        self.needs.send(UpdateWages())
        # each region eats what its households ate in the economy's last year (the farm model's harvest only before an
        # economy year has closed), steps on its own, and the nation is their sum (regions.py)
        regions = self._regions()
        kcal_by_region = self._regional_kcal_per_day(regions, farm_year.food_available_kcal_per_day)
        self._last_demographic_step = self._step_regions(regions, kcal_by_region, year)
        record = self.world.yearly_record
        record.append(rules.yearly_record_row(year, self._bands().total, self._last_demographic_step))
        del record[:-YEARLY_RECORD_LIMIT]
        self.needs.send(AdvanceColonies(year))
        self._refresh_indexes(year)
