"""What defends a household against alarm and accusation, and the one lever against prominence.

Needs: effect_values, effect_sum, running_mechanics, revenue_estimate, standing_floor, founder, year,
danger_lines, send (RecordEvent)."""
from sim.reporting.api import RecordEvent

from . import constants, eminence_rules, rules


class Protection:

	def update_protection(self):
		"""Standing, office and money all protect: wealth buys advocates, priesthoods, magistracies and, in a society with a
		high bribability, verdicts."""
		needs = self.needs
		weights = self.world.value_weights
		protection = 0.0
		for _node_id, patron_protection in needs.effect_values("patron_protection"):
			protection += patron_protection * weights["patronage_weight"]
		# an armourer is protected differently from a philosopher, and only when somebody wants what he makes: gated on having
		# a patron at all
		if needs.running_mechanics("patron"):
			protection += constants.MILITARY_USEFULNESS_PROTECTION * weights["patronage_weight"] * self.military_leverage()
		works_protection = needs.effect_sum("protection", protection)
		# both a burden and a shield: once the household is large enough for the state to press a civic office on it, the
		# office costs money every year and is itself standing
		pressed_office = self.state_notice() > constants.STATE_NOTICE_THRESHOLD
		income = max(1.0, needs.revenue_estimate())
		self.seat.protection = rules.protection_total(works_protection, pressed_office, self.seat.reputation,
		                                              self.seat.bribes_ytd, income, weights["bribability"])
		self.bump("standing")

	def withdraw_from_public_life(self):
		"""Deliberately become a smaller man: the one lever against prominence. The price is reputation, which sets credit,
		protection, wages and the pace of projects; what was built stays, the floor under reputation. Answers (done, text)."""
		seat = self.seat
		floor = self.needs.standing_floor()
		danger = self.needs.danger_lines()["eminence"]
		refusal = eminence_rules.withdrawal_refusal(
			self.needs.founder()["alive"], seat.last_withdrawal, self.needs.year(), constants.WITHDRAW_EVERY, seat.eminence, danger,
			constants.WITHDRAW_MIN_EMINENCE_FRACTION, seat.reputation, floor)
		if refusal == eminence_rules.WITHDRAW_DEAD:
			return False, "there is nobody left to withdraw"
		if refusal == eminence_rules.WITHDRAW_TOO_SOON:
			last = seat.last_withdrawal
			return False, ("you stepped back in %d; doing it again so soon is not retirement, it is a performance, and nobody "
			               "would believe it. You could again in %d" % (last, last + constants.WITHDRAW_EVERY))
		# do not let them pay for nothing: work out whether it would buy anything before taking anything
		if refusal == eminence_rules.WITHDRAW_UNNOTICED:
			return False, ("nobody is watching you closely enough for this to buy anything: prominence is %.1f against a danger "
			               "line of %.0f. Withdrawing now would only cost you the standing that gets your work funded. Nothing "
			               "was changed." % (seat.eminence, danger))
		if refusal == eminence_rules.WITHDRAW_ALREADY_OBSCURE:
			return False, ("you are already as obscure as a man who has built what you have built can be. What is left of your "
			               "standing is the work itself, and that does not go away. Nothing was changed.")
		seat.last_withdrawal = self.needs.year()
		rep_before, em_before = seat.reputation, seat.eminence
		# halfway to the floor, not to zero: the work stands
		seat.reputation, seat.eminence = eminence_rules.after_withdrawal(
			seat.reputation, seat.eminence, floor, constants.WITHDRAW_REPUTATION_RETENTION, constants.WITHDRAW_EMINENCE_RETENTION)
		self.update_protection()
		message = ("you withdraw from public life: reputation %.1f -> %.1f, eminence %.1f -> %.1f. What you built still stands, and "
		           "that is the floor under your standing (%.1f). It costs you credit, protection and cheap labour until it grows "
		           "back." % (rep_before, seat.reputation, em_before, seat.eminence, floor))
		self.needs.send(RecordEvent.of("withdrew_from_public_life", message))
		return True, message
