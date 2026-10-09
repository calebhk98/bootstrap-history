"""One year for every seat: the order of the year's phases, which run once and which run for each seat.

World phases run once, with the first seat still in play acting (they read the society, not a holder).
Seat phases run for each seat in the fixed order the seats joined, each inside `act_as`. A seat whose run
ended (its founder died with no one to carry the work, was denounced or brought down) is left out of the
seat phases from then on; the others carry on. The market closes once, after every seat's draws and sales,
so a seat never sees another's draws within the year: a mechanism that wants another seat's state reads
last year's. `sim` is the Sim, or anything with the same phase methods."""


def run_year(sim):
	"""Advance the game one year."""
	seats = sim.playing_seats() or [sim.state.acting_seat]
	world = seats[0]
	for seat_id in seats:
		with sim.act_as(seat_id):
			sim.begin_seat_year()
	with sim.act_as(world):
		sim.begin_world_year()
	for seat_id in seats:
		with sim.act_as(seat_id):
			sim._step_apprenticeships()          # 0.  people whose apprenticeship ended
			sim._step_staff()                    # 1.  staff, attrition
			sim._step_money_seat()               # 2.  money
	with sim.act_as(world):
		sim._step_money_world()                  # 2.  the society's own year
	for seat_id in seats:
		with sim.act_as(seat_id):
			sim._step_win_conditions()           # 2c. threshold goals
	with sim.act_as(world):
		sim._step_dated_shocks(seats)            # 3.  dated shocks
	seats = [seat_id for seat_id in seats if seat_id not in sim.ended_seats()]
	if not seats:
		if sim.debug:
			sim.verify_step_invariants()
		return
	world = seats[0]
	for seat_id in seats:
		with sim.act_as(seat_id):
			sim._run_seat_work()                 # 4. to 7. what this seat does with the year
	with sim.act_as(world):
		sim._step_market()                       # 7b. the year's market closes
		sim.step_wild_stock()                    # 7c(ii). hunters thin the game, the game regrows
	for seat_id in seats:
		with sim.act_as(seat_id):
			sim.step_living_stock()              # 7c. held stock breeds and dies
			sim.step_defence_stores()            # 7d. threats spend the magazines, works restock them
	if sim.events:
		with sim.act_as(world):
			sim._random_events(sim.state.scenario.year, [s for s in seats if s not in sim.ended_seats()])   # 8.
	for seat_id in seats:
		with sim.act_as(seat_id):
			# The state's levy, the market and the shrinking of standing all move the purse after the money phase checked it.
			sim.enforce_credit_limit(sim.state.scenario.year)
	sim.state.scenario.year += 1
	if sim.debug:
		sim.verify_step_invariants()
