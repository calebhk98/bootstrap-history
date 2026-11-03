"""Moving the household's base to another tile: the quote and the move."""
import math

from sim.constants import declare
from sim.polity.api import ScaleFamiliarity, ScaleProtection
from sim.ledger.api import NoteSpend, PayEdge
from sim.workforce.api import ONCE_COMMISSION


class Relocation:
    def __init__(self, world, book, hours, market, pools, settlement):
        self._world = world
        self.book = book
        self.hours = hours
        self.market = market
        self.pools = pools
        self.settlement = settlement

    RELOCATION_STANDING_RETAINED = declare(
        "RELOCATION_STANDING_RETAINED", 0.3, kind="temporary_heuristic",
        unit="fraction of familiarity and protection kept", source=None,
        confidence="D",
        why="Local standing (how well the town knows you, who protects you) "
            "does not travel; this share is what a founder's name still "
            "carries in a place they have just arrived in.")

    def _relocation_wage_bill_per_year(self):
        return sum(count * self.market.unscarce_annual(trade)
                   for trade, count in self.book.employed_by_trade().items())

    def relocation_quote(self, tile):
        """(days, hours lost, money) to move the base to `tile`; None when no route joins it to the base."""
        days = self.settlement.travel_days_to_tile(tile)
        if days is None:
            return None
        year_share = min(1.0, days / 365.0)
        hours = year_share * self.hours.director_pool()
        # The whole payroll is paid while it walks, and does no other work.
        money = year_share * self._relocation_wage_bill_per_year()
        return days, hours, money

    def move_base(self, tile):
        """Move the household to another tile the nation holds."""
        tile = str(tile or "").strip()
        people = self.settlement.settlement_tiles()
        if tile not in people:
            return False, ("%r is not a tile your nation holds. "
                           'Type {"cmd":"move_base"} to list them.' % tile)
        if tile == self.settlement.base_tile():
            return False, "you are already based at %s. Nothing was changed." % tile
        if people[tile] < 1.0:
            return False, "nobody lives at %s: no cultivable land feeds anyone there." % tile
        quote = self.relocation_quote(tile)
        if quote is None:
            return False, "no route over the ways your people can travel joins %s to your base." % tile
        days, hours, money = quote
        workforce = self._world.workforce
        balance = self._world.finance.balance
        if money > balance:
            return False, ("moving to %s takes about %d days and would cost %s in "
                           "wages while your household travels; you have %s."
                           % (tile, math.ceil(days), self._world.money_text(money, grouped=True),
                              self._world.money_text(balance, grouped=True)))
        self._world.send(PayEdge(self._world.EDGE_WORKERS, money, "relocation"))
        self._world.send(NoteSpend(money))
        workforce.relocation_hours_this_year = (
            (workforce.relocation_hours_this_year or 0.0) + hours)
        # Local contracts and the local market's memory stay behind.
        workforce.commissioned = {}
        workforce.contract_hours = {}
        workforce.hours_wanted_once.pop(ONCE_COMMISSION, None)
        self._world.send(ScaleFamiliarity(self.RELOCATION_STANDING_RETAINED))
        self._world.send(ScaleProtection(self.RELOCATION_STANDING_RETAINED))
        workforce.base_tile = tile
        self.pools.resync_pools()
        return True, ("moved to %s after about %d days on the road: %s in wages "
                      "paid, %d hours of your year gone, local contracts "
                      "dropped and local standing mostly left behind. The town "
                      "there holds about %s people."
                      % (tile, math.ceil(days), self._world.money_text(money, grouped=True), round(hours),
                         self._world.plain_number(self.settlement.home_town_population_estimate())))
