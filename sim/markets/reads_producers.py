"""What the agent economy answers about its producers and the people who work for them. Part of the port."""
from sim.economy import api as economy_api


class ProducerReads:

    def __init__(self, agent):
        self._agent = agent

    def capacities(self):
        """[(recipe id, capacity in runs)] of every producer; empty before the economy opens."""
        if not self._agent.opened():
            return []
        listed = economy_api.producer_list(self._agent.economy(), scoped=False)       # id order: a loaded game holds them so
        return list(zip(listed.recipe_ids, listed.capacity_runs))

    def runs_last_year(self):
        """[{tile, runs, inputs, outputs}] of each producer that ran last year."""
        economy = self._agent.economy()
        recipes = economy_api.recipes_of(economy)
        rows = []
        listed = economy_api.producer_list(economy, scoped=False)
        for recipe_id, tile, last_runs in zip(listed.recipe_ids, listed.tiles, listed.last_runs):
            recipe = recipes.get(recipe_id)
            if last_runs > 0.0 and recipe is not None:
                rows.append({"tile": tile, "runs": last_runs, "inputs": dict(recipe.inputs), "outputs": dict(recipe.outputs)})
        return rows

    def capacity_tonnes(self, material):
        """Tonnes a year the economy's producers can make of a material at full capacity; zero before the
        economy has opened."""
        if not self._agent.opened():
            return 0.0
        economy = self._agent.economy()
        units = economy_api.capacity_units_by_material(economy)       # summed in id order, kept while the producers are unchanged
        per_unit = self._agent.tonnes_per_unit(material)
        return 0.0 if per_unit is None else units.get(material, 0.0) * per_unit

    def worker_years_by_recipe(self):
        """Worker-years a year the economy's producers can put into each recipe at full capacity."""
        economy = self._agent.economy()
        years = {}
        listed = economy_api.producer_list(economy)       # a float sum: in id order, as a loaded game holds them
        for recipe_id, capacity_runs in zip(listed.recipe_ids, listed.capacity_runs):
            recipe = economy_api.recipes_of(economy).get(recipe_id)
            if recipe is not None:
                years[recipe_id] = years.get(recipe_id, 0.0) + (
                    capacity_runs * sum(recipe.labour_hours.values()) / economy_api.working_hours_per_year(economy))
        return years

    def by_good(self):
        """{good: [(tile, recipe id)]} of the economy's producers for each good their recipes put out."""
        economy = self._agent.economy()
        found = {}
        listed = economy_api.producer_list(economy)
        for recipe_id, tile in zip(listed.recipe_ids, listed.tiles):
            recipe = economy_api.recipes_of(economy).get(recipe_id)
            for good in (recipe.outputs if recipe is not None else ()):
                found.setdefault(good, []).append((tile, recipe_id))
        return found

    def output_tonnes_of(self, material):
        """{tile: tonnes of `material` the producers made there last year}, in tile order, for every tile that made anything; zero
        where the material has no mass."""
        per_unit = self._agent.tonnes_per_unit(material)
        units = economy_api.output_of(self._agent.economy(), material)
        return {tile: 0.0 if per_unit is None else made * per_unit for tile, made in units.items()}

    def people_by_trade(self):
        """The labour core's people by trade, or None before the economy has been opened."""
        if not self._agent.opened():
            return None
        return economy_api.people_by_trade(self._agent.economy())

    def people_by_tile_and_trade(self):
        """The labour core's people by tile and trade, or None before the economy has been opened."""
        if not self._agent.opened():
            return None
        return economy_api.people_by_tile_and_trade(self._agent.economy())
