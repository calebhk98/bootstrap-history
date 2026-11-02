"""Buying a job rather than a person: the fee, the checks, `commission`, and the automatic commission for a
project blocked only on hands."""
from .labour_refusals import cash_in_hand_refusal, economy_lacks, economy_lacks_refusal
from .request_rules import commission_request_refusal
from .staff_moves import commission_spare_hours
from sim.workforce.api import ONCE_COMMISSION, PostHoursOnce


class Commissions:
    def __init__(self, world, hands, market, schedule, supply, trades):
        self._world = world
        self.hands = hands
        self.market = market
        self.schedule = schedule
        self.supply = supply
        self.trades = trades

    def commission_fee(self, trade, hours):
        """What a one-off job of `hours` costs at the trade's wage now; the clearing pays the wage it sets."""
        return self.market.commission_cost(trade, hours)

    def auto_commission_for_blocked(self, look=40):
        """Buy the hands for the nearest thing that is blocked ONLY on hands.

        Deliberately narrow. It looks at the front of the priority order, at
        things the goal actually needs, and only acts where craftsmen are the
        single remaining obstacle - not where money, prerequisites, the
        calendar or scholars are. Buying a year of a carpenter to raise a
        workshop is a sensible thing to do; buying labour speculatively is not,
        and this must never become a way to spend a run's savings on nothing.
        """
        # ON CREDIT IF NEED BE. This required money in hand, which is exactly
        # what a household in the hole does not have - and buying a season of
        # somebody's hands is a one-off, not a standing wage, so it is the
        # right instrument for a poor household and the wrong one to forbid
        # them. A Rome run ended at year 800 with 270 technologies, no
        # craftsmen at all and no way to get any: it could not hire (no
        # surplus), could not commission (no cash), so attrition took the last
        # of its staff and it never opened another concern. commission() does
        # its own affordability check against cash AND credit, which is the
        # check that should govern here too.
        if self._world.spending_power("buy") <= 0:
            return None
        need = getattr(self._world, "goal_closure", None)
        if need is None:
            try:
                need = self._world.goal_closure = self._world.closure(self._world.nodes, self._world.goal)
            except Exception:
                need = self._world.goal_closure = set()
        seen = 0
        done_nodes, active_nodes = self._world.projects.done, self._world.projects.active
        for node_id in self._world.order:
            if seen >= look:
                break
            if node_id in done_nodes or node_id in active_nodes or node_id not in need:
                continue
            if self._world.exclusion_reason(node_id):
                continue
            node = self._world.nodes[node_id]
            if any(prereq_id not in done_nodes for prereq_id in node["pre"]):
                continue
            seen += 1
            short = node["art"] - self.hands.craft_hands_available()
            if short <= 0 or node["sch"] > self.hands.effective_scholars():
                continue
            hours = short * self._world.HOURS_PER_PERSON_YEAR
            # The cheapest craft trade this society actually has that can
            # spare the time: a workshop needs hands, not a particular guild.
            best = None
            for trade in sorted(self._world.wages):
                if not self.trades.is_craft_trade(trade) or not self.trades.trade_available(trade):
                    continue
                spare = commission_spare_hours(self.supply.market_supply(trade), self.hands.hours_reserved(trade))
                if spare < hours:
                    continue
                if best is None or self.schedule.wage_per_hour(trade) < self.schedule.wage_per_hour(best):
                    best = trade
            if best is None:
                continue
            did_commission, _why = self.commission(best, hours)
            if did_commission:
                return (node_id, best, hours)
        return None

    def commission_check(self, trade, hours):
        """What `commission` and `quote commission` agree on before money
        moves. Returns (fee, refusal)."""
        trade = str(trade or "").strip().lower()
        known = trade in self._world.wages
        if known and economy_lacks(self._world, trade):
            return None, economy_lacks_refusal(trade)
        exists = known and hours > 0 and self.trades.trade_available(trade)
        spare = commission_spare_hours(self.supply.market_supply(trade), self.hands.hours_reserved(trade)) if exists else 0.0
        refusal = commission_request_refusal(known, trade, hours, exists, self._world.trade_notes.get(trade, ""), spare)
        if refusal:
            return None, refusal
        fee = self.commission_fee(trade, hours)
        if fee > self._world.spending_power("buy"):
            return None, cash_in_hand_refusal(self._world, 
                "%.0f hours of a %s" % (hours, trade), fee)
        return fee, None

    def commission(self, trade, hours):
        """Ask the labour core for a job, not a person: `hours` of the trade for this year only, with no standing
        obligation. They are posted with the household's places and filled at the year's clearing (sim/markets/port_staff.py),
        at the wage the clearing sets; the hours arrive as contract hours then. Answers (posted, message)."""
        trade = str(trade or "").strip().lower()
        fee, refusal = self.commission_check(trade, hours)
        if refusal:
            return False, refusal
        self._world.send(PostHoursOnce(ONCE_COMMISSION, trade, hours))
        return True, ("%.0f hours of a %s posted to the labour market: they are hired at the year's clearing at its wage "
                      "(about %s at today's)" % (hours, trade, self._world.money_text(fee)))
