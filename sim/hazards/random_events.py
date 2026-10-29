"""The yearly chances that need no date: a patron's death, a fire, banditry; and what a catastrophe takes from capital.

Needs: year, events_enabled, ended_seats, acting_as, game_random, civilisation, running_mechanics, founder, automation,
standing, price_index, money_per_labour_hour, acting_balance, money_text."""
from typing import List

from sim.agents.api import edges
from sim.coin.api import PlunderHousehold
from sim.ledger.api import PayEdge
from sim.polity.api import RaiseScandal, ScaleProtection
from sim.reporting.api import RecordEvent

from . import constants
from .capital_loss import capital_lost
from .patron_death import patron_dies


class RandomEvents:

	def step_random_events(self, seats: List[str]) -> None:
		"""The phase `random_events`: each seat still in play meets its own patron's death, fire and banditry, on its own dice."""
		if not self.needs.events_enabled():
			return
		year = self.needs.year()
		ended = self.needs.ended_seats()
		for seat_id in [seat_id for seat_id in seats if seat_id not in ended]:
			with self.needs.acting_as(seat_id):
				self.random_events_for_seat(year)

	def random_events_for_seat(self, year: int) -> None:
		dice = self.needs.game_random()
		# a patron's death rolls once per cooldown, not every year
		last_patron_death = self.seat.last_patron_death
		if patron_dies(dice.random(), constants.PATRON_DEATH_ANNUAL_CHANCE,
		               lambda: self.needs.running_mechanics("patron_mortal"),
		               last_patron_death, year, constants.PATRON_DEATH_COOLDOWN_YEARS):
			self.patron_death(year)
		if dice.random() < constants.FIRE_ANNUAL_CHANCE:
			had = max(0.0, self.needs.acting_balance())
			self.lose_capital(constants.FIRE_CAPITAL_LOSS, "fire")
			self.needs.send(RecordEvent.of("fire", "fire in the %s: it destroyed %s"
			                               % (self.needs.civilisation().get("fire_quarter", "crowded quarter"), self.loss_words(had))))
		if dice.random() < constants.BANDITRY_ANNUAL_CHANCE:
			had = max(0.0, self.needs.acting_balance())
			self.needs.send(PlunderHousehold(constants.BANDITRY_TAKE_STRENGTH, "banditry", True))
			self.needs.send(RecordEvent.of("banditry", "banditry or a frontier war disrupts supply: it cost you %s" % self.loss_words(had)))

	def patron_death(self, year: int) -> None:
		self.seat.last_patron_death = year
		# a one-off jump is not a trend: the year's starting mark moves with the scandal
		self.needs.send(RaiseScandal(constants.PATRON_DEATH_SCANDAL))
		was = self.needs.standing()["protection"]
		self.needs.send(ScaleProtection(constants.PATRON_DEATH_PROTECTION_RETENTION))
		gift = constants.PATRON_DEATH_COURTING_GIFT_LABOUR_HOURS * self.needs.money_per_labour_hour() * self.needs.price_index()
		courted = self.needs.founder()["policy"].get("auto_court_heir", not self.needs.automation()["manual"])
		if courted:
			self.needs.send(PayEdge(edges.EDGE_OFFICIALS, gift, "courting a patron's heir"))
		protection_now = self.needs.standing()["protection"]
		if courted:
			text = ("your patron dies; auto_court_heir courts his heir afresh for %s. Protection falls from %d%% to %d%% and "
			        "scandal rises by %d" % (self.needs.money_text(gift, grouped=True), was * 100, protection_now * 100,
			                                 constants.PATRON_DEATH_SCANDAL))
		else:
			text = ("your patron dies. No money was spent because auto_court_heir is off; protection falls from %d%% to %d%% "
			        "and scandal rises by %d" % (was * 100, protection_now * 100, constants.PATRON_DEATH_SCANDAL))
		self.needs.send(RecordEvent.of("patron_dies", text + constants.PATRON_DEATH_RECOVERY_NOTE))

	def loss_words(self, had_before: float) -> str:
		"""'1,240 denarii' or 'nothing, you were holding none': every catastrophe line says what it actually cost."""
		lost = had_before - max(0.0, self.needs.acting_balance())
		if lost <= 0.5:
			return "nothing, because you were holding none"
		return self.needs.money_text(lost, grouped=True)

	def lose_capital(self, fraction: float, cause: str = "losses") -> float:
		"""Destroy a fraction of what you HAVE, never of what you owe: a fire destroys goods, and if you own nothing it
		takes nothing. It does not pay off your creditors. Answers the money destroyed."""
		lost = capital_lost(self.needs.acting_balance(), fraction)
		if lost <= 0.0:
			return 0.0
		self.needs.send(PayEdge(edges.EDGE_DESTROYED, lost, cause))
		return lost

	def lose_capital_command(self, command) -> float:
		return self.lose_capital(command.fraction, command.cause)
