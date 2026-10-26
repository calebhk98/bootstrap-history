"""Eminence: the one danger no patron can protect a household from, and where it stands.

In an autocracy prominence is not only a shield, it is a target: it rises with reputation and with visible wealth, it is
multiplied by having got close to the throne, and no amount of patronage reduces it. It feeds scandal rather than killing
outright, because the usual outcome is a bad year, a confiscation or a lost patron.

Needs: danger_lines, mechanic, running, standing_floor, acting_balance, effect_factor,
year, money_per_labour_hour."""
from . import constants, eminence_rules


class Eminence:

	def priced(self, hours):
		"""A count of labour hours as money in this civilisation's coin."""
		return hours * self.needs.money_per_labour_hour()

	def prominence_hazard(self):
		"""Eminence gained in a year: reputation (squared, so the already famous dominate) and visible wealth mixed, scaled by
		the civilisation's weight, shaped by what stands between the founder and the throne, and softened by familiarity."""
		seat = self.seat
		return eminence_rules.yearly_hazard(
			seat.reputation, self.needs.acting_balance(), seat.familiarity,
			self.world.value_weights.get("w_eminence_danger", constants.EMINENCE_DANGER_WEIGHT_DEFAULT),
			constants.EMINENCE_REPUTATION_SCALE, self.priced(constants.EMINENCE_WEALTH_VISIBLE_THRESHOLD_LABOUR_HOURS),
			constants.EMINENCE_HAZARD_BASE_SCALE, constants.EMINENCE_HAZARD_REPUTATION_SHARE,
			constants.EMINENCE_HAZARD_WEALTH_SHARE, constants.EMINENCE_FAMILIARITY_RELIEF,
			lambda hazard: self.needs.effect_factor("eminence_hazard_factor", hazard))

	def eminence_report(self):
		"""Where you stand against the one danger no patron can protect you from."""
		seat = self.seat
		needs = self.needs
		danger = needs.danger_lines()["eminence"]
		yearly = self.prominence_hazard()
		settles = eminence_rules.settling_eminence(yearly, constants.EMINENCE_DECAY_RATE)
		probability = eminence_rules.chance_of_ruin(seat.eminence, danger, constants.EMINENCE_HAZARD_SCALE)
		helps = []
		for node_id in tuple(needs.mechanic["eminence_hazard_factor"]):
			spec = needs.mechanic["eminence_hazard_factor"].get(node_id)
			if needs.running[node_id] and spec.get("hint_when_running"):
				helps.append(spec["hint_when_running"])
			elif not needs.running[node_id] and spec.get("hint_when_absent"):
				helps.append(spec["hint_when_absent"])
		if needs.acting_balance() > self.priced(constants.EMINENCE_WEALTH_VISIBLE_THRESHOLD_LABOUR_HOURS):
			helps.append("visible wealth is half of what makes you a target")
		# the lever, named: this screen must not leave a player with no command in it that means "get smaller"
		last = seat.last_withdrawal
		if last is not None and needs.year() - last < constants.WITHDRAW_EVERY:
			lever_note = "you stepped back in %d; again no sooner than %d" % (last, last + constants.WITHDRAW_EVERY)
		else:
			lever_note = ("'withdraw' halves this now and gives up half the reputation you hold above what your work alone is "
			              "worth (%.1f). That is a real price - reputation is your credit, your protection, your wages and the "
			              "pace of your projects - and it is the only thing that lowers prominence the year you do it."
			              % needs.standing_floor())
		return {"now": round(seat.eminence, 2),
		        "dangerous_above": danger,
		        "settles_at_if_nothing_changes": round(settles, 1),
		        "chance_of_ruin_this_year": round(probability, 4),
		        # the ruin roll covers three outcomes, two of them survivable: break them out so nobody reads it as a chance of death
		        "if_it_lands_it_is": {
			        "property confiscated and a forced retirement": constants.EMINENCE_OUTCOME_CONFISCATION_SHARE,
			        "your patron destroyed in someone else's quarrel": constants.EMINENCE_OUTCOME_PATRON_LOST_SHARE,
			        "the end of the run": constants.EMINENCE_OUTCOME_RUN_ENDS_SHARE},
		        "chance_the_run_ENDS_this_year": round(probability * constants.EMINENCE_OUTCOME_RUN_ENDS_SHARE, 4),
		        "the_one_lever": lever_note,
		        "what_would_change_it": helps,
		        "note": "This is prominence, not scandal. It cannot be bribed away, and every defence that makes you safer from "
		                "accusation makes you larger and so raises this."}
