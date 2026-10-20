"""The key a household-demand answer is cached under: the answer is computed from the key, never from the raw inputs,
so a cached answer and a fresh one are the same number."""

POPULATION_DIGITS = 3
INCOME_DIGITS = 3


def demand_key(population, opening_population, income_hours_per_capita):
    """(population over the opening's, income per head), each rounded to a thousandth."""
    return (round(float(population) / opening_population, POPULATION_DIGITS),
            round(income_hours_per_capita, INCOME_DIGITS))


def population_of_key(key, opening_population):
    """The population the key stands for."""
    return key[0] * opening_population
