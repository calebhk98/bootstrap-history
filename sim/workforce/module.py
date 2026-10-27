"""The workforce module: people who work, their hours, wages and training, and the labour market.

`Labour` (sim/labour/) is its implementation; it is built over `WorkforceWorld` (world.py), which answers every outside
fact from the views this module declares. The people, hours and pay books of each seat are its seat state
(state.py), written only by `Labour` and the module's commands; everyone else reads them through the views."""
from sim.assembly.api import Module
from sim.labour.api import Labour

from .apprenticeships import Apprenticeships
from .applying_hours import ApplyingHours
from .commands_applied import Applying
from .prelude import Prelude
from .staff_hiring import StaffHiring
from .staff_watch import StaffWatch
from .staff_year import StaffYear
from .hours_year import HoursYear
from .housing_prices import HousingPrices
from .views import Views
from .views_state import ViewsState
from .wage_fallback import WageFallback
from .world import WorkforceWorld


class Workforce(Views, ViewsState, Applying, ApplyingHours, StaffWatch, Apprenticeships, StaffYear, StaffHiring, Prelude, WageFallback, HoursYear, HousingPrices, Module):

	def setup(self):
		self.labour = Labour(WorkforceWorld(self.needs, self))
