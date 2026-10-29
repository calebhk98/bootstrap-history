"""What the root does in the year's phases that no module owns: it asks the owners' views in the order the year runs and sends their
commands. Plain functions of the `Sim`, called by the entries of `year_phases.SHIPPED`."""
from dataclasses import dataclass

from sim.actors.api import AdvanceActors
from sim.agents.api import edges
from sim.coin.api import ChargeHouseholdTheft
from sim.demography.api import StepPopulation
from sim.finance.api import (ChargeInterest, EnforceCreditLimit, JudgeInsolvency, ServeBondageYear, ShedLossMakers,
                             WarnNearLimit)
from sim.hazards.api import RecoverOutput
from sim.ledger.api import PayEdge, PayWages, ReceiveFromEdge
from sim.markets.api import OpenMarketBook
from sim.polity.api import CloseStandingYear, RenewStanding
from sim.projects.api import (AdvanceProjects, AutoOpenVentures, CloseLapsedDependents, CloseSpendYear, CloseUnstaffedVentures, NoteVentureYear,
                              ReopenRestaffedVentures)
from sim.reporting.api import RecordAutomation
from sim.resources.api import AutoMothballMines, NoteMineCostPaid
from sim.workforce.api import (AutoBuyPeople, AutoManumit, ChargeLivingCost, CloseHoursYear, FadeMarketPressure,
                               TakeWageFallback)
from sim.diffusion.api import AdvanceSociety

from . import node_rederive
from .invariants import check_labour_market_invariants, check_yearly_invariants


@dataclass(frozen=True)
class StepContext:
	"""Immutable dependencies used by the turn phases."""
	trade_family: object
	invariant_checker: object


def verify_step_invariants(sim):
	"""Validate this turn without reading configuration from globals."""
	sim.step_context.invariant_checker(sim.state)
	check_yearly_invariants(sim)
	return check_labour_market_invariants(sim)


def begin_world_year(sim):
	"""What the society notes before the year starts."""
	node_rederive.refresh_derived_nodes(sim)
	sim.refresh_farm_territory()
	sim.send(OpenMarketBook())   # every book entry opens at the year's start, so a read before the first step cannot open one at another state


def money_seat(sim):
	"""The acting seat's takings, costs, credit and insolvency."""
	view, send, state = sim.view, sim.send, sim.state
	living_cost = view("living_cost")(None, None, None)
	living_cost = send(ChargeLivingCost(living_cost, view("dependants_beyond_means")(
		living_cost, view("revenue_estimate")(), view("upkeep")(), view("mine_operating_cost")())))
	mine_cost = view("mine_operating_cost")()
	send(NoteMineCostPaid(mine_cost))
	revenue, upkeep = view("revenue_estimate")(), view("upkeep")()
	keeping_owed, keeping = view("coin_keeping_due")(revenue, upkeep, living_cost, mine_cost)
	# the concerns the clearing pays are credited when it clears (economy_port_year `_settle_seats`)
	send(ReceiveFromEdge(edges.EDGE_CUSTOMERS, view("estimated_revenue")(), "venture revenue"))
	send(PayEdge(edges.EDGE_SUPPLIERS, upkeep, "running costs of concerns"))
	send(PayWages(living_cost, "living costs"))
	send(PayEdge(edges.EDGE_SUPPLIERS, mine_cost, "mine running costs"))
	send(PayEdge(edges.EDGE_COIN_GUARDS, keeping, "keeping coin under guard"))
	send(ChargeHouseholdTheft(keeping, keeping_owed))
	send(AutoMothballMines())
	# staff hired or taught this year get first claim on reclaiming what attrition shut, before anything is judged still short and closed again
	year = sim.year
	before = state.household.capital
	reopened = send(ReopenRestaffedVentures(year))
	if reopened:
		send(RecordAutomation("reopen (always on, not a policy)", "reopen", ", ".join(reopened), "a staffing closure, and the people to watch it are free again", before, dict(ids=list(reopened))))
	send(CloseLapsedDependents(year))
	send(CloseUnstaffedVentures(year))
	# open what plainly pays for itself before the books are struck: a concern opened this year earns this year
	if state.founder.policy.get("auto_open", not sim.manual):
		before = state.household.capital
		opened = send(AutoOpenVentures())
		if opened:
			send(RecordAutomation("auto_open", "open", ", ".join(opened), "net-positive concerns already built, within the staff and money available", before, dict(ids=list(opened))))
	send(ChargeInterest(year))
	send(NoteVentureYear())
	send(ShedLossMakers(year))
	send(WarnNearLimit(year))
	send(EnforceCreditLimit(year))
	send(JudgeInsolvency())
	send(AutoBuyPeople())
	send(AutoManumit())


def money_world(sim):
	"""The society's own year: output recovery, population, literacy and trades, the actors. Once a year."""
	sim.send(RecoverOutput())
	# population and the wage premium it drives recover on their own clock, before this year's shocks can add a fresh deficit
	sim.send(StepPopulation(sim.year))
	# a year's schooling gain is visible to this same year's teaching decisions
	sim.send(AdvanceSociety(sim.year))
	sim.send(AdvanceActors())


def seat_work(sim):
	"""What the acting seat does with its year once the projects are started and the materials seen to."""
	pool, hired_left = sim.view("start_hours")()
	remaining, remaining_after_projects, hours_effective_total = sim.send(AdvanceProjects(pool, hired_left))
	remaining = sim.send(TakeWageFallback(remaining))
	close_standing_and_books(sim, pool, remaining, remaining_after_projects, hours_effective_total)
	sim.send(ServeBondageYear())


def close_standing_and_books(sim, pool, remaining, remaining_after_projects, hours_effective_total):
	"""The year's close for reputation, hours, spending and the people market, in the order the tallies read each other."""
	sim.send(RenewStanding())
	sim.send(CloseHoursYear(pool, remaining, remaining_after_projects, hours_effective_total))
	sim.send(CloseSpendYear())
	sim.send(FadeMarketPressure())
	sim.send(CloseStandingYear())
