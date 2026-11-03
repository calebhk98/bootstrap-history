"""The hands and hours a project can draw on this year: scholars, craftsmen, the hours of a trade, and what a
technology makes an hour worth once bought."""
from sim.constants import declare

from .labour_wage_schedule import person_year_hours
from . import trade_data
from .hands import contracted_hours_of, hands_available
from sim.workforce.api import ONCE_COMMISSION


class Hands:
    def __init__(self, world, supply, trades):
        self._world = world
        self.supply = supply
        self.trades = trades

    def effective_scholars(self):
        """You are your own natural philosopher; everyone else is hired."""
        return hands_available(self._world.workforce.scholars, self._world.standing.founder_alive, 0.0, 1.0)

    def scholar_hands_available(self):
        """Scholars you can actually put on a project this year: your staff, yourself, and a scholar for every year of
        scholar-trade hours (only the scholar trade counts, as in the pools' recount) you have bought, delivered or still on order (the one rule `_hands_with_commissioned` states)."""
        scholar = trade_data.scholar_trade()
        return self._hands_with_commissioned(self._world.workforce.scholars, lambda trade: trade == scholar)

    def wage_fallback_trade(self):
        """The trade a founder with no work sells his hours in: the scholar trade."""
        return trade_data.scholar_trade()

    def _hands_with_commissioned(self, staff, counts_trade):
        """Staff on the payroll, the founder while alive, and a person for every full year of commissioned hours in the
        trades `counts_trade` accepts. A year of a trade's time is a person of it for whether a thing that needs one may
        be attempted, and buying a job rather than a person is the point of `commission`, so a gate that read the payroll
        alone could not be unblocked by the advice to commission."""
        return hands_available(staff, self._world.standing.founder_alive,
                               contracted_hours_of(self.commissioned_hours(), counts_trade),
                               person_year_hours(self._world))

    # ---- a technology can make the SAME worker do more, without replacing them.
    # market_supply counts hours; this makes an hour of a trade worth more once bought (a flying shuttle does not
    # hire a second weaver). LABOUR_PRODUCTIVITY_SOURCES: [(node, trade, bonus)] from each node's `labour_productivity`,
    # as the mechanics module's view gives them; each bonus is a fraction of what the node's own note claims, and
    # the total is capped because small bonuses compound with the rest of the economy.
    LABOUR_PRODUCTIVITY_CAP = declare(
        "LABOUR_PRODUCTIVITY_CAP", 1.5, kind="temporary_heuristic",
        unit="dimensionless multiplier", source=None, confidence="D",
        why="However many productivity-raising technologies a run has "
            "built, no trade's hour may be worth more than half again its "
            "base value. Every other saturating multiplier in this file "
            "(labour market price_factor, literacy_factor) is capped for the "
            "same reason: an uncapped sum of small, individually-"
            "defensible bonuses is still an uncapped sum, and this "
            "compounds with hired_cap and market_supply's own "
            "institutional multipliers. The cap value itself is tuned, "
            "not derived from any real productivity ceiling.")

    def labour_productivity(self, trade):
        """How much MORE a real hour of this trade is worth this year, from
        technology that makes the worker faster rather than replacing them.

        1.0 with nothing built (an hour is an hour, exactly the old
        behaviour). Multiplies the HOURS a project can draw, in
        hours_you_can_call_on - not market_supply, and not the wage bill: the
        workforce is not bigger and is not paid differently, it simply gets
        more done. See LABOUR_PRODUCTIVITY_SOURCES for what is wired in and
        why each figure is what it is.
        """
        bonus = 0.0
        projects = self._world.projects
        for node, row_trade, add in self._world.knowledge.LABOUR_PRODUCTIVITY_SOURCES:
            if row_trade == trade and node in projects.done:
                bonus += add
        productivity = min(self.LABOUR_PRODUCTIVITY_CAP, 1.0 + bonus)
        if trade == trade_data.scholar_trade():
            productivity *= self._world.knowledge.research_productivity()
        return productivity

    def hours_you_can_call_on(self, trade):
        """Hours of this trade a project can actually draw on this year: the hours hiring can reach (market_supply)
        plus the hours already commissioned, times what technology makes an hour worth. Commissioning is a second
        channel through a subcontracting shop, bounded on its own by the trade's spare hours (commission_spare_hours),
        so the two are added; it also buys certainty, hours reserved for your work rather than competed for."""
        return ((self.supply.market_supply(trade) + self._world.workforce.contract_hours.get(trade, 0.0))
                * self.labour_productivity(trade))

    def commissioned_hours(self):
        """{trade: hours} bought from outside shops: the contracts the clearing delivered and the orders it has not yet filled."""
        workforce = self._world.workforce
        hours = dict(workforce.contract_hours)
        for trade, ordered in workforce.hours_wanted_once.get(ONCE_COMMISSION, {}).items():
            hours[trade] = hours.get(trade, 0.0) + ordered
        return hours

    def hours_reserved(self, trade):
        """Hours of this trade you have already bought from an outside shop."""
        return self.commissioned_hours().get(trade, 0.0)

    def craft_hands_available(self):
        """Craftsmen you can actually put on a job this year: your staff, yourself, and a craftsman for every year of craft
        hours you have bought (the one rule `_hands_with_commissioned` states)."""
        return self._hands_with_commissioned(self._world.workforce.artisans, self.trades.is_craft_trade)
