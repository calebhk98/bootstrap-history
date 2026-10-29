"""Once a year the state notices what a household has become, and acts on it: a requisition and a pressed office, a demand for
military supply, and the tail risk of outright confiscation. The reports it acts on are in notice.py.

Needs: revenue_estimate, civilisation, events_enabled, game_random, money_text, send (RecordEvent)."""
from sim.reporting.api import RecordEvent

from . import constants


class Pressure:

	def state_pressure(self, year):
		needs = self.needs
		seat = self.seat
		money_text = needs.money_text
		self.settle_household_year()
		notice = self.state_notice()
		revenue = max(0.0, needs.revenue_estimate())
		state_pressure_cfg = needs.civilisation().get("state_pressure") or {}

		req_share, req_why = self.requisition_report()
		off_share, off_name = self.office_report()
		took = (req_share + off_share) * revenue
		if took > 0.5:
			office_paid = off_share * revenue
			answer = self.answer_state_demand(took - office_paid)
			if answer["penalty"] > 0.0:
				needs.send(RecordEvent.of("requisition_enforced", "You refused the requisition and the state enforced it: "
				                          "the demand and a penalty of %s on top" % money_text(answer["penalty"], grouped=True)))
			elif answer["withheld"] > 0.5:
				needs.send(RecordEvent.of("requisition_unenforced", "You refused the requisition and the state did not "
				                          "enforce it this year: %s withheld" % money_text(answer["withheld"], grouped=True)))
			elif answer["negotiated"]:
				needs.send(RecordEvent.of("requisition_negotiated", "You negotiated the requisition and the state took your offer: "
				                          "%s paid of %s asked%s" % (
					                          money_text(answer["paid"], grouped=True), money_text(took - office_paid, grouped=True),
					                          (", with %s of service" % money_text(answer["service"], grouped=True))
					                          if answer["service"] > 0.5 else "")))
			took = office_paid + answer["paid"]
			self.pay_state(took, {"office": office_paid, "requisition": answer["paid"] - answer["penalty"],
			                      "penalty": answer["penalty"]})
			last = seat.said_requisition
			if year - last >= 15:
				seat.said_requisition = year
				bits = ["%s takes %s this year" % (state_pressure_cfg.get("requisition_name", "the state"),
				                                   money_text(req_share * revenue, grouped=True))]
				if req_why:
					bits.append("; ".join(req_why))
				if off_share > 0.0005 and off_name:
					bits.append("%s costs %s more, and is not something you get to decline cheaply"
					            % (off_name, money_text(off_share * revenue, grouped=True)))
				needs.send(RecordEvent.of("state_noticed", "THE STATE HAS NOTICED YOU: " + "; ".join(bits)))
		elif notice > constants.STATE_NOTICE_THRESHOLD * 0.7:
			band = int(notice / max(0.01, constants.STATE_NOTICE_THRESHOLD * 0.1))
			if band > seat.said_notice_approach:
				seat.said_notice_approach = band
				needs.send(RecordEvent.of("state_notice_approaching", "this household is becoming large enough for the state to "
				                          "take an interest: notice %.2f against a line of %.2f. A patron or standing, and "
				                          "holdings that are not all in one place, are what blunt it when it arrives"
				                          % (notice, constants.STATE_NOTICE_THRESHOLD)))

		if needs.events_enabled() and self.military_demand_eligible():
			last = seat.last_military_demand
			if (year - last >= constants.MILITARY_DEMAND_COOLDOWN_YEARS
					and needs.game_random().random() < constants.MILITARY_DEMAND_ANNUAL_CHANCE):
				take = (self.state_military_ask(revenue, self.household_scale())
				        * (1.0 - constants.MILITARY_DEMAND_PROTECTION_DISCOUNT * seat.protection))
				take = max(0.0, take)
			else:
				take = 0.0
			if take > 0.0:
				seat.last_military_demand = year
				asked = take
				answered = self.answer_state_demand(asked)
				take = answered["paid"]
				self.pay_state(take, {"military supply": take - answered["penalty"], "penalty": answered["penalty"]})
				name = state_pressure_cfg.get("military_name", "the arsenal")
				if seat.demand_stance == "comply":
					said = ("%s asks for your output: %s handed over in powder, iron or finished pieces. Refusing a state that "
					        "can still fight is not free, and this was the cheaper choice (the 'answer' command changes how you "
					        "answer)" % (name, money_text(take, grouped=True)))
				elif answered["enforced"]:
					said = ("%s asked for %s of your output, you refused and it enforced: %s taken with the penalty"
					        % (name, money_text(asked, grouped=True), money_text(take, grouped=True)))
				else:
					said = ("%s asked for %s of your output, you refused and it could not enforce: nothing taken"
					        % (name, money_text(asked, grouped=True)))
				needs.send(RecordEvent.of("state_military_demand", said, asked=asked, taken=take, stance=seat.demand_stance))

		probability, conf_why = self.confiscation_risk()
		if probability > 0.0:
			band = int(probability / 0.05)
			last_band = seat.said_confiscation_band
			if band > last_band:
				seat.said_confiscation_band = band
				needs.send(RecordEvent.of("treasury_watching", "THE TREASURY IS LOOKING AT YOUR FORTUNE: a %d%% chance this year "
				                          "of outright confiscation, against a scale that only keeps climbing while this "
				                          "household grows. %s" % (round(probability * 100),
				                                                   ("Held off by: " + "; ".join(conf_why)) if conf_why else
				                                                   "Nothing you have built is holding it off yet")))
			if needs.events_enabled() and needs.game_random().random() < probability:
				answer, demanded, lost = self.answer_confiscation(constants.CONFISCATION_CAPITAL_LOSS, "confiscation by the state")
				name = state_pressure_cfg.get("confiscation_name", "confiscation")
				if lost > 0.5:
					seat.reputation = max(0.0, seat.reputation - constants.CONFISCATION_REPUTATION_LOSS)
					needs.send(RecordEvent.of("state_confiscation", "%s: the state takes what it judges a fortune too large to go "
					                          "on merely taxing - %s gone%s"
					                          % (name, money_text(lost, grouped=True),
					                             " (you negotiated it down from %s)" % money_text(demanded, grouped=True)
					                             if answer["negotiated"] else ""),
					                          demanded=demanded, lost=lost, negotiated=bool(answer["negotiated"])))
				elif answer["withheld"] > 0.5:
					needs.send(RecordEvent.of("confiscation_refused", "%s: the state demanded %s of your fortune, you refused and "
					                          "it could not enforce: nothing taken" % (name, money_text(demanded, grouped=True))))
				else:
					needs.send(RecordEvent.of("confiscation_too_large", "%s: the state demands a fortune too large to go on merely "
					                          "taxing, and finds nothing it can see to take" % name))
		else:
			seat.said_confiscation_band = -1
