"""Interest on loans: what a borrower pays goes to its lenders, each in proportion to what it has lent.

A borrower's debt is a set of loan claims in the actors' book (`sim/agents/purses.py`), so the interest is paid
straight to the claim holders. The household savers the simulation does not model one by one hold part of every
claim; what they receive reaches the strata that hold savings, in proportion to what each holds.
"""
from sim.agents.api import EDGE_SAVERS, ledger, payroll


class InterestMixin:

    def pay_interest(self, payer, owed, purpose="interest"):
        """`payer` pays `owed` of interest to its lenders; the savers' part is shared among the strata. The lenders
        that are actors enter it as income."""
        received = payer.purses.pay_interest(payer.account_id, owed)
        payer.note_outlay(purpose, sum(received.values()))
        for lender, amount in received.items():
            if lender == EDGE_SAVERS:
                continue
            party = self._lender_party(lender)
            if party is not None:
                party.note_income("interest_on_lending", amount)
        savers = received.get(EDGE_SAVERS, 0.0)
        if savers > 0.0:
            payroll.pay_savers(self.actors, self.edge(EDGE_SAVERS), savers)
        return received

    def note_lender_posting(self, account, signed, label):
        """A lender's cash moved by a loan it made or was repaid: entered in the books the lender keeps."""
        if account in self.state.seats:
            keeper = self.state.seats[account].household
        else:
            keeper = self.actors.actors.get(account)
        if keeper is not None:
            (keeper.note_income if signed > 0.0 else keeper.note_outlay)(label, abs(signed))

    def _lender_party(self, account):
        """The actor behind a lender's account, or None for an edge."""
        if account in self.state.seats:
            return self.seat_party(account)
        return self.actors.actors.get(account)
