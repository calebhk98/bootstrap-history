"""A mass-mortality shock cut across the age cohorts, called with a population and not a game."""


def cut_cohorts(population, raw, vulnerability_child, vulnerability_working_age, vulnerability_elderly):
    """Cut the cohorts of `population` unevenly by age so the population-weighted average loss equals `raw`
    (a fraction of the whole), each cohort losing at most all of itself."""
    weighted = (population.children * vulnerability_child
                + population.working_age * vulnerability_working_age
                + population.elderly * vulnerability_elderly)
    if weighted <= 0.0 or raw <= 0.0:
        return
    scale = raw * population.total / weighted
    population.children -= population.children * min(1.0, scale * vulnerability_child)
    population.working_age -= population.working_age * min(1.0, scale * vulnerability_working_age)
    population.elderly -= population.elderly * min(1.0, scale * vulnerability_elderly)
