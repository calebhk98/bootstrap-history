"""One year for every seat: runs the phase registry in `year_phases` (shipped phases and mod phases alike).

World phases run once, with the first seat still in play acting (they read the society, not a holder).
Seat phases run for each seat in the fixed order the seats joined, each inside `act_as`. A seat whose run
ended (its founder died with no one to carry the work, was denounced or brought down) is left out of the
seat phases from then on; the others carry on. The market closes once, after every seat's draws and sales,
so a seat never sees another's draws within the year: a mechanism that wants another seat's state reads
last year's. `sim` is the Sim, or anything with the same phase methods."""
from .year_phases import run_phases
from . import invariants, year_steps


def run_year(sim):
	"""Advance the game one year."""
	run_phases(sim)
	if sim.debug:
		year_steps.verify_step_invariants(sim)
	elif len(sim.view("countries_in_game")()) > 1:
		invariants.check_yearly_invariants(sim)
