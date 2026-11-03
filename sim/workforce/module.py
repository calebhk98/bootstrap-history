"""The workforce module: people who work, their hours, wages and training, and the labour market.

`Labour` (sim/labour/) is its implementation; it is built over `WorkforceWorld` (world.py), which answers every outside
fact from the views this module declares. The people, hours and pay books of each seat are its seat state
(state.py), written only by `Labour` and the module's commands; everyone else reads them through the views."""
from sim.assembly.api import Module

from .applying_hours import ApplyingHours
from .applying_people import ApplyingPeople
from .apprenticeships import Apprenticeships
from .commands_applied import Applying
from .core import Core
from .hours_year import HoursYear
from .housing_prices import HousingPrices
from .prelude import Prelude
from .staff_hiring import StaffHiring
from .staff_watch import StaffWatch
from .staff_year import StaffYear
from .standing_bondage import StandingBondage
from .views import Views
from .views_facts import FactViews
from .views_report import ReportViews
from .views_standing import StandingViews
from .views_state import ViewsState
from .wage_fallback import WageFallback


class Workforce(Module):

	PARTS = {
		"core": Core,
		"standing_bondage": StandingBondage,
		"standing_views": StandingViews,
		"views": Views,
		"fact_views": FactViews,
		"report_views": ReportViews,
		"views_state": ViewsState,
		"applying": Applying,
		"applying_people": ApplyingPeople,
		"applying_hours": ApplyingHours,
		"staff_watch": StaffWatch,
		"apprenticeships": Apprenticeships,
		"staff_year": StaffYear,
		"staff_hiring": StaffHiring,
		"prelude": Prelude,
		"wage_fallback": WageFallback,
		"hours_year": HoursYear,
		"housing_prices": HousingPrices,
	}
