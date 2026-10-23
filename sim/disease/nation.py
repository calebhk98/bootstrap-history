"""One nation's disease year over three age bands, for any country that holds its people that way.

The home nation (`sim/engine/disease_port.py`) and each foreign country (`sim/agents/country_disease.py`) call
the same functions; the caller supplies the people, the food, the state to rewrite and the tuning numbers.
"""
import math
import random

from . import year as year_step
from .nation_tuning import (AGE_FATALITY_FROM_STARVATION_VULNERABILITY, AGE_VULNERABILITY, AGEING, BANDS,
                            CAREGIVER_BANDS, DISEASE_CARE_COLLAPSE_SENSITIVITY, DISEASE_EMERGENCE_ANNUAL_CHANCE,
                            DISEASE_CONTACT_INFECTED_PEOPLE, DISEASE_TRAVELLER_ANNUAL_CHANCE, DISEASE_TRAVEL_DECAY_DAYS, DISEASE_URBAN_DENSITY_RATIO, INTRODUCTION_BAND,
                            SURVIVING_SHARE_FLOOR)
from sim.world import demography


def contact_sources(exposure):
	"""The outside sources a civilisation's `disease_exposure` names, as plain records: {pathogens, tiles,
	carrier_modes, circulating, first_year, last_year}. `tiles` are map tiles where the pathogens live outside the
	nation; `carrier_modes` are carriage modes the outsiders bring (so a people with no ships can still be reached by
	sea); `circulating` says the pathogens are always present at the source, else they only now and then start
	there; the years, when given, are when the contact exists at all."""
	return [{"pathogens": tuple(entry["pathogens"]), "tiles": tuple(entry.get("tiles", ())),
			 "carrier_modes": tuple(entry.get("carrier_modes", ())), "circulating": bool(entry.get("circulating", False)),
			 "first_year": (entry.get("years") or (None, None))[0], "last_year": (entry.get("years") or (None, None))[1]}
			for entry in (exposure or {}).get("outside_contact", ())]


def contact_weight(travel_days):
	"""The share of a source's contact that routes let through: one at no distance, falling with the fewest days of
	travel between the source and the nation, zero when no route joins them (`travel_days` None)."""
	if travel_days is None:
		return 0.0
	return math.exp(-max(0.0, travel_days) / DISEASE_TRAVEL_DECAY_DAYS)


def arrival_chances(sources, year, weight_of=None):
	"""{pathogen id: chance it reaches the nation this year} over every source whose contact is open. A source's
	chance is its traveller rate (always present there) or its emergence rate (it starts there now and then), times
	`weight_of(source)`, the share of that rate that routes let through; sources combine as independent chances."""
	missed = {}
	for source in sources:
		if source["first_year"] is not None and not source["first_year"] <= year <= source["last_year"]:
			continue
		weight = 1.0 if weight_of is None else weight_of(source)
		if weight <= 0.0:
			continue
		rate = DISEASE_TRAVELLER_ANNUAL_CHANCE if source["circulating"] else DISEASE_EMERGENCE_ANNUAL_CHANCE
		for pathogen_id in source["pathogens"]:
			missed[pathogen_id] = missed.get(pathogen_id, 1.0) * (1.0 - min(1.0, rate * weight))
	return {pathogen_id: 1.0 - kept for pathogen_id, kept in missed.items()}


def introductions(records, chances, year, seed_text, also_present=()):
	"""Pathogens that arrive this year, each absent from the nation and drawn once against its chance (from
	`arrival_chances`); those in `also_present` (circulating in a country it has contact with) draw at the
	traveller rate."""
	chances = dict(chances)
	for pathogen_id in also_present:
		chances[pathogen_id] = max(chances.get(pathogen_id, 0.0), DISEASE_TRAVELLER_ANNUAL_CHANCE)
	arrivals = []
	for pathogen_id in sorted(chances):
		if year_step.is_circulating(records, pathogen_id):
			continue
		if random.Random("%s:contact:%s:%d" % (seed_text, pathogen_id, year)).random() < chances[pathogen_id]:
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


def provisioning_factor(disease_loss):
    """The multiple of a party (settlers outfitted, soldiers kept in the field) that a place's yearly disease loss
    (the share of working-age people it takes, from the endemic rate and the model's forecast) makes necessary for
    the stated number to be there at the end of the year."""
    return 1.0 / max(1.0 - max(float(disease_loss), 0.0), SURVIVING_SHARE_FLOOR)
