"""The year's phases: what step() calls, in the order it calls them.

These are methods of Sim, living in a mixin (StepPhasesMixin) rather than
directly in core.py's `class Sim(...)`. `Sim.step()` itself stays in
core.py: it is the orchestrator, not one of the phases, and it is short
because it only runs the year's phases (sim/engine/year_phases.py). Method resolution walks the whole
MRO, so it does not matter to the phases that these live on StepPhasesMixin
rather than directly on Sim.

Each phase method below still reads and writes exactly the self.* state it
needs, UNASSIGNED to any one domain mixin's territory: this file groups
the phases by "step() calls them in this order", not by "the labour phase
belongs to labour.py, the money phase belongs to economy.py". Assigning
each phase's state to a specific domain mixin is a distinct, harder job
(see docs/architecture/SIM_DECOMPOSITION_REVISITED.md's staged proposal)
that this file does not attempt - do not assume a phase here can be moved
into a domain file without first working out its self.* footprint.
"""
import random
from dataclasses import dataclass

from sim.finance.api import ServeBondageYear
from sim.polity.api import CloseStandingYear, RenewStanding
from sim.projects.api import AdvanceProjects
from .invariants import check_labour_market_invariants, check_yearly_invariants
from .step_phase_money import MoneyPhaseMixin
from sim.workforce.api import CloseHoursYear, TakeWageFallback


@dataclass(frozen=True)
class StepContext:
    """Immutable dependencies used by the turn phases."""
    trade_family: object
    invariant_checker: object


class StepPhasesMixin(MoneyPhaseMixin):
    """Composition point for the named phases Sim.step() calls, in order. The money
    phases live in step_phase_money.py and come in through the base above (the start and the progress of projects are the
    projects module's); the rest are below. Sim inherits this mixin, so step() calls
    self._step_whatever() exactly as if these methods were defined directly on Sim.
    """

    def verify_step_invariants(self):
        """Validate this turn without reading configuration from globals."""
        self.step_context.invariant_checker(self.state)
        check_yearly_invariants(self)
        return check_labour_market_invariants(self)

    def begin_world_year(self):
        """What the society notes before the year starts."""
        self.refresh_derived_nodes()
        self.refresh_farm_territory()
        # open every book entry at the year's start, so a read before the first step cannot open one at another state
        self._open_market_book()

    def _run_seat_work(self):
        """What the acting seat does with its year once the projects are started and the materials seen to (the
        phases `seat_prelude`, `start_projects` and `materials` before it)."""
        pool, hired_left = self.view("start_hours")()   # 4b. measured by the start of projects
        # 5. progress, director hours
        remaining, remaining_after_projects, hours_effective_total = self.send(AdvanceProjects(pool, hired_left))
        # 5b. if there is no work and no money, take a job
        remaining = self.send(TakeWageFallback(remaining))
        # 6. reputation, familiarity, protection, scandal
        self._step_reputation(pool, remaining, remaining_after_projects, hours_effective_total)
        self._step_bondage()                   # 6b. serving out a debt

    def _step_reputation(self, pool, remaining, remaining_after_projects, hours_effective_total):
        # 6. reputation, familiarity, protection, scandal
        #
        # reputation decays toward what the household is known for, and familiarity is renewed: the polity module's
        self.send(RenewStanding())
        self.send(CloseHoursYear(pool, remaining, remaining_after_projects, hours_effective_total))
        self.state.household.spend_last_year = getattr(self, "_spend_this_year", 0.0)
        self._spend_this_year = 0.0
        # Sellers restock, so the pressure your buying put on the market fades.
        self.state.holdings.market_pressure = max(0.0, self.state.holdings.market_pressure * self.MARKET_PRESSURE_DECAY - self.MARKET_PRESSURE_ANNUAL_FADE)
        # eminence's warning, protection, the state's pressure, scandal, bribery and the two hazards that end a run: the polity module's
        self.send(CloseStandingYear())

    def _step_bondage(self):
        # 6b. serving out a debt: the finance module's year of service
        self.send(ServeBondageYear())

