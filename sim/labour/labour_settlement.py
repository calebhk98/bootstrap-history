"""Where the household lives: its base tile, the town there, and moving it.

The town's people come from the tile's share of the nation, so a smaller
nation means a smaller town and a poorer tile means a smaller town.
"""
import math

from sim.constants import declare
import sim.geography.api as geography
from sim.geography.api import settlement


class SettlementMixin:

    TOWN_MAX_SHARE_OF_TILE = declare(
        "TOWN_MAX_SHARE_OF_TILE", 0.5, kind="temporary_heuristic",
        unit="fraction of a tile's people", source=None, confidence="D",
        why="Largest share of a tile's people that can live in its one "
            "market town. Keeps the town inside the tile's headcount, and so "
            "inside the nation's; the share itself is tuned, not measured.")
    HIRE_TRAVEL_DAYS = declare(
        "HIRE_TRAVEL_DAYS", 1.0, kind="temporary_heuristic",
        unit="days of travel", source=None, confidence="D",
        why="How far a hire will travel to work for you (and goods to reach "
            "you), in days over the routes the actor's technologies open "
            "(geography's reach). Sets how many tiles' towns the labour "
            "market reaches; a day on foot or by cart stays inside the "
            "base's own tile, faster ways of travelling reach neighbours.")
    RELOCATION_STANDING_RETAINED = declare(
        "RELOCATION_STANDING_RETAINED", 0.3, kind="temporary_heuristic",
        unit="fraction of familiarity and protection kept", source=None,
        confidence="D",
        why="Local standing (how well the town knows you, who protects you) "
            "does not travel; this share is what a founder's name still "
            "carries in a place they have just arrived in.")

    def held_tiles(self):
        """The tiles this nation holds."""
        return tuple(geography.tiles_held(self._world.civ))

    def settlement_tiles(self):
        """{tile id: people living there} for the tiles this nation holds."""
        homes = self.held_tiles()
        total = self._world.population.total
        return {tile: total * settlement.population_share(homes, tile)
                for tile in settlement.tile_ids(homes)}

    def base_tile(self):
        """The tile the household operates from."""
        chosen = getattr(self._world.state.household, "base_tile", None)
        homes = self.held_tiles()
        if chosen and chosen in settlement.tile_ids(homes):
            return chosen
        return settlement.default_base_tile(homes)

    def distance_to_tile_km(self, tile):
        return settlement.distance_km(self.held_tiles(), self.base_tile(), tile)

    def _nominal_town_population(self):
        """The town the reference size and civilisation scale give here,
        before the people who actually live nearby bound it."""
        homes = self.held_tiles()
        place = settlement.relative_capacity(homes, self.base_tile())
        return (self.TOWN_POPULATION_REFERENCE * place
                * (self.POP_SCALE_FLOOR_SHARE
                   + self.POP_SCALE_VARIABLE_SHARE * min(1.0, self._world.pop_scale)))

    def _town_population_at(self, tile):
        """People in `tile`'s town: the nominal town there, never more than a
        set share of the tile's own people (and so never more than the nation's)."""
        homes = self.held_tiles()
        tile_people = self._world.population.total * settlement.population_share(homes, tile)
        place = settlement.relative_capacity(homes, tile)
        nominal = (self.TOWN_POPULATION_REFERENCE * place
                   * (self.POP_SCALE_FLOOR_SHARE
                      + self.POP_SCALE_VARIABLE_SHARE * min(1.0, self._world.pop_scale)))
        return min(nominal, tile_people * self.TOWN_MAX_SHARE_OF_TILE)

    def home_town_population_estimate(self):
        """People in the base's town."""
        return self._town_population_at(self.base_tile())

    def held_technologies(self):
        """Technologies this actor's people can travel with: the civilisation's own and those built."""
        return frozenset(self._world.held_and_running())

    def reachable_tiles(self, days_budget=None):
        """{tile: days} a hire can travel to the base from within `days_budget` (default
        HIRE_TRAVEL_DAYS), over the routes the held technologies open (geography's reach)."""
        days_budget = self.HIRE_TRAVEL_DAYS if days_budget is None else days_budget
        held = self.held_technologies()
        base = self.base_tile()
        if base is None:
            return {}
        built = self._world.state.economy.improvements
        key = (base, held, days_budget, repr(sorted((edge, sorted(ways)) for edge, ways in built.items())))
        cache = self.__dict__.setdefault("_reachable_tiles_cache", {})
        if key not in cache:
            cache.clear()
            modes = geography.usable_modes([held])
            cache[key] = geography.reach([base], modes, days_budget, built, held_nodes=held)
        return cache[key]

    def reach_population_estimate(self, days_budget=None):
        """People in the home territory's towns within a hire's travel budget of the base,
        the base's own town always included."""
        homes = self.held_tiles()
        base = self.base_tile()
        within = self.reachable_tiles(days_budget)
        return sum(self._town_population_at(tile) for tile in settlement.tile_ids(homes)
                   if tile == base or tile in within)

    def local_market_share(self):
        """How much of a full-size market the base's town offers (1.0 at the
        best tile of an undiminished nation); scales every pool that is not
        sized straight from the town's headcount."""
        full = (self.TOWN_POPULATION_REFERENCE
                * (self.POP_SCALE_FLOOR_SHARE
                   + self.POP_SCALE_VARIABLE_SHARE * min(1.0, self._world.pop_scale)))
        return self.home_town_population_estimate() / full if full > 0 else 0.0

    def _relocation_wage_bill_per_year(self):
        household = self._world.state.household
        return sum(count * self.labour_market.unscarce_annual(trade)
                   for trade, count in household.employees.items())

    def travel_days_to_tile(self, tile):
        """Days the household needs to reach `tile` by the fastest route over the modes its people hold
        (geography's route over the ways built, weighted by time); None when no route joins the tiles."""
        held = self.held_technologies()
        found = geography.route([self.base_tile()], [tile], geography.usable_modes([held]),
                                self._world.state.economy.improvements, held_nodes=held, fastest=True)
        return None if found is None else found["days"]

    def relocation_quote(self, tile):
        """(days, hours lost, money) to move the base to `tile`; None when no route joins it to the base."""
        days = self.travel_days_to_tile(tile)
        if days is None:
            return None
        year_share = min(1.0, days / 365.0)
        hours = year_share * self.director_pool()
        # The whole payroll is paid while it walks, and does no other work.
        money = year_share * self._relocation_wage_bill_per_year()
        return days, hours, money

    def move_base(self, tile):
        """Move the household to another tile the nation holds."""
        tile = str(tile or "").strip()
        people = self.settlement_tiles()
        if tile not in people:
            return False, ("%r is not a tile your nation holds. "
                           'Type {"cmd":"move_base"} to list them.' % tile)
        if tile == self.base_tile():
            return False, "you are already based at %s. Nothing was changed." % tile
        if people[tile] < 1.0:
            return False, "nobody lives at %s: no cultivable land feeds anyone there." % tile
        quote = self.relocation_quote(tile)
        if quote is None:
            return False, "no route over the ways your people can travel joins %s to your base." % tile
        days, hours, money = quote
        household = self._world.state.household
        if money > household.capital:
            return False, ("moving to %s takes about %d days and would cost %s in "
                           "wages while your household travels; you have %s."
                           % (tile, math.ceil(days), "{:,.0f}".format(money),
                              "{:,.0f}".format(household.capital)))
        self._world.pay_edge(self._world.EDGE_WORKERS, money, "relocation")
        household.total_spend += money
        household.relocation_hours_this_year = (
            (household.relocation_hours_this_year or 0.0) + hours)
        # Local contracts and the local market's memory stay behind.
        household.commissioned = {}
        household.contract_hours = {}
        self.labour_market.clear_pressure()
        household.familiarity *= self.RELOCATION_STANDING_RETAINED
        household.protection *= self.RELOCATION_STANDING_RETAINED
        household.base_tile = tile
        self._resync_pools()
        return True, ("moved to %s after about %d days on the road: %s in wages "
                      "paid, %d hours of your year gone, local contracts "
                      "dropped and local standing mostly left behind. The town "
                      "there holds about %s people."
                      % (tile, math.ceil(days), "{:,.0f}".format(money), round(hours),
                         "{:,.0f}".format(self.home_town_population_estimate())))
