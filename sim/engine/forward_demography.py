"""One-line forwarders from the old `Sim` names of demography to the demography module, for callers not yet in a module.

The engine's mixins, the screens' hosts and the mods still say `sim.population.total`, `sim.pop_scale` or `sim.urban_fraction()`;
each line goes when its last caller reads the view (`sim.view(name)`) or sends the command (`sim.send(command)`) itself."""
from sim.demography.api import DEFAULT_POPULATION_100AD, POP_SCALE_FLOOR, RecordFoodEaten, rules


class ForwardDemographyMixin:

    # numbers other topics' code and mods still read off the game (sim/demography/constants.py declares them)
    DEFAULT_POPULATION_100AD = DEFAULT_POPULATION_100AD
    POP_SCALE_FLOOR = POP_SCALE_FLOOR

    @property
    def population(self):
        """The nation's people in three age bands, as they stand now (a reading: it changes nothing)."""
        return self.view("population")()

    @property
    def pop_scale(self):
        return self.view("pop_scale")()

    def _adult_equivalent_population(self, population):
        return rules.adult_equivalents(population)

    def people_by_tile(self):
        return self.view("people_by_tile")()

    def urban_fraction(self):
        return self.view("urban_fraction")()

    @property
    def _last_demographic_step(self):
        return self.view("demographic_flows")()

    @property
    def farm_stock_kg(self):
        return self.view("farm_holdings")()["stock_kg"]

    def record_food_eaten(self, outcome):
        """Keep the year's national food eaten over need from the economy's outcome, for the next demographic step."""
        accounts = getattr(outcome, "accounts", None)
        if accounts is None:
            return self.send(RecordFoodEaten(None, {}))
        return self.send(RecordFoodEaten(rules.national_eaten_over_need(accounts), rules.eaten_over_need_by_tile(accounts)))
