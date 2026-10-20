"""What staff are paid against the market, and how many take better offers.

Methods of Labour, written against the household actor's `employees`, so a firm or state can use them.
Deaths follow the working-age mortality rate. A person leaves for a better offer at the rate the labour
market moves workers off a lower payer (market.clearing.on_the_job_loss_share): none when paid at least
the going wage for the trade.
"""
from sim.world import demography

from .market.clearing import on_the_job_loss_share
from .staff_pay_rules import blended_pay, pay_of, roll_trade, settled_pay


class StaffPayMixin:

    def keeps_pay_at_market(self):
        return bool(self._world.state.founder.policy.get("keep_pay_at_market", True))

    def staff_pay(self, trade):
        """Money a year one person of `trade` on the payroll is paid: the going wage while pay is kept at
        the market, else the figure last settled (the going wage when none was)."""
        return pay_of(self.labour_market.quote_annual(trade), self.keeps_pay_at_market(),
                      self._world.state.household.staff_pay_held.get(trade))

    def note_hire_pay(self, trade, count, pay_premium=0.0):
        """Fold `count` new people hired at the going wage (plus `pay_premium`) into the trade's settled pay."""
        household = self._world.state.household
        offered = self.labour_market.quote_annual(trade) * (1.0 + pay_premium)
        household.staff_pay_held[trade] = blended_pay(
            self.employed(trade), household.staff_pay_held.get(trade, offered), count, offered)

    def settle_staff_pay(self):
        """Yearly: with pay kept at the market the settled figure follows it; trades no longer held are dropped."""
        held_pay = self._world.state.household.staff_pay_held
        settled = settled_pay(held_pay, sorted(self.employed_by_trade()), self.labour_market.quote_annual,
                              self.keeps_pay_at_market())
        held_pay.clear()
        held_pay.update(settled)

    def offer_loss_share(self, trade):
        """Yearly chance one person of `trade` takes a better offer, from the pay against the going wage."""
        return on_the_job_loss_share(self.staff_pay(trade), self.labour_market.quote_annual(trade))

    def roll_staff_year(self, rng):
        """Roll each person on the books for the year, trades sorted so draws are reproducible.
        Returns (survivors by trade, died by trade, left for better offers by trade); the roster is updated."""
        death_rate = demography.BASELINE_ANNUAL_MORTALITY_RATE_WORKING_AGE
        died, left = {}, {}
        for trade in sorted(self.employed_by_trade()):
            trade_died, trade_left, survivors = roll_trade(int(round(self.employed(trade))), self.offer_loss_share(trade),
                                                           death_rate, rng.random)
            if trade_died:
                died[trade] = trade_died
            if trade_left:
                left[trade] = trade_left
            self.set_employed(trade, float(survivors) if survivors > 0 else 0.0)
        return died, left
