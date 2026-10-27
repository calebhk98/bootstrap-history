"""One-line forwarders from the old `Sim` names of disease to the disease module, for callers not yet in a module.

The yearly population step, the fog, the colonies and the agents' budget still say `sim.epidemic_forecast()` or
`sim.regional_disease_loss(tile)`; each line goes when its last caller reads the view or sends the command itself."""
from sim.disease.api import HitSeatsWithEpidemic, RunEpidemicYear


class DiseaseForwardsMixin:

    def _disease_burden(self):
        return self.view("disease_burden")()

    def epidemic_deaths_by_tile(self):
        return self.view("epidemic_deaths_by_tile")()

    def epidemic_forecast(self, food_available_calories_per_day=None):
        return self.view("epidemic_forecast")(food_available_calories_per_day)

    def regional_disease_loss(self, tile):
        return self.view("regional_disease_loss")(tile)

    def frontier_disease_loss(self):
        return self.view("frontier_disease_loss")()

    def epidemic_year(self, food_available_calories_per_day, year):
        """(epidemic deaths by band, disease burden, endemic death rates) for the year's population step: the
        epidemics run and cut each seat's staff before the burden and the endemic rates are read. What the
        externality providers add is counted in the deaths the seats are cut by."""
        deaths = self.view("externality_deaths")(self.send(RunEpidemicYear(food_available_calories_per_day, year)), year)
        self.send(HitSeatsWithEpidemic(deaths, year))
        return deaths, self.view("disease_burden")(), self.view("endemic_death_rates")()
