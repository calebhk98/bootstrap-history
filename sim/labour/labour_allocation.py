"""The society's labour need by trade and the farming technique it holds.

Farm work is hours the economy's farm producers hire in the labour core plus households' own-plot
hours; nothing here allocates workers to the farm or moves people between trades (sim/labour/market/DESIGN.md)."""
import sim.geography.api as geography
from sim.world import farming_technique
from sim.labour import labour_market
from sim.labour import trade_data
from sim.labour import workforce_carriage
from sim.labour import workforce_spinup


FARM_TRADE = workforce_spinup.FARM_TRADE


class Allocation:
    def __init__(self, world, schedule):
        self._world = world
        self.schedule = schedule
        self._need_shares_cache = None          # (techniques reached, shares) of the last answer; set by _non_farm_need_shares

    def _non_farm_need_shares(self):
        """Each non-farm trade's share of need from household demand through
        the recipe graph; with no recipe available, the current split."""
        reached = frozenset(self._world.scenario.civ["starting_techs"]) | frozenset(self._world.projects.done)
        cached = self._need_shares_cache
        if cached is None or cached[0] != reached:
            shares = workforce_spinup.need_shares_by_trade(
                labour_market.production_data(), reached, self._world.trades.techniques_available_to,
                workforce_carriage.carriage_for(reached, geography.tiles_held(self._world.scenario.civ)),
                self._world.scenario.civ)
            cached = self._need_shares_cache = (reached, shares)
        if cached[1]:
            return cached[1]
        hours = self._world.society.society_labour_hours
        rest = sum(value for trade, value in hours.items() if trade != FARM_TRADE)
        return {trade: value / rest for trade, value in hours.items()
                if trade != FARM_TRADE and rest > 0.0}

    def need_shares(self):
        """Each non-farm trade's share of the society's labour need, from the recipes and the carriage."""
        return dict(self._non_farm_need_shares())

    def unskilled_trade(self):
        """The registry's flagged fallback trade: the one anyone can take up at once."""
        return trade_data.fallback_trade_of(self._world, self.schedule.wage_schedule().training_years)

    def farming_technique(self):
        """This society's farming technique from the technologies it holds,
        each weighted by how far it has spread."""
        projects = self._world.projects
        year = self._world.game.year
        starting = set(self._world.scenario.civ.get("starting_techs", ()))
        adoption = {}
        declarations = {node_id: self._world.knowledge.mechanic(node_id, "farming_technique")
                        for node_id in self._world.knowledge.nodes_with_mechanic("farming_technique")}
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
        """Farming's share of the society's booked hours; before any are booked, of the people the labour core holds."""
        hours = self._world.society.society_labour_hours
        if hours and sum(hours.values()) > 0.0:
            return hours.get(FARM_TRADE, 0.0) / sum(hours.values())
        people = self._world.economy.agent_people_by_trade()
        return people.get(FARM_TRADE, 0.0) / max(1e-9, sum(people.values())) if people else 0.0
