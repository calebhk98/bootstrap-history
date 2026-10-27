"""The year's money phase as the workforce sees it: the living cost billed, the standing policies on buying and freeing people, and
the fade of the pressure the household's buying puts on the people market."""
from sim.reporting.api import RecordEvent

from . import constants, rules
from .commands_hours import SettleLivingCost

ARTISAN_CEILING_FOR_AUTO_BUY = 12      # the standing policy stops buying once the workshop has this many artisans
MOST_PEOPLE_AUTO_BOUGHT_PER_YEAR = 6


class StandingBondage:

	def charge_living_cost(self, command):
		charged = rules.living_cost_charged(command.living_cost, command.dependants_beyond_means, self.seat.wages_prepaid)
		self.settle_living_cost(SettleLivingCost(charged))
		return charged

	def auto_buy_people(self, command):
		# only when the optimizer is playing: buying people in manual mode with no command and no log line would hide the acquisition
		if not self.needs.founder()["policy"].get("auto_buy_people", False):
			return
		count = rules.people_to_buy(
			self.needs.legacy_acting_household().capital, self.labour.SLAVE_BASE_PRICE, self.staff()["artisans"],
			constants.AUTO_BUY_PEOPLE_CAPITAL_FLOOR_IN_PRICES, constants.AUTO_BUY_PEOPLE_CAPITAL_PER_PERSON_IN_PRICES,
			ARTISAN_CEILING_FOR_AUTO_BUY, MOST_PEOPLE_AUTO_BOUGHT_PER_YEAR)
		if count and self.needs.running_mechanics("hosts_bought_people"):
			got = self.labour.buy_slaves(count)
			if got:
				self.needs.send(RecordEvent.of("people_bought", "bought %d people for the workshop" % got))

	def auto_manumit(self, command):
		if not self.needs.founder()["policy"].get("auto_manumit", not self.needs.automation()["manual"]) or not self.staff()["slaves"]:
			return
		if self.needs.legacy_dice().random() < constants.AUTO_MANUMIT_ANNUAL_CHANCE:
			freed = self.labour.manumit(rules.people_to_free(self.staff()["slaves"], constants.AUTO_MANUMIT_SHARE_DIVISOR))
			if freed:
				self.needs.send(RecordEvent.of("people_freed", "freed %d people" % freed))

	def fade_market_pressure(self, command):
		holdings = self.needs.legacy_state().holdings
		holdings.market_pressure = rules.market_pressure_after_a_year(
			holdings.market_pressure, constants.MARKET_PRESSURE_DECAY, constants.MARKET_PRESSURE_ANNUAL_FADE)
