"""A foreign country's epidemics: the model the home nation runs (sim/disease), over the country's own age bands.

A pathogen arrives by the same contact rule as at home: while one of the country's `disease_exposure` windows is
open, and also while another country has it circulating (the between-country contact rule, a labelled temporary
heuristic until routes carry infected people). Its deaths, by band, go into the country's `Population.step`.
"""
from functools import lru_cache
from typing import Any, Dict, Iterable, Set

from sim.disease import api as disease

from .records import CountryProfile


@lru_cache(maxsize=1)
def _known() -> Dict[str, Any]:
	return disease.load_pathogens()


def introduce(profile: CountryProfile, pathogen_id: str) -> None:
	"""Have a pathogen reach this country at its next step (a scenario or a mod seeding an outbreak)."""
	profile.disease_arrivals.append(pathogen_id)


def circulating_in(profiles: Iterable[CountryProfile]) -> Set[str]:
	"""The pathogens someone in any of these countries is infected with now."""
	return {pathogen_id for profile in profiles for pathogen_id in profile.disease_records
			if disease.is_circulating(profile.disease_records, pathogen_id)}


def disease_deaths(profile: CountryProfile, people: Dict[str, float], nutrition_ratio: float, year: int,
				   seed_text: str, circulating_elsewhere: Set[str]) -> Dict[str, float]:
	"""Run the country's year of epidemics; the deaths by band for `Population.step(epidemic_deaths=)`."""
	windows = disease.nation.contact_windows(profile.extra.get("disease_exposure"))
	arrivals = disease.nation.introductions(profile.disease_records, windows, year, seed_text,
											also_present=circulating_elsewhere)
	arrivals += [pathogen_id for pathogen_id in profile.disease_arrivals if pathogen_id not in arrivals]
	profile.disease_arrivals = []
	return disease.nation.run_year(_known(), profile.disease_records, profile.disease_introduced, profile.disease_deaths,
								   people, nutrition_ratio, profile.urban_fraction, arrivals, seed_text, year)
