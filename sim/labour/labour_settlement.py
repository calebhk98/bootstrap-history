"""Where the household lives: its base tile, the town there, and moving it.

The town's people come from the tile's share of the nation, so a smaller
nation means a smaller town and a poorer tile means a smaller town.
"""
import math

from sim.constants import declare
from sim.geography import api as geography
from sim.geography.api import Geography, settlement


class SettlementMixin:

    TOWN_MAX_SHARE_OF_TILE = declare(
        "TOWN_MAX_SHARE_OF_TILE", 0.5, kind="temporary_heuristic",
        unit="fraction of a tile's people", source=None, confidence="D",
        why="Largest share of a tile's people that can live in its one "
            "market town. Keeps the town inside the tile's headcount, and so "
            "inside the nation's; the share itself is tuned, not measured.")
    RELOCATION_KM_PER_DAY = declare(
        "RELOCATION_KM_PER_DAY", 25.0, kind="temporary_heuristic",
        unit="km per day at the baseline travel pace", source=None, confidence="D",
        why="How fast a household with its goods and staff moves overland "
            "before the civilisation's own travel tradition (base_reach) "
            "speeds it up. A walking caravan pace, not fitted to a source.")
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

    def settlement_tiles(self):
        """{tile id: people living there} for the tiles this nation holds."""
        homes = self._world.civ.get("home_regions") or []
        total = self._world.population.total
        return {tile: total * settlement.population_share(homes, tile)
                for tile in settlement.tile_ids(homes)}

    def base_tile(self):
        """The tile the household operates from."""
        chosen = getattr(self._world.state.household, "base_tile", None)
        homes = self._world.civ.get("home_regions") or []
        if chosen and chosen in settlement.tile_ids(homes):
            return chosen
        return settlement.default_base_tile(homes)

    def distance_to_tile_km(self, tile):
        return settlement.distance_km(
            self._world.civ.get("home_regions") or [], self.base_tile(), tile)

    def _nominal_town_population(self):
        """The town the reference size and civilisation scale give here,
        before the people who actually live nearby bound it."""
        homes = self._world.civ.get("home_regions") or []
        place = settlement.relative_capacity(homes, self.base_tile())
        return (self.TOWN_POPULATION_REFERENCE * place
                * (self.POP_SCALE_FLOOR_SHARE
                   + self.POP_SCALE_VARIABLE_SHARE * min(1.0, self._world.pop_scale)))

    def _town_population_at(self, tile):
        """People in `tile`'s town: the nominal town there, never more than a
        set share of the tile's own people (and so never more than the nation's)."""
        homes = self._world.civ.get("home_regions") or []
        tile_people = self._world.population.total * settlement.population_share(homes, tile)
        place = settlement.relative_capacity(homes, tile)
        nominal = (self.TOWN_POPULATION_REFERENCE * place
                   * (self.POP_SCALE_FLOOR_SHARE
                      + self.POP_SCALE_VARIABLE_SHARE * min(1.0, self._world.pop_scale)))
        return min(nominal, tile_people * self.TOWN_MAX_SHARE_OF_TILE)

    def home_town_population_estimate(self):
        """People in the base's town."""
        return self._town_population_at(self.base_tile())

    def travel_speed_km_per_day(self):
        """How fast a household with its goods and staff moves when it relocates:
        the walking pace, sped up by the civilisation's travel tradition (base_reach)."""
        return self.RELOCATION_KM_PER_DAY * (
            1.0 + Geography.REACH_SPEED_COEF * float(self._world.civ.get("base_reach", 2)))

    def held_technologies(self):
        """Technologies this actor's people can travel with: the civilisation's own and those built."""
        return frozenset(self._world.civ.get("starting_techs", ())) | frozenset(self._world.state.projects.done)

    def reachable_tiles(self, days_budget=None):
        """{tile: days} a hire can travel to the base from within `days_budget` (default
        HIRE_TRAVEL_DAYS), over the routes the held technologies open (geography's reach)."""
        days_budget = self.HIRE_TRAVEL_DAYS if days_budget is None else days_budget
        held = self.held_technologies()
        base = self.base_tile()
        key = (base, held, days_budget)
        cache = self.__dict__.setdefault("_reachable_tiles_cache", {})
        if key not in cache:
            cache.clear()
            modes = geography.usable_modes([held])
            cache[key] = geography.reach([base], modes, days_budget, held_nodes=held)
        return cache[key]

    def reach_population_estimate(self, days_budget=None):
        """People in the home territory's towns within a hire's travel budget of the base,
        the base's own town always included."""
        homes = self._world.civ.get("home_regions") or []
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

    def relocation_quote(self, tile):
        """(days, hours lost, money) to move the base to `tile`."""
        km = self.distance_to_tile_km(tile)
        days = km / self.travel_speed_km_per_day()
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
        days, hours, money = self.relocation_quote(tile)
        household = self._world.state.household
        if money > household.capital:
            return False, ("moving to %s takes about %d days and would cost %s in "
                           "wages while your household travels; you have %s."
                           % (tile, math.ceil(days), "{:,.0f}".format(money),
                              "{:,.0f}".format(household.capital)))
        household.cost_capital(money, "relocation")
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
