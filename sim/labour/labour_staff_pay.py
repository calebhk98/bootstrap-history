"""What staff are paid against the market, and how many take better offers.

Methods of Labour, written against the household actor's `employees`, so a firm or state can use them.
Deaths follow the working-age mortality rate. A person leaves for a better offer at the rate the labour
market moves workers off a lower payer (market.clearing.on_the_job_loss_share): none when paid at least
the going wage for the trade.
"""
from sim.world import demography

from .market.clearing import on_the_job_loss_share


class StaffPayMixin:

    def keeps_pay_at_market(self):
        return bool(self._world.state.founder.policy.get("keep_pay_at_market", True))

    def staff_pay(self, trade):
        """Money a year one person of `trade` on the payroll is paid: the going wage while pay is kept at
        the market, else the figure last settled (the going wage when none was)."""
        market = self.labour_market.quote_annual(trade)
        if self.keeps_pay_at_market():
            return market
        return self._world.state.household.staff_pay_held.get(trade, market)

    def note_hire_pay(self, trade, count, pay_premium=0.0):
        """Fold `count` new people hired at the going wage (plus `pay_premium`) into the trade's settled pay."""
        household = self._world.state.household
        have = self.employed(trade)
        offered = self.labour_market.quote_annual(trade) * (1.0 + pay_premium)
        held = household.staff_pay_held.get(trade, offered)
        household.staff_pay_held[trade] = (have * held + count * offered) / max(have + count, 1e-9)

    def settle_staff_pay(self):
        """Yearly: with pay kept at the market the settled figure follows it; trades no longer held are dropped."""
        household = self._world.state.household
        for trade in sorted(set(household.staff_pay_held) - set(self.employed_by_trade())):
            household.staff_pay_held.pop(trade)
        if self.keeps_pay_at_market():
            for trade in sorted(self.employed_by_trade()):
                household.staff_pay_held[trade] = self.labour_market.quote_annual(trade)

    def offer_loss_share(self, trade):
        """Yearly chance one person of `trade` takes a better offer, from the pay against the going wage."""
        return on_the_job_loss_share(self.staff_pay(trade), self.labour_market.quote_annual(trade))

    def roll_staff_year(self, rng):
        """Roll each person on the books for the year, trades sorted so draws are reproducible.
        Returns (survivors by trade, died by trade, left for better offers by trade); the roster is updated."""
        household = self._world.state.household
        death_rate = demography.BASELINE_ANNUAL_MORTALITY_RATE_WORKING_AGE
        died, left = {}, {}
        for trade in sorted(self.employed_by_trade()):
            head = int(round(self.employed(trade)))
            offer_rate = self.offer_loss_share(trade)
            for _ in range(head):
                draw = rng.random()
                if draw < death_rate:
                    died[trade] = died.get(trade, 0) + 1
                elif draw < death_rate + (1.0 - death_rate) * offer_rate:
                    left[trade] = left.get(trade, 0) + 1
            survivors = head - died.get(trade, 0) - left.get(trade, 0)
            if survivors > 0:
                self.set_employed(trade, float(survivors))
            else:
                self.set_employed(trade, 0.0)
        return died, left
