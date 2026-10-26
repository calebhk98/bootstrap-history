"""The seat's year of standing: the mark scandal is read against, reputation and familiarity, then protection, the state's
pressure, scandal, bribery and the two hazards that can end a run (denunciation and eminence).

The engine's `_step_reputation` runs `renew_standing` first, then the hours and spending it tallies for other owners, then
`close_standing_year`, so the order of the old single step is kept.

Needs: standing_floor, techniques_held, tree_nodes, legacy_value_weights, year, danger_lines, legacy_constant, acting_balance,
founder, automation, events_enabled, legacy_dice, patrons_lost_to_eminence, money_text, send (PayEdge, ForgetTechnique, EndRun,
RecordEvent)."""
from sim.agents.api import edges
from sim.knowledge.api import ForgetTechnique
from sim.ledger.api import PayEdge
from sim.reporting.api import RecordEvent
from sim.seats.api import EndRun
from sim.unit_conversions import PERCENT_SCALE

from . import constants, eminence_warning, rules


class Year:

	def step_begin_seat_year(self, seat_id):
		"""The phase `begin_seat_year`: where scandal stood when the player last looked. `state` prints the chance of being
		denounced from the current scandal, and scandal moves during the year, so the direction needs the year's opening mark."""
		self.seat.scandal_last_year = self.seat.scandal

	def renew_standing(self):
		"""Reputation decays toward what the household is known for, not toward zero; every year the world has known it and every
		visible thing it has done makes the next one less astonishing."""
		seat = self.seat
		needs = self.needs
		floor = needs.standing_floor()
		constant = needs.legacy_constant
		seat.reputation = rules.reputation_toward_floor(seat.reputation, floor, constant["REPUTATION_DECAY_TOWARD_FLOOR"])
		nodes = needs.tree_nodes()
		publications = sum(1 for node_id in needs.techniques_held() if set(nodes[node_id].get("traits", [])) & {"spectacle", "inexplicable"})
		seat.familiarity = rules.familiarity_after(needs.legacy_value_weights()["adaptation_rate"], publications, needs.year() - 100,
		                                           constant["FAMILIARITY_CEILING"], constant["FAMILIARITY_PUBLICATION_WEIGHT"],
		                                           constant["FAMILIARITY_TENURE_WEIGHT"])

	def close_standing_year(self):
		"""Warn of eminence, work out protection, let the state press, then scandal, bribery and the hazards of denunciation and
		prominence."""
		needs = self.needs
		seat = self.seat
		constant = needs.legacy_constant
		year = needs.year()
		weights = needs.legacy_value_weights()
		danger = needs.danger_lines()["eminence"]
		# warn before it kills: eminence can end the run outright with nothing in the log ever mentioning it beforehand
		band = eminence_warning.eminence_band_to_announce(seat.eminence, danger, seat.said_eminence)
		if band is not None:
			seat.said_eminence = band
			needs.send(RecordEvent.of("eminence_warning", "YOU ARE BECOMING CONSPICUOUS: eminence %.0f against a danger line of %.0f. "
			                          "This is the one thing no patron and no bribe protects you from, and it grows with reputation "
			                          "and visible wealth. A wide, dispersed institution is what survives you" % (seat.eminence, danger)))
		self.update_protection()
		# the state notices you, after protection so this year's patronage and office standing are what requisition bargains
		# against, and before scandal and eminence so two unrelated draws are not resolved in one breath
		self.state_pressure(year)
		self.pay_concern_levies(year)
		seat.scandal *= constant["SCANDAL_DECAY_RATE"]
		# eminence accumulates in a separate pool because bribery does not touch it: you cannot buy an emperor's judgement
		seat.eminence = seat.eminence * constant["EMINENCE_DECAY_RATE"] + self.prominence_hazard()
		# you can buy your way out of trouble, and a sane player does
		capital = needs.acting_balance()
		if (seat.scandal > constant["AUTO_BRIBE_SCANDAL_THRESHOLD"] and capital > constant["AUTO_BRIBE_CAPITAL_THRESHOLD"]
				and needs.founder()["policy"].get("auto_bribe", not needs.automation()["manual"])):
			spend = min(capital * constant["AUTO_BRIBE_CAPITAL_SHARE"], seat.scandal * constant["AUTO_BRIBE_COST_PER_SCANDAL_POINT"])
			needs.send(PayEdge(edges.EDGE_OFFICIALS, spend, "bribes"))
			seat.bribes_ytd = constant["BRIBES_YTD_DECAY"] * seat.bribes_ytd + spend
			seat.scandal -= (spend / constant["BRIBE_SCANDAL_REDUCTION_SCALE"] * weights["bribability"])
		else:
			seat.bribes_ytd *= constant["BRIBES_YTD_DECAY"]
		seat.scandal = max(0.0, seat.scandal)
		self.warn_and_roll_scandal(constant, weights)
		self.roll_eminence(constant)
		self.bump("standing")

	def warn_and_roll_scandal(self, constant, weights):
		"""Denunciation ends the run outright, so a scandal figure with no threshold, no probability and no note would not be
		legible the way eminence's own warning is: two hazards of the same shape must both be legible."""
		needs = self.needs
		seat = self.seat
		danger = needs.danger_lines()["suspicion"]
		announce, seat.said_scandal = rules.scandal_warning_band(seat.scandal, danger, seat.said_scandal)
		if announce is not None:
			needs.send(RecordEvent.of("scandal_warning", "YOU ARE BEING TALKED ABOUT: scandal %.0f against a line of %.0f. Past it "
			                          "you may be denounced, and that ends the run - about %.0f%% a year at this level. 'bribe' buys "
			                          "advocacy and piety; it falls a tenth a year on its own"
			                          % (seat.scandal, danger,
			                             PERCENT_SCALE * max(0.0, (seat.scandal - danger) / constant["SCANDAL_HAZARD_SCALE"]))))
		if needs.events_enabled() and seat.scandal > needs.danger_lines()["suspicion"]:
			probability = (seat.scandal - needs.danger_lines()["suspicion"]) / constant["SCANDAL_HAZARD_SCALE"]
			if needs.legacy_dice().random() < probability:
				needs.send(EndRun("denounced: %s" % ("as a sorcerer" if weights["w_magic_fear"] > 0.5 else "as a subversive")))

	def roll_eminence(self, constant):
		"""The eminence hazard is separate and unbribable. Its usual outcome is a bad year rather than a death: a confiscation,
		a patron destroyed in someone else's quarrel, a forced withdrawal from public life."""
		needs = self.needs
		seat = self.seat
		danger = needs.danger_lines()["eminence"]
		if not (needs.events_enabled() and seat.eminence > danger):
			return
		probability = (seat.eminence - danger) / constants.EMINENCE_HAZARD_SCALE
		dice = needs.legacy_dice()
		if not dice.random() < probability:
			return
		roll = dice.random()
		if roll < constants.EMINENCE_OUTCOME_CONFISCATION_SHARE:
			# a demand the household answers like any other (comply, refuse, negotiate, conceal)
			_answer, _demanded, take = self.answer_confiscation(constant["EMINENCE_CONFISCATION_CAPITAL_LOSS"],
			                                                    "confiscation by the state")
			if take > 0.0:
				seat.reputation = max(0.0, seat.reputation - constant["EMINENCE_CONFISCATION_REPUTATION_LOSS"])
				needs.send(RecordEvent.of("prominence_confiscated", "PROMINENCE: property confiscated, %s lost, and you withdraw from "
				                          "public life for a while" % needs.money_text(take, short=True)))
			else:
				needs.send(RecordEvent.of("prominence_demand_kept", "PROMINENCE: the court demanded your property and you kept it, "
				                          "but you withdraw from public life for a while"))
			seat.eminence *= constant["EMINENCE_CONFISCATION_RETENTION"]
		elif roll < (constants.EMINENCE_OUTCOME_CONFISCATION_SHARE + constants.EMINENCE_OUTCOME_PATRON_LOST_SHARE):
			for patron in needs.patrons_lost_to_eminence():
				if patron in needs.techniques_held():
					needs.send(ForgetTechnique((patron,)))
					needs.send(RecordEvent.of("prominence_patron_destroyed", "PROMINENCE: your patron is destroyed in someone else's "
					                          "quarrel and you lose %s" % patron))
					break
			seat.eminence *= constant["EMINENCE_PATRON_LOSS_RETENTION"]
			seat.reputation = max(0.0, seat.reputation - constant["EMINENCE_PATRON_LOSS_REPUTATION_LOSS"])
		else:
			needs.send(EndRun("too eminent: brought down not for what you built but for how large you had become"))
