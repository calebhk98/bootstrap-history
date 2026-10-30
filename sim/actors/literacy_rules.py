"""The reading shares of a country, asked and moved as plain functions of a `CountryLiteracy` over its strata."""
from typing import Any, Dict, Sequence, Tuple

LITERACY_FIELDS = ("literacy_general", "literacy_elite")   # the order a report lists them in


def figures(literacy: Any) -> Dict[str, float]:
	"""Each reading share as it stands."""
	return {field: literacy.get(field) for field in LITERACY_FIELDS}


def school(literacy: Any, steps: Sequence[Tuple[str, float, float]]) -> Tuple[Dict[str, float], Dict[str, float]]:
	"""Close, in order, each step's (field, fraction, ceiling) of the gap in place. Answers the figures before and after."""
	before = figures(literacy)
	for field, fraction, ceiling in steps:
		literacy.school(field, fraction, ceiling)
	return before, figures(literacy)
