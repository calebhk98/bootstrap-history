"""The scenario module's rules: plain functions of the configuration, the civilisation and the save."""
from typing import Any, Dict, Mapping, Optional


def opening_start_year(civilisation: Mapping[str, Any], configuration: Mapping[str, Any]) -> int:
	"""A civilisation brings its own date: Norse Scandinavia does not start in 100 AD."""
	return int(civilisation.get("year", configuration["start_year"]))


def horizon_end_year(end_year: Optional[int], configuration: Mapping[str, Any]) -> int:
	"""The year the horizon ends: the one the player set, else the configured years after the start."""
	return end_year or (configuration["start_year"] + configuration["horizon_years"])


def society_name(civilisation: Mapping[str, Any]) -> str:
	return civilisation.get("name", "this society")


def danger_lines(configuration: Mapping[str, Any]) -> Dict[str, Any]:
	"""The eminence and suspicion figures past which a household is in danger."""
	return {"eminence": configuration["eminence_danger"], "suspicion": configuration["suspicion_danger"]}


def founder_life_terms(configuration: Mapping[str, Any], minimum_remaining_years: float) -> Dict[str, Any]:
	"""What a new founder's lifespan is drawn from."""
	return {"immortal": configuration["immortal"], "minimum": minimum_remaining_years,
	        "mean": configuration["founder_life_mean"], "spread": configuration["founder_life_sd"]}


def kit_capital(kit: Mapping[str, Any], annual_labourer_wage: float) -> float:
	"""Opening money of a kit: its labourer-years times the civilisation's opening annual labourer wage."""
	return kit["labourer_years"] * annual_labourer_wage


def scenario_slot_of(blob: Any) -> Dict[str, Any]:
	"""The saved scenario state of a save's parsed text, or an empty one when the save does not hold it."""
	modules = blob.get("modules") if isinstance(blob, dict) else None
	slot = modules.get("scenario") if isinstance(modules, dict) else None
	return slot if isinstance(slot, dict) else {}
