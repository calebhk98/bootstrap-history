"""The registry of the year's phases: shipped phases and mod phases are entries of one kind, ordered by constraints.

A phase has a name, a scope and a handler. A seat phase is `handler(sim, seat_id)`, run for each seat inside
`act_as`; adjacent seat phases run together, seat by seat. A world phase is `handler(sim, seats)`, run once with
the first seat acting; it may return a new seat list (the seats still in play), and an empty list ends the year.
The shipped phases keep the order they are listed in. A mod phase names `after` and/or `before` phases (shipped
names, or `<mod_id>:<name>` for another mod's) and is placed right after its latest `after` or right before its
earliest `before`; the order is a pure function of the registrations, so it is the same on every run."""
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Sequence

from .mods_base import ModError

SEAT = "seat"
WORLD = "world"


@dataclass(frozen=True)
class Phase:
	name: str
	scope: str
	handler: Callable
	owner: str = ""                    # the mod that registered it; empty for a shipped phase
	after: Sequence[str] = ()
	before: Sequence[str] = ()


def module_seat_phase(name: str) -> Callable:
	"""A seat phase a module runs: its declared method is called with the seat id."""
	return lambda sim, seat_id: sim.assembly.phase_handler(name)(seat_id)


def module_world_phase(name: str) -> Callable:
	"""A world phase a module runs: its declared method is called with the seats still in play."""
	return lambda sim, seats: sim.assembly.phase_handler(name)(seats)


def _still_playing(sim, seats):
	return [seat_id for seat_id in seats if seat_id not in sim.ended_seats()]


def _advance_year(sim, seats):
	sim.state.scenario.year += 1


SHIPPED: List[Phase] = [
	Phase("begin_seat_year", SEAT, lambda sim, seat_id: sim.begin_seat_year()),
	Phase("trim_audit", SEAT, module_seat_phase("trim_audit")),
	Phase("hear_of_other_seats", SEAT, module_seat_phase("hear_of_other_seats")),
	Phase("begin_world_year", WORLD, lambda sim, seats: sim.begin_world_year()),
	Phase("apprenticeships", SEAT, lambda sim, seat_id: sim._step_apprenticeships()),
	Phase("staff", SEAT, lambda sim, seat_id: sim._step_staff()),
	Phase("money_seat", SEAT, lambda sim, seat_id: sim._step_money_seat()),
	Phase("money_world", WORLD, lambda sim, seats: sim._step_money_world()),
	Phase("win_conditions", SEAT, module_seat_phase("win_conditions")),
	Phase("dated_shocks", WORLD, module_world_phase("dated_shocks")),
	Phase("drop_ended_seats", WORLD, _still_playing),
	Phase("seat_prelude", SEAT, lambda sim, seat_id: sim._run_seat_prelude()),
	Phase("start_projects", SEAT, module_seat_phase("start_projects")),
	Phase("materials", SEAT, module_seat_phase("materials")),
	Phase("material_shortage_notes", SEAT, module_seat_phase("material_shortage_notes")),
	Phase("seat_work", SEAT, lambda sim, seat_id: sim._run_seat_work()),
	Phase("founder_mortality", SEAT, module_seat_phase("founder_mortality")),
	Phase("market", WORLD, lambda sim, seats: sim._step_market()),
	Phase("coin_revaluation", WORLD, module_world_phase("coin_revaluation")),
	Phase("wage_market_ratios", WORLD, module_world_phase("wage_market_ratios")),
	Phase("wild_stock", WORLD, module_world_phase("wild_stock")),
	Phase("soil_nitrogen", WORLD, module_world_phase("soil_nitrogen")),
	Phase("living_stock", SEAT, module_seat_phase("living_stock")),
	Phase("defence_stores", SEAT, module_seat_phase("defence_stores")),
	Phase("random_events", WORLD, module_world_phase("random_events")),
	Phase("world_hazards", WORLD, module_world_phase("world_hazards")),
	Phase("campaigns", WORLD, module_world_phase("campaigns")),
	Phase("revolts", WORLD, module_world_phase("revolts")),
	Phase("famine_watch", WORLD, module_world_phase("famine_watch")),
	Phase("credit_limit", SEAT, lambda sim, seat_id: sim.enforce_credit_limit(sim.state.scenario.year)),
	Phase("advance_year", WORLD, _advance_year),
]

MOD_PHASES: List[Phase] = []     # registered by mod code, in mod load order


def register_mod_phase(phase: Phase) -> None:
	MOD_PHASES.append(phase)


def _describe(phase: Phase) -> str:
	return "mod %s phase %s" % (phase.owner, phase.name) if phase.owner else "shipped phase %s" % phase.name


def _mod_order(known: Dict[str, Phase]) -> List[Phase]:
	"""Mod phases sorted so every mod phase follows the mod phases it depends on; ties keep registration order."""
	names = {phase.name: phase for phase in MOD_PHASES}
	for phase in MOD_PHASES:
		for reference in list(phase.after) + list(phase.before):
			if reference not in known and reference not in names:
				raise ModError("%s names the unknown phase %r" % (_describe(phase), reference))
	depends = {phase.name: [reference for reference in phase.after if reference in names]
	           + [other.name for other in MOD_PHASES if phase.name in other.before] for phase in MOD_PHASES}
	# depends[x] lists the mod phases that must run before x
	done: List[Phase] = []
	placed = set()
	pending = list(MOD_PHASES)
	while pending:
		ready = next((phase for phase in pending if all(name in placed for name in depends[phase.name])), None)
		if ready is None:
			first = pending[0]
			blocked = next(names[name] for name in depends[first.name] if name not in placed)
			raise ModError("phase constraints form a cycle between %s and %s" % (_describe(first), _describe(blocked)))
		pending.remove(ready)
		placed.add(ready.name)
		done.append(ready)
	return done


def ordered_phases() -> List[Phase]:
	"""The shipped phases with the mod phases placed by their constraints; ModError on an unknown name or a conflict."""
	phases = list(SHIPPED)
	if not MOD_PHASES:
		return phases
	known = {phase.name: phase for phase in SHIPPED}
	for phase in _mod_order(known):
		names = [other.name for other in phases]
		afters = [name for name in phase.after if name in names]
		befores = [name for name in phase.before if name in names]
		low = max([names.index(name) + 1 for name in afters], default=0)
		high = min([names.index(name) for name in befores], default=len(phases))
		if low > high:
			latest = max(afters, key=names.index)
			earliest = min(befores, key=names.index)
			raise ModError("%s cannot run after %s and before %s: %s comes first" % (
				_describe(phase), _describe(next(p for p in phases if p.name == latest)),
				_describe(next(p for p in phases if p.name == earliest)), earliest))
		position = low if afters else high
		while afters and position < high and phases[position].owner:
			position += 1
		phases.insert(position, phase)
	return phases


def run_phases(sim, phases: Optional[List[Phase]] = None) -> None:
	"""Run the year's phases in order."""
	phases = ordered_phases() if phases is None else phases
	seats = sim.playing_seats() or [sim.state.acting_seat]
	index = 0
	while index < len(phases) and seats:
		phase = phases[index]
		if phase.scope == WORLD:
			with sim.act_as(seats[0]):
				replacement = phase.handler(sim, seats)
			if replacement is not None:
				seats = list(replacement)
			index += 1
			continue
		run = [phase]
		while index + len(run) < len(phases) and phases[index + len(run)].scope == SEAT:
			run.append(phases[index + len(run)])
		for seat_id in seats:
			with sim.act_as(seat_id):
				for member in run:
					member.handler(sim, seat_id)
		index += len(run)
