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

from .bondage_workshop_rules import bondage_repayment, serve_bondage_year
from sim.polity.api import CloseStandingYear, RenewStanding
from .invariants import check_labour_market_invariants, check_yearly_invariants
from .step_phase_money import MoneyPhaseMixin
from .step_phase_projects import ProjectProgressPhaseMixin
from sim.reporting.api import RecordEvent


@dataclass(frozen=True)
class StepContext:
    """Immutable dependencies used by the turn phases."""
    trade_family: object
    invariant_checker: object


class StepPhasesMixin(MoneyPhaseMixin, ProjectProgressPhaseMixin):
    """Composition point for the named phases Sim.step() calls, in order. The money,
    materials and project-progress phases live in step_phase_*.py (the start of projects is the projects module's
    phase) and come in through the
    bases above; the rest are below. Sim inherits this mixin, so step() calls
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
        remaining, remaining_after_projects, hours_effective_total = (
            self._step_progress(pool, hired_left))
        # 5b. if there is no work and no money, take a job
        remaining = self._step_wage_fallback(remaining)
        # 6. reputation, familiarity, protection, scandal
        self._step_reputation(pool, remaining, remaining_after_projects, hours_effective_total)
        self._step_bondage()                   # 6b. serving out a debt

    def _step_wage_fallback(self, remaining):
        # 5b. IF THERE IS NO WORK AND NO MONEY, TAKE A JOB. A man who arrives
        #     with four hundred denarii and a lens does not sit watching his
        #     savings run out; he teaches, or writes, or sets bones for money. It
        #     is in the protocol as `work` for a player and the optimizer had no
        #     equivalent, so a single bad year in the opening decade could end a
        #     run: one Rome seed earned four technologies in five hundred years
        #     because a fire in 103 took a fifth of everything it had.
        if (not self.manual and remaining > self.WAGE_FALLBACK_MIN_HOURS
                and (self.state.household.capital < self.living_cost() * self.WAGE_FALLBACK_LIVING_COST_YEARS
                     or not self.state.projects.active)):
            trade = ("scholar" if self.labour.effective_scholars() >= 1 else "scribe")
            hours = min(remaining, self.WAGE_FALLBACK_MAX_HOURS)
            # ONLY IF IT PAYS BETTER THAN THE STANDING JOB IT TAKES THE HOURS FROM: a founder who already
            # sells these hours in a trade does not move them to a worse-paid one.
            # NOT `pool`: that name already holds the year's project budget,
            # computed at 4b. Reusing it here would overwrite it, so
            # hours_this_year would then report "offered_to_projects"
            # against the WHOLE year instead of against the project budget,
            # letting a year's hours add up to more than what was actually
            # available.
            held_trade = self.held_trade()
            standing_pay = (self.labour.wage_for_hours(held_trade, hours) if held_trade else 0.0)
            if self.labour.wage_for_hours(trade, hours) > standing_pay:
                _, err = self.labour.work_for_wages(trade, hours)
                # Kept in step with `remaining` so hours_this_year (below) does
                # not count hours sold for wages here as still unused.
                if err is None:
                    remaining -= hours
        return remaining

    def _step_reputation(self, pool, remaining, remaining_after_projects, hours_effective_total):
        # 6. reputation, familiarity, protection, scandal
        #
        # reputation decays toward what the household is known for, and familiarity is renewed: the polity module's
        self.send(RenewStanding())
        # WHERE THE YEAR'S HOURS WENT: captured here, before the tallies
        # below reset for the next year, the same way spend_last_year
        # already captures the year's spending, so a player can see the
        # breakdown as `hours_this_year` in `state` rather than only a
        # final hours-left figure with no way to tell where the rest went.
        self.hours_this_year = {
            "available": round(self.labour.director_pool(), 1),
            "wage_work": round(self.state.household.wage_hours_this_year, 1),
            "teaching": round(self.state.household.teaching_hours_this_year, 1),
            "moving": round(self.state.household.relocation_hours_this_year or 0.0, 1),
            "supervising": round(self.state.household.supervision_hours_this_year, 1),
            "offered_to_projects": round(max(0.0, pool - remaining_after_projects), 1),
            # OFFERED is what projects were given a shot at; EFFECTIVE is what
            # actually reduced their founder_hours_left. The gap between the
            # two is hours that went in and came straight back out again
            # because a trade or the money to pay for it fell short that year
            # - see hours_offered_this_year / hours_effective_this_year on
            # each project in `active`, and underfunded_this_year.
            "effective_on_projects": round(hours_effective_total, 1),
            "unused": round(max(0.0, remaining), 1),
        }
        # Reset AFTER the progress pass above, which is where the hours you sold
        # are subtracted from the hours you have left to direct.
        self.labour.close_wage_year()
        # Contracted work is bought for a year and expires with it: hours you
        # paid a shop for in 142 are not still sitting there in 143.
        self.state.household.contract_hours = {}
        self.state.household.teaching_hours_this_year = 0.0
        self.state.household.relocation_hours_this_year = 0.0
        self.state.household.supervision_hours_this_year = 0.0
        self.state.household.spend_last_year = getattr(self, "_spend_this_year", 0.0)
        self._spend_this_year = 0.0
        # Sellers restock, so the pressure your buying put on the market fades.
        self.state.holdings.market_pressure = max(0.0, self.state.holdings.market_pressure * self.MARKET_PRESSURE_DECAY - self.MARKET_PRESSURE_ANNUAL_FADE)
        # eminence's warning, protection, the state's pressure, scandal, bribery and the two hazards that end a run: the polity module's
        self.send(CloseStandingYear())

    def _step_bondage(self):
        # 6b. serving out a debt. The hours you owe go to the creditor and the
        #     debt falls; when it is done you are free, and you keep everything
        #     you know.
        household = self.state.household
        if household.bondage_years_left > 0:
            repayment = bondage_repayment(self.cfg["founder_hours_per_year"], self.BONDAGE_LABOUR_SHARE,
                                          self.BONDAGE_WAGE_MARKUP, self.labour.market.quote("labourer"))
            household.bondage_years_left, household.bondage_debt, served = serve_bondage_year(
                household.bondage_years_left, household.bondage_debt, repayment)
            if served:
                self.send(RecordEvent.of("bondage_served", "your term is served and the debt is discharged; "
                                     "you are your own man again"))

