"""What the providers of the workforce module's extension points answered, combined: plain functions of the answers."""
from typing import Iterable, Optional


def overhead_hours(answers: Iterable[float]) -> float:
	"""Hours of the directed-hours pool the `director_overhead` providers charge, each answer counted as zero when negative."""
	return sum(max(0.0, float(hours)) for hours in answers)


def last_answer(answers: Iterable[Optional[float]]) -> Optional[float]:
	"""The last answer that is not None, never negative; None when no provider has an opinion (`town_population` and
	`town_mortality_premium`: a provider later in mod load order overrides an earlier one)."""
	chosen = None
	for found in answers:
		if found is not None:
			chosen = max(0.0, float(found))
	return chosen
