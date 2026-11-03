"""The yearly demographic step: each region's people fed what their households ate, then stepped.

Food comes from the agent economy alone: the share of its need each region's households ate in the economy's last closed
year (`record_food_eaten`), the opening's full ration before one has closed. A bad harvest shows as food eaten short of need,
which lowers the nutrition ratio, which raises mortality and lowers fertility through `Population.step`: there is no
separate famine path and no farm model here."""
from sim.assembly.api import Part
from sim.land.api import AdvanceColonies

from . import rules
from .constants import YEARLY_RECORD_LIMIT


class Recovery(Part):

    def step_population(self, command):
        year = command.year
        # each region eats what its households ate in the economy's last year, steps on its own, and the nation is their sum
        regions = self.parts.regions._regions()
        kcal_by_region = self.parts.regions._regional_kcal_per_day(regions)
        self.parts.regions._last_demographic_step = self.parts.regions._step_regions(regions, kcal_by_region, year)
        record = self.world.yearly_record
        record.append(rules.yearly_record_row(year, self.parts.counts._bands().total, self.parts.regions._last_demographic_step))
        del record[:-YEARLY_RECORD_LIMIT]
        self.needs.send(AdvanceColonies(year))
        self.parts.counts._refresh_indexes(year)
