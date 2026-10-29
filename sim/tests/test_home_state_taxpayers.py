"""Complaint 649: the home state sees the playing household seats of its own country, never a seat that lives under another
state; a seat with no country is the game's own country. The rule is called on a stand-in game that holds only what it reads."""
QUICK_TOPIC = True

import contextlib
from types import SimpleNamespace

from .harness import check

from sim.actors.world_budget import BudgetView

from .world_stand_in import fake_needs

HOME = "home"
SEAT_INCOME = {"founder": 5.0, "native": 7.0, "stranger": 11.0, "ruler": 13.0}


class HomeView(BudgetView):
	def __init__(self, seats, playing):
		self.acting = None
		self.needs = fake_needs(
			legacy_seats=seats, acting_seat="founder", seat_list={"playing": playing}, acting_as=self._act_as,
			legacy_household_actor=lambda: None, revenue_estimate=lambda: SEAT_INCOME[self.acting])
		self.registry = SimpleNamespace(state=SimpleNamespace(home_country=HOME), active_firms=lambda: [], country_of=lambda actor: HOME, country_of_tile=lambda tile: None)

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


# firms: a firm belongs to the country its record names (none is the game's own), whatever tile it stands on
def firm(country, margin):
	return SimpleNamespace(record=SimpleNamespace(country=country, last_margin=margin, business=SimpleNamespace(plants=[])))


def country_of(actor):
	return actor.record.country or HOME


firms = [firm(None, 17.0), firm(HOME, 19.0), firm("far", 23.0)]
view.registry.active_firms = lambda: firms
view.registry.country_of = country_of
home_firm_incomes = sorted(income for _scale, income in view.firm_taxpayers(HOME))
check("the home state sees the firm with no country and the firm of its own country, not a foreign firm",
	  home_firm_incomes == [17.0, 19.0], home_firm_incomes)
check("a foreign state's firms are the ones the same rule selects for that country",
	  [income for _scale, income in view.firm_taxpayers("far")] == [23.0], view.firm_taxpayers("far"))
visible = sorted(income for _scale, income in view.visible_taxpayers())
check("the home state's visible taxpayers are its seats and its own firms only",
	  visible == sorted([SEAT_INCOME["founder"], SEAT_INCOME["native"], 17.0, 19.0]), visible)
