"""Complaint 649: the home state sees the playing household seats of its own country, never a seat that lives under another
state; a seat with no country is the game's own country. The rule is called on a stand-in game that holds only what it reads."""
QUICK_TOPIC = True

import contextlib
from types import SimpleNamespace

from .harness import check

from sim.engine.agents_port_budget import BudgetView

HOME = "home"
SEAT_INCOME = {"founder": 5.0, "native": 7.0, "stranger": 11.0, "ruler": 13.0}


class HomeView(BudgetView):
	def __init__(self, seats, playing):
		self.acting = None
		self._sim = SimpleNamespace(
			state=SimpleNamespace(seats=seats, acting_seat="founder"),
			actors=SimpleNamespace(state=SimpleNamespace(home_country=HOME), active_firms=lambda: []),
			household=None, playing_seats=lambda: playing, act_as=self._act_as, revenue=lambda: SEAT_INCOME[self.acting])

	@contextlib.contextmanager
	def _act_as(self, seat_id):
		self.acting = seat_id
		yield

	def visible_scale_of(self, actor):
		return 1.0


def seat(country, kind="household"):
	return SimpleNamespace(country=country, holds_household=kind != "country")


seats = {"founder": seat(None), "native": seat(HOME), "stranger": seat("far"), "ruler": seat("far", "country")}
view = HomeView(seats, list(seats))
incomes = sorted(income for _scale, income in view.visible_taxpayers())
check("the home state sees the seat with no country and the seat of its own country, not a stranger's or a country seat",
	  incomes == [SEAT_INCOME["founder"], SEAT_INCOME["native"]], incomes)
check("a foreign state's seats are the ones the same rule selects for that country",
	  [income for _scale, income in view.seat_taxpayers("far")] == [SEAT_INCOME["stranger"]], view.seat_taxpayers("far"))
