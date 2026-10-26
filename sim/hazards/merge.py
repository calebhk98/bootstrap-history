"""What a dated hazard does to the world when several seats each meet it differently.

Each seat's own works and conditions decide how hard the hazard bites that seat. The world effects
(population, output, the coin) happen once, and take the mildest figure any seat's works leave, so what
one seat builds shields the whole society as it would a single player's. Pure functions on hazard dicts."""
from typing import Dict, Iterable, Optional

# world effects where a larger number is the milder one, and where a smaller one is
MILDER_WHEN_HIGHER = ("output_factor",)
MILDER_WHEN_LOWER = ("real_erosion", "staff_loss")
# world effects that are one shape for everyone: kept only when every seat still meets them
SHARED_WHEN_ALL_MEET = ("values",)


def mildest_hazard(hazards: Iterable[Optional[Dict]]) -> Optional[Dict]:
	"""The hazard the world meets: None when any seat's causes or conditions leave it out entirely,
	else a copy with each world effect at its mildest across seats (dropped when any seat is spared it)."""
	given = list(hazards)
	if not given or any(hazard is None for hazard in given):
		return None
	merged = dict(given[0])
	for key in MILDER_WHEN_HIGHER + MILDER_WHEN_LOWER + SHARED_WHEN_ALL_MEET:
		if not all(key in hazard for hazard in given):
			merged.pop(key, None)
	for key in MILDER_WHEN_HIGHER:
		if key in merged:
			merged[key] = max(hazard[key] for hazard in given)
	for key in MILDER_WHEN_LOWER:
		if key in merged:
			merged[key] = min(hazard[key] for hazard in given)
	return merged
