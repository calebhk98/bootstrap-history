"""Workforce rules: plain functions of plain values."""


def surviving_people(dice, headcount: float, survival_share: float) -> float:
	"""How many of `headcount` people survive a shock: each is rolled one by one against `survival_share`, so headcounts
	stay whole. `dice` is the game's random source."""
	people = int(round(headcount))
	return float(sum(1 for _ in range(people) if dice.random() >= 1.0 - survival_share))
