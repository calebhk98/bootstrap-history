"""The polity module: a seat's standing with its society and its state, and the state's pressure on it.

A household is noticed, protected, levied and ruined by the same few things: its reputation and scandal with the people, its
eminence with the throne, its protection from patrons and money, how far the state's officials reach, and the interest groups
it has made. The module owns those figures for each seat, answers every question about them, applies every change to them, and
runs the seat's year of standing. It also holds what the state records of a country (its army's losses, its tiles' unrest, its
risings and its ruler) for the campaigns that change them, and the society's value weights' shifts."""
from sim.assembly.api import Module

from .appliers import Appliers
from .demands import Demands
from .eminence import Eminence
from .groups import Groups
from .notice import Notice
from .patronage import Patronage
from .pressure import Pressure
from .protection import Protection
from .reach import Reach
from .transfers import Transfers
from .year import Year


class Polity(Reach, Notice, Protection, Eminence, Pressure, Demands, Groups, Transfers, Patronage, Year, Appliers, Module):

	def setup(self) -> None:
		self._state_reach_memo = None     # (the key it was worked out for, the share): never saved
		self._staff_reach_memo = {}       # line name -> the same
		self._banned_materials_cache = {}

	def value_weights(self):
		"""The society's value weights, by name."""
		return self.world.value_weights

	# ---- the views of one seat's figures ----

	def standing(self):
		"""The acting seat's figures with its society and state."""
		seat = self.seat
		return {"protection": seat.protection, "scandal": seat.scandal, "bribes_year_to_date": seat.bribes_ytd,
		        "reputation": seat.reputation, "scandal_last_year": seat.scandal_last_year, "eminence": seat.eminence,
		        "familiarity": seat.familiarity, "demand_stance": seat.demand_stance, "service_offer": seat.service_offer,
		        "concealed": seat.concealed, "defiance": seat.defiance, "last_withdrawal": seat.last_withdrawal,
		        "governance": seat.gov}

	def eminence(self):
		return self.seat.eminence

	def value_weight(self, key):
		return self.world.value_weights[key]
