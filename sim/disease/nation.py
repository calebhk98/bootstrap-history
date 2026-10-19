"""One nation's disease year over three age bands, for any country that holds its people that way.

The home nation (`sim/engine/disease_port.py`) and each foreign country (`sim/agents/country_disease.py`) call
the same functions; the caller supplies the people, the food, the state to rewrite and the tuning numbers.
"""
import random

from . import year as year_step
from .nation_tuning import (AGE_FATALITY_FROM_STARVATION_VULNERABILITY, AGE_VULNERABILITY, AGEING, BANDS,
                            CAREGIVER_BANDS, DISEASE_CARE_COLLAPSE_SENSITIVITY, DISEASE_CONTACT_ANNUAL_CHANCE,
                            DISEASE_CONTACT_INFECTED_PEOPLE, DISEASE_URBAN_DENSITY_RATIO, INTRODUCTION_BAND)
from sim.world import demography


def contact_windows(exposure):
	"""[(pathogen ids, first year, last year)] a civilisation's `disease_exposure` says the outside world reaches it in."""
	return [(tuple(entry["pathogens"]), entry["years"][0], entry["years"][1])
			for entry in (exposure or {}).get("outside_contact", ())]


def introductions(records, windows, year, seed_text, annual_chance=None, also_present=()):
	"""Pathogens that arrive this year, each absent from the nation and drawn once: those listed in an open
	window, and those in `also_present` (circulating in a country it has contact with)."""
	chance = DISEASE_CONTACT_ANNUAL_CHANCE if annual_chance is None else annual_chance
	listed = [pathogen_id for pathogen_ids, first_year, last_year in windows if first_year <= year <= last_year
			  for pathogen_id in pathogen_ids]
	arrivals = []
	for pathogen_id in sorted(set(listed) | set(also_present)):
		if year_step.is_circulating(records, pathogen_id):
			continue
		if random.Random("%s:contact:%s:%d" % (seed_text, pathogen_id, year)).random() < chance:
			arrivals.append(pathogen_id)
	return arrivals


def crowding_index(urban_fraction, density_ratio=None):
	"""The person-weighted density relative to a rural settlement: one for a wholly rural people, rising toward
	the urban density ratio with the urban share."""
	ratio = DISEASE_URBAN_DENSITY_RATIO if density_ratio is None else density_ratio
	urban = min(1.0, max(0.0, float(urban_fraction)))
	return (1.0 - urban) + urban * ratio


def fatality_scale_by_band(people, nutrition_ratio):
	"""Each band's multiplier on a pathogen's case fatality: its relative vulnerability, rescaled to a
	population-weighted mean of one, times the shortfall of food it is living through."""
	total = sum(people.values())
	weight = {band: AGE_VULNERABILITY[band] ** AGE_FATALITY_FROM_STARVATION_VULNERABILITY for band in BANDS}
	mean = sum(people[band] * weight[band] for band in BANDS) / total if total > 0 else 1.0
	return {band: weight[band] / mean * demography.nutrition_mortality_multiplier(nutrition_ratio, AGE_VULNERABILITY[band])
			for band in BANDS}


def run_year(known, records, introduced, deaths, people, nutrition_ratio, urban_fraction, arrivals, seed_text, year,
			 fatality_factor=None, transmission_scale=None, care_sensitivity=None, density_ratio=None):
	"""Advance every pathogen in `records` or `arrivals` by a year, rewriting `records` (and the `introduced`
	years and running `deaths` per pathogen) in place; return `{band: deaths}` for `Population.step(epidemic_deaths=)`.
	Does nothing, at no cost, when there is no arrival and no pathogen under way."""
	if not arrivals and not records:
		return {}
	sensitivity = DISEASE_CARE_COLLAPSE_SENSITIVITY if care_sensitivity is None else care_sensitivity
	result = year_step.advance_year(
		known, records, people, seed_text, introductions=arrivals, introduction_band=INTRODUCTION_BAND,
		introduction_size=DISEASE_CONTACT_INFECTED_PEOPLE, ageing=AGEING,
		fatality_scale=fatality_scale_by_band(people, nutrition_ratio), transmission_scale=transmission_scale,
		fatality_factor=fatality_factor, crowding=crowding_index(urban_fraction, density_ratio),
		care_collapse=(CAREGIVER_BANDS, sensitivity))
	for pathogen_id in result.introduced:
		introduced.setdefault(pathogen_id, []).append(year)
	for pathogen_id, band_deaths in result.deaths_by_pathogen.items():
		deaths[pathogen_id] = deaths.get(pathogen_id, 0) + sum(band_deaths.values())
	return {band: float(count) for band, count in result.deaths_by_band.items()}
