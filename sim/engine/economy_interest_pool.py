"""Interest on loans: what borrowers pay in a year is what lenders receive, split by what each supplied.

Every borrower (a seat, a firm, the state) adds its interest to the market's pool as it pays it. At
the next meeting the pool is shared among the sources of funds in proportion to what each supplied at the
last meeting: the state and each seat are credited, the firms are credited in proportion to their
purses, and the society's savers (households, not modelled actor by actor) are credited as a running
total on the market record. Nothing is created: what lenders receive is what borrowers paid.
"""

from sim.agents.api import edges, ledger
from .economy_capital_market import SEAT_SOURCE_PREFIX

INTEREST_PURPOSE = "interest_on_lending"


class InterestPoolMixin:

    def note_interest_paid(self, amount):
        """A borrower paid `amount` of interest: it joins the pool lenders will be paid from."""
        if amount > 0.0:
            record = self.capital_market()
            record.interest_pool += amount
            record.interest_paid_total += amount

    def pay_lenders(self):
        """Share the pool among the sources of funds by their share of the last meeting's supply; the
        amount paid out. Waits while no meeting has fixed a supply."""
        record = self.capital_market()
        if record.interest_pool <= 0.0 or record.supply <= 0.0:
            return 0.0
        pool = record.interest_pool
        record.interest_pool = 0.0
        firms = [firm for firm in self.actors.active_firms() if firm.money > 0.0]
        firm_funds = sum(firm.money for firm in firms)
        for source, funds in record.supply_by_source.items():
            share = pool * funds / record.supply
            if share <= 0.0:
                continue
            if source == "state":
                ledger.transfer(self.edge(edges.EDGE_INTEREST), self.state_treasury(), share, INTEREST_PURPOSE)
            elif source.startswith(SEAT_SOURCE_PREFIX):
                seat_household = self._seat_facades[source[len(SEAT_SOURCE_PREFIX):]]
                ledger.transfer(self.edge(edges.EDGE_INTEREST), seat_household, share, INTEREST_PURPOSE)
            elif source == "firms" and firm_funds > 0.0:
                for firm in firms:
                    ledger.transfer(self.edge(edges.EDGE_INTEREST), firm, share * firm.money / firm_funds, INTEREST_PURPOSE)
            else:
                record.interest_to_households += share
                self.pay_savers(share)
            record.interest_received_total += share
        return pool
