"""The farm's cleared ground, ladder, ceiling and technique: what the workforce sets and the demography and the actors read.

The state is the module's world state (`state.py`); the farm workforce sends the commands as it clears ground and picks the
year's technique, and the territory commands come from the held tiles (`farm_territory`)."""
from sim.demography.api import rules as demography_rules
from sim.world import agriculture as farm_rules


class FarmState:

    def farm_land(self):
        """The cleared ground the farm works: hectares and yield quality."""
        return farm_rules.Land(self.world.cleared_hectares, self.world.cleared_quality)

    def farm_technique_this_year(self):
        return self.world.technique_this_year

    def farm_ladder(self):
        return self.world.ladder

    def farm_arable_ceiling(self):
        return self.world.arable_ceiling

    def opening_farmed_hectares(self):
        return self.world.opening_farmed_hectares

    def farm_food_demand_kg(self):
        """Kilograms of grain the people would harvest by eating what they need, before the first harvest."""
        technique = self.world.technique_this_year
        return (demography_rules.adult_equivalents(self.needs.population())
                * farm_rules.annual_food_demand_kg_per_person(technique.crop))

    def set_farm_land(self, command):
        farm_rules.Land(command.hectares, command.quality)   # validates the inputs before anything is stored
        self.world.cleared_hectares = float(command.hectares)
        self.world.cleared_quality = float(command.quality)

    def set_farm_technique(self, command):
        self.world.technique_this_year = command.technique

    def set_farm_territory(self, command):
        self.world.ladder = command.ladder
        self.world.arable_ceiling = command.ceiling

    def record_opening_farm(self, command):
        self.world.opening_farmed_hectares = self.world.cleared_hectares
