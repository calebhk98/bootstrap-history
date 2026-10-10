"""Food a running work hands out to the nation, which the nation's people eat on top of the harvest.

A work declares `mechanics.food_relief = {"material": m, "energy_kcal_per_kg": e}`. While it is open it hands out
the `m` it consumes each year (its `annual_consumables`, times the units run), so the calories reach the people only
as far as the work really buys and distributes grain. The people's nutrition ratio, which sets how many die and are
born (`sim/world/demography.py`), counts them with the year's food.
"""

DAYS_PER_YEAR = 365.0


class FoodReliefMixin:

    def relief_kilograms_per_year(self):
        """{node id: kilograms of food handed out a year} for the open works that declare `food_relief`."""
        handed = {}
        for node_id, spec in self._effect_terms("food_relief"):
            if not self.effect_holds(node_id, spec):
                continue
            kilograms = (self.nodes[node_id].get("annual_consumables") or {}).get(spec["material"], 0.0)
            handed[node_id] = kilograms * self.institution_units(node_id)
        return handed

    def relief_kcal_per_day(self):
        """The food energy a day, over the whole nation, that open works hand out."""
        total = 0.0
        for node_id, kilograms in self.relief_kilograms_per_year().items():
            total += kilograms * self.mechanic(node_id, "food_relief")["energy_kcal_per_kg"]
        return total / DAYS_PER_YEAR
