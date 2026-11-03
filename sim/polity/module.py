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
from .standing_floor import StandingFloor
from .standing_views import StandingViews
from .transfers import Transfers
from .year import Year


class Polity(Module):

	PARTS = {
		"standing_views": StandingViews,
		"reach": Reach,
		"notice": Notice,
		"protection": Protection,
		"standing_floor": StandingFloor,
		"eminence": Eminence,
		"pressure": Pressure,
		"demands": Demands,
		"groups": Groups,
		"transfers": Transfers,
		"patronage": Patronage,
		"year": Year,
		"appliers": Appliers,
	}
