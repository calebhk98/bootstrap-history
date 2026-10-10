"""One-off transfers to the state: paying its debt, meeting what it owes interest groups, relief and gifts.

A work declares `mechanics.transfer` (see data/branches/MECHANICS.md) and pays when it is finished; the `pay`
command pays by hand. Both go through `pay_state`, so the state's purse, its debt and the claims it funds from
that purse are the ordinary ones: a smaller debt costs less interest, a funded claim is not raised from taxpayers.
"""
from .units_prose import money_text

# what a transfer can be sized by, besides a stated sum
SIZED_BY_DEBT = "debt"
SIZED_BY_CLAIMS = "claims"


class TransfersMixin:

    def state_debt(self):
        """What the acting seat's state owes: its purse below zero."""
        return self.state_treasury().debt()

    def state_claims(self):
        """What the state has undertaken to make good to organised interest groups this year."""
        return sum(group.record.claim for group in self.actors.of_kind("interest_group") if group.organised())

    def transfer_size(self, spec):
        """The sum a `transfer` spec asks for now: a share of the state's debt or of its claims, or a stated sum
        in labour hours priced in the society's coin."""
        sized_by = spec.get("of")
        if sized_by == SIZED_BY_DEBT:
            return spec.get("share", 1.0) * self.state_debt()
        if sized_by == SIZED_BY_CLAIMS:
            return spec.get("share", 1.0) * self.state_claims()
        return spec.get("labour_hours", 0.0) * self.labour.money_per_labour_hour()

    def pay_state_sum(self, wanted, purpose):
        """Pay the state up to `wanted` from the purse (never into debt); the sum paid."""
        paid = min(max(0.0, wanted), max(0.0, self.state.household.capital))
        if paid > 0.0:
            self.pay_state(paid, purpose)
        return paid

    def settle_with_state(self, target, amount=None):
        """(sum paid, text): pay the state `amount`, or all of what `target` names (`debt` or `claims`).
        Paying beyond the debt leaves the state a reserve, which is said."""
        sized_by = {SIZED_BY_DEBT: self.state_debt, SIZED_BY_CLAIMS: self.state_claims}.get(target)
        wanted = sized_by() if sized_by is not None else amount
        if wanted is None or wanted <= 0.0:
            return 0.0, ("the state owes nothing under %s" % target) if sized_by is not None else "name a sum or `debt`"
        paid = self.pay_state_sum(wanted, target if sized_by is not None else "gift")
        if paid <= 0.0:
            return 0.0, "you have no money to pay with"
        owed = self.state_debt()
        return paid, ("paid the state %s; it still owes %s" % (money_text(paid, self, grouped=True),
                                                               money_text(owed, self, grouped=True))
                      if owed > 0.0 else "paid the state %s; it owes nothing now" % money_text(paid, self, grouped=True))

    def carry_out_transfers(self, node_id):
        """On finishing a work that declares `transfer`, pay what it asks once and say so."""
        spec = self.mechanic(node_id, "transfer")
        if not spec:
            return
        paid = self.pay_state_sum(self.transfer_size(spec), spec.get("purpose", "transfer"))
        household = self.state.household
        household.log.append((self.state.scenario.year, "%s: paid the state %s" % (
            self.nodes[node_id]["name"], money_text(paid, self, grouped=True))))
