"""The workforce module: people who work, their hours, wages and training, and the labour market.

`Labour` (sim/labour/) is its implementation; it is built over `WorkforceWorld` (world.py), which answers every outside
fact from the views this module declares. The staff and hour fields it keeps are still on the household record
(`legacy_acting_household`), written only inside this module's commands and `Labour`; they move into this module's own
state when the household record does."""
from sim.assembly.api import Module
from sim.labour.api import Labour

from .apprenticeships import Apprenticeships
from .commands_applied import Applying
from .prelude import Prelude
from .staff_hiring import StaffHiring
from .staff_year import StaffYear
from .hours_year import HoursYear
from .views import Views
from .wage_fallback import WageFallback
from .world import WorkforceWorld


class Workforce(Views, Applying, Apprenticeships, StaffYear, StaffHiring, Prelude, WageFallback, HoursYear, Module):

	def setup(self):
		self.labour = Labour(WorkforceWorld(self.needs, self))
