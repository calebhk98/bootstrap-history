"""What the household pays the state: one-off transfers (its debt, what it owes interest groups, relief and gifts), a state's
share of what one kind of concern earns, and what the state's patron funding gives back.

A work declares `mechanics.transfer` (see data/branches/MECHANICS.md) and pays when it is finished; the `pay` command pays by
hand. Both go through `pay_state`, so the state's purse, its debt and the claims it funds from that purse are the ordinary ones.
A node declares `mechanics.state_levy = {"share": s}`; while it is open the state is paid `s` of its revenue each year.

Needs: state_treasury, transfer_listening, legacy_household_actor, acting_balance, legacy_actor_registry, mechanic, tree,
money_text, money_per_labour_hour, running_mechanics, operating, concern_revenue, output_factor, legacy_said_once."""
from sim.agents.api import ledger
from sim.reporting.api import RecordEvent

from . import rules


class Transfers:

	def pay_state(self, amount, purpose):
		"""The household pays the state: the founder's loss is the treasury's gain."""
		with self.needs.transfer_listening():
			ledger.transfer(self.needs.legacy_household_actor(), self.needs.state_treasury(), amount, purpose)

	def state_debt(self):
		"""What the acting seat's state owes: its purse below zero."""
		return self.needs.state_treasury().debt()

	def state_claims(self):
		"""What the state has undertaken to make good to organised interest groups this year."""
		return sum(group.record.claim for group in self.needs.legacy_actor_registry().home_actors("interest_group")
		           if group.organised())

	def transfer_size(self, spec):
		"""The sum a `transfer` spec asks for now: a share of the state's debt or of its claims, or a stated sum in labour hours
		priced in the society's coin."""
		sized_by = spec.get("of")
		debt = self.state_debt() if sized_by == rules.SIZED_BY_DEBT else 0.0
		claims = self.state_claims() if sized_by == rules.SIZED_BY_CLAIMS else 0.0
		return rules.transfer_size(spec, debt, claims, self.needs.money_per_labour_hour())

	def pay_state_sum(self, wanted, purpose):
		"""Pay the state up to `wanted` from the purse (never into debt); the sum paid."""
		paid = min(max(0.0, wanted), max(0.0, self.needs.acting_balance()))
		if paid > 0.0:
			self.pay_state(paid, purpose)
		return paid

	def settle_with_state(self, target, amount=None):
		"""(sum paid, text): pay the state `amount`, or all of what `target` names (`debt` or `claims`). Paying beyond the debt
		leaves the state a reserve, which is said."""
		sized_by = {rules.SIZED_BY_DEBT: self.state_debt, rules.SIZED_BY_CLAIMS: self.state_claims}.get(target)
		wanted = sized_by() if sized_by is not None else amount
		if wanted is None or wanted <= 0.0:
			return 0.0, ("the state owes nothing under %s" % target) if sized_by is not None else "name a sum or `debt`"
		paid = self.pay_state_sum(wanted, target if sized_by is not None else "gift")
		if paid <= 0.0:
			return 0.0, "you have no money to pay with"
		owed = self.state_debt()
		money_text = self.needs.money_text
		return paid, ("paid the state %s; it still owes %s" % (money_text(paid, grouped=True), money_text(owed, grouped=True))
		              if owed > 0.0 else "paid the state %s; it owes nothing now" % money_text(paid, grouped=True))

	def carry_out_transfers(self, node_id):
		"""On finishing a work that declares `transfer`, pay what it asks once and say so."""
		spec = self.needs.mechanic["transfer"].get(node_id)
		if not spec:
			return
		paid = self.pay_state_sum(self.transfer_size(spec), spec.get("purpose", "transfer"))
		self.needs.send(RecordEvent.of("state_paid", "%s: paid the state %s"
		                               % (self.needs.tree[node_id]["name"], self.needs.money_text(paid, grouped=True)),
		                               work=node_id, paid=paid))

	# ---- the state's share of a kind of concern ----

	def concern_levy_due(self):
		"""{node id: sum the state takes from it this year} for the open concerns that declare `state_levy`."""
		needs = self.needs
		operating = needs.operating()
		rows = []
		for node_id, parameters in needs.running_mechanics("state_levy"):
			if node_id not in operating:
				continue   # a trade the society already has is not the household's concern to levy
			rows.append((node_id, parameters["share"], needs.concern_revenue[node_id] * needs.output_factor()))
		return rules.concern_levy_due(rows)

	def pay_concern_levies(self, year):
		"""Pay the state its share of each levied concern's takings; the household's loss is the treasury's gain. The log says so
		the first year only."""
		said = self.needs.legacy_said_once()
		for node_id, owed in sorted(self.concern_levy_due().items()):
			self.pay_state(owed, "levy on " + node_id)
			if "levy:" + node_id not in said:
				said.add("levy:" + node_id)
				self.needs.send(RecordEvent.of("concern_levy", "the state takes its share of %s: %s this year, and so on each year it is open"
				                               % (self.needs.tree[node_id]["name"], self.needs.money_text(owed, grouped=True))))
