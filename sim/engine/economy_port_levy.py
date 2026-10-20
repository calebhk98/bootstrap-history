"""The working time a state takes from its people, handed to the agent economy each year."""


def levy_hours_per_worker(sim) -> float:
	"""Hours of each working-age person's year the home state called up for its works and its army this year
	(its record of hours taken), spread over the working age; zero before the state has acted."""
	government = sim.actors.government_of(None)
	working_age = sim.population.working_age
	if government is None or working_age <= 0.0:
		return 0.0
	return max(0.0, sum(government.record.corvee_hours.values()) / working_age)
