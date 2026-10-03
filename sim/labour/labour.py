"""People: hiring them, teaching them, buying them, paying them.

`Labour` is the labour of one simulation (`sim.labour`). It reads the rest of the simulation through
the world it is given (an engine-side adapter, sim/engine/labour_port.py) and holds nothing of the
engine itself.

This file is a pure composition point: one file holding all of a household's labour mechanics
becomes a file nobody can edit without colliding with everyone else touching them, so the methods
live in sibling modules, grouped by subject, and this file composes them into the single `Labour`:

    labour_capacity.py       literacy, institutional (staff_capacity) and supervisory
                             (supervision_room) ceilings on how many people this household may hire,
                             teach, own or direct, plus the founder's own hour budget the rest
                             spends (CapacityMixin)
    labour_population.py     the local labour market itself - depth, price response to recent hiring,
                             and the population estimates the 'population' command shows
                             (PopulationMixin)
    labour_settlement.py     the base tile, the town there, and moving it (SettlementMixin)
    labour_wages.py          what staff actually cost every year, and what it costs to be one
                             yourself (WagesMixin)
    labour_training.py       hiring, firing, teaching, commissioning, and what a technology does to
                             an hour once bought (TrainingMixin)
    labour_bondage.py        buying people, freeing them, and the pool bookkeeping that keeps
                             trained/granted staff honest (BondageMixin)
    labour_staff_ledger.py   who left the payroll and why, which specialists nothing uses (StaffLedgerMixin)
    labour_staff_controls.py concerns to keep staffed and a reserve of spare hands (StaffControlsMixin)
    labour_allocation.py     the farm workforce and the labour market's split of the rest
                             (LabourAllocationMixin)

No method appears in more than one of them; see each module's own docstring for exactly which
methods it holds and why they sit together.
"""
from .labour_capacity import CapacityMixin
from .labour_population import PopulationMixin
from .labour_settlement import SettlementMixin
from .labour_wages import WagesMixin
from .labour_training import TrainingMixin
from .labour_bondage import BondageMixin
from .labour_staff_ledger import StaffLedgerMixin
from .labour_staff_controls import StaffControlsMixin
from .labour_allocation import LabourAllocationMixin


class Labour(CapacityMixin, PopulationMixin, SettlementMixin, WagesMixin, TrainingMixin, BondageMixin,
             StaffLedgerMixin, StaffControlsMixin, LabourAllocationMixin):
    """Questions and transactions about labour, for one simulation. `world` is what labour reads of it."""

    def __init__(self, world):
        self._world = world

    @property
    def market(self):
        """The labour market every employer asks (labour_market_api.LabourMarket)."""
        return self.labour_market

    def allocate_farm_workforce(self, adult_equivalent_population):
        return self._allocate_farm_workforce(adult_equivalent_population)

    def apply_land_clearing(self):
        return self._apply_land_clearing()

    def grant_staff(self, scholars=0.0, artisans=0.0):
        return self._grant_staff(scholars, artisans)

    def opening_wage_schedule(self):
        return self._opening_wage_schedule()

    def resync_pools(self):
        return self._resync_pools()

    def room_advice(self):
        return self._room_advice()

    def set_farm_area(self, hectares):
        return self._set_farm_area(hectares)

    def staff_advice(self, kind, deficit=None):
        return self._staff_advice(kind, deficit)

    def stochastic_round(self, x):
        return self._stochastic_round(x)

    def trade_headcount_pending(self, trade):
        return self._trade_headcount_pending(trade)
