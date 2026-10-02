"""Where the household lives: its base tile, the town there, and moving it.

The town's people come from the tile's share of the nation, so a smaller
nation means a smaller town and a poorer tile means a smaller town.
"""
import math

from sim.constants import declare
from sim.world import settlement


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
    RELOCATION_STANDING_RETAINED = declare(
        "RELOCATION_STANDING_RETAINED", 0.3, kind="temporary_heuristic",
        unit="fraction of familiarity and protection kept", source=None,
        confidence="D",
        why="Local standing (how well the town knows you, who protects you) "
            "does not travel; this share is what a founder's name still "
            "carries in a place they have just arrived in.")

    def settlement_tiles(self):
        """{tile id: people living there} for the tiles this nation holds."""
        homes = self.civ.get("home_regions") or []
        total = self.population.total
        return {tile: total * settlement.population_share(homes, tile)
                for tile in settlement.tile_ids(homes)}

    def base_tile(self):
        """The tile the household operates from."""
        chosen = getattr(self.state.household, "base_tile", None)
        homes = self.civ.get("home_regions") or []
        if chosen and chosen in settlement.tile_ids(homes):
            return chosen
        return settlement.default_base_tile(homes)

    def distance_to_tile_km(self, tile):
        return settlement.distance_km(
            self.civ.get("home_regions") or [], self.base_tile(), tile)

    def _nominal_town_population(self):
        """The town the reference size and civilisation scale give here,
        before the people who actually live nearby bound it."""
        homes = self.civ.get("home_regions") or []
        place = settlement.relative_capacity(homes, self.base_tile())
        return (self.TOWN_POPULATION_REFERENCE * place
                * (self.POP_SCALE_FLOOR_SHARE
                   + self.POP_SCALE_VARIABLE_SHARE * min(1.0, self.pop_scale)))

    def home_town_population_estimate(self):
        """People in the base's town: the nominal town, never more than a
        set share of the tile's own people (and so never more than the
        nation's)."""
        homes = self.civ.get("home_regions") or []
        tile_people = self.population.total * settlement.population_share(
            homes, self.base_tile())
        return min(self._nominal_town_population(),
                   tile_people * self.TOWN_MAX_SHARE_OF_TILE)

    def local_market_share(self):
        """How much of a full-size market the base's town offers (1.0 at the
        best tile of an undiminished nation); scales every pool that is not
        sized straight from the town's headcount."""
        full = (self.TOWN_POPULATION_REFERENCE
                * (self.POP_SCALE_FLOOR_SHARE
                   + self.POP_SCALE_VARIABLE_SHARE * min(1.0, self.pop_scale)))
        return self.home_town_population_estimate() / full if full > 0 else 0.0

    def _relocation_wage_bill_per_year(self):
        household = self.state.household
        return sum(count * self.labour_market.unscarce_annual(trade)
                   for trade, count in household.employees.items())

    def relocation_quote(self, tile):
        """(days, hours lost, money) to move the base to `tile`."""
        km = self.distance_to_tile_km(tile)
        speed = 1.0 + self.REACH_SPEED_COEF * float(self.civ.get("base_reach", 2))
        days = km / (self.RELOCATION_KM_PER_DAY * speed)
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
        household = self.state.household
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
