"""A nation as a metapopulation: one patch of age bands per tile, infection passing along the edges between tiles.

Each tile holds its people as the age-band patches `sim/disease/step.py` steps. The force of infection on a tile
is its own infectious share (times the tile's crowding to the pathogen's `density_exponent`) plus, for every tile
joined to it by traffic, the other tile's infectious share times the share of this tile's people-days that the
traffic shares with it. Traffic is people moving: the crews that go with the tonnes merchants carry, and migrants.
No traffic, no spread between tiles; more traffic, more; a crowded tile passes and takes infection faster.

Randomness is seeded afresh each year from the game's seed text, the pathogen, the tile, the band and the year, so
the saved state is only counts and a loaded game draws what a straight run would. The same stepping with expected
values in place of draws forecasts a year (`forecast_year`).
"""
import math

from sim.unit_conversions import CIVIL_DAYS_PER_YEAR as DAYS_PER_YEAR

from . import network
from .endemic_state import endemic_counts
from .nation_tuning import (AGEING, BANDS, CAREGIVER_BANDS, DISEASE_CARE_COLLAPSE_SENSITIVITY,
                            DISEASE_CONTACT_INFECTED_PEOPLE, INTRODUCTION_BAND)
from .numerics import binomial
from .spread_tuning import (DISEASE_LOCAL_TRIPS_PER_PERSON_YEAR, DISEASE_TRAVELLERS_PER_TONNE_CARRIED,
                            DISEASE_VISIT_DAYS)
from .step import _advance_one, care_collapse_multiplier, wane_idle
from .types import Patch
from .year import _fit_to_people, _move_share


def expected(_rng, trials, probability):
    """The expected number of successes: the stepping's draw when it forecasts rather than runs."""
    return trials * probability


# ---- traffic and contact ------------------------------------------------------------------------------------

def _pair(first, second):
    return (first, second) if first < second else (second, first)


def trade_trips(carried, tiles, travellers_per_tonne=DISEASE_TRAVELLERS_PER_TONNE_CARRIED):
    """{(tile, tile): trips in a year} between tiles of `tiles` from the tonnes merchants carried between them
    (`{origin: {destination: tonnes}}`), either way, each tonne taking `travellers_per_tonne` people."""
    members = set(tiles)
    trips = {}
    for origin, row in carried.items():
        for destination, tonnes in row.items():
            if origin != destination and origin in members and destination in members and tonnes > 0.0:
                key = _pair(origin, destination)
                trips[key] = trips.get(key, 0.0) + tonnes * travellers_per_tonne
    return trips


def migrant_trips(emigrants, immigrants, borders):
    """{(tile, tile): migrants} between bordering tiles: a tile's emigrants go to the tiles it borders in
    proportion to the people those tiles took in (`emigrants`, `immigrants` are {tile: people}, `borders`
    is {tile: bordering tiles})."""
    trips = {}
    for origin in sorted(emigrants):
        leaving = emigrants[origin]
        neighbours = [tile for tile in borders.get(origin, ()) if immigrants.get(tile, 0.0) > 0.0]
        taken = sum(immigrants[tile] for tile in neighbours)
        if leaving <= 0.0 or taken <= 0.0:
            continue
        for tile in neighbours:
            key = _pair(origin, tile)
            trips[key] = trips.get(key, 0.0) + leaving * immigrants[tile] / taken
    return trips


def local_trips(people_by_tile, borders, trips_per_person=DISEASE_LOCAL_TRIPS_PER_PERSON_YEAR):
    """{(tile, tile): trips} between bordering tiles: every person makes `trips_per_person` trips a year to the
    tiles the tile borders, shared out by those tiles' people."""
    people = {tile: sum(bands.values()) for tile, bands in people_by_tile.items()}
    trips = {}
    for origin in sorted(people):
        neighbours = [tile for tile in borders.get(origin, ()) if people.get(tile, 0.0) > 0.0]
        taken = sum(people[tile] for tile in neighbours)
        if people[origin] <= 0.0 or taken <= 0.0:
            continue
        for tile in neighbours:
            key = _pair(origin, tile)
            trips[key] = trips.get(key, 0.0) + people[origin] * trips_per_person * people[tile] / taken
    return trips


def add_trips(*flows):
    total = {}
    for flow in flows:
        for key, trips in flow.items():
            total[key] = total.get(key, 0.0) + trips
    return total


def contacts_from_trips(trips, people_by_tile, visit_days=DISEASE_VISIT_DAYS):
    """{tile: [(other tile, share of this tile's people-days spent with the other tile's people)]}. Trips in
    either direction put the same person-days in the same place; a tile's shares are scaled down together if
    they would add to more than all of its time."""
    contacts = {}
    for (first, second), count in sorted(trips.items()):
        if first not in people_by_tile or second not in people_by_tile or count <= 0.0:
            continue
        for tile, other in ((first, second), (second, first)):
            people = sum(people_by_tile[tile].values())
            if people > 0.0:
                contacts.setdefault(tile, []).append((other, count * visit_days / DAYS_PER_YEAR / people))
    for tile, links in contacts.items():
        total = sum(share for _, share in links)
        if total > 1.0:
            contacts[tile] = [(other, share / total) for other, share in links]
    return contacts


def crowding_by_tile(people_by_tile, area_by_tile, national_index):
    """{tile: crowding}: each tile's person density over the people-weighted mean density, times the nation's
    crowding index, so the people-weighted mean is the nation's index and a dense town sits above the countryside.
    A tile with no known area takes the national index."""
    people = {tile: sum(bands.values()) for tile, bands in people_by_tile.items()}
    density = {tile: people[tile] / area_by_tile[tile] for tile in people if area_by_tile.get(tile, 0.0) > 0.0}
    weight = sum(people[tile] for tile in density)
    mean = sum(people[tile] * density[tile] for tile in density) / weight if weight > 0.0 else 0.0
    return {tile: national_index * density[tile] / mean if tile in density and mean > 0.0 else national_index
            for tile in people}


# ---- the patches -------------------------------------------------------------------------------------------

def is_circulating(records, pathogen_id):
    """Whether anyone in any tile of the saved `records` is infected with `pathogen_id` right now."""
    tiles = records.get(pathogen_id)
    if not tiles:
        return False
    names = {name for bands in tiles.values() for counts in bands.values() for name in counts
             if name not in (network.SUSCEPTIBLE, network.RECOVERED)}
    return any(counts.get(name, 0) > 0 for bands in tiles.values() for counts in bands.values() for name in names)


def infected_total(records, pathogen_id):
    """People infected with the pathogen across the tiles of the saved records."""
    return sum(count for bands in (records.get(pathogen_id) or {}).values() for counts in bands.values()
               for name, count in counts.items() if name not in (network.SUSCEPTIBLE, network.RECOVERED))


def _rounded(people_by_band):
    return {band: int(round(people_by_band[band])) for band in BANDS}


def patches_for(pathogen, saved, people_by_tile, crowding, seed_text, year, endemic=False, ageing=AGEING):
    """{tile: {band: Patch}} for every tile in `people_by_tile`: the saved counts moved across the band edges and
    fitted to the people there now; a tile with no saved counts (the pathogen is new, or so is the tile) opens
    naive, or at the endemic equilibrium when the pathogen is endemic to the people."""
    tiles = {}
    for tile in sorted(people_by_tile):
        people = _rounded(people_by_tile[tile])
        seeds = {band: "%s:%s:%s:%s:%d" % (seed_text, pathogen.id, tile, band, year) for band in BANDS}
        if saved is not None and tile in saved:
            patches = {band: Patch(counts=dict(saved[tile][band]), seed=seeds[band]) for band in BANDS}
            for band, (next_band, share) in ageing.items():
                _move_share(patches[band], patches[next_band], share)
            for band in BANDS:
                _fit_to_people(patches[band], people[band])
        else:
            if endemic:
                counts = endemic_counts(pathogen, people, crowding.get(tile, 1.0))
            else:
                counts = {band: {name: 0 for name in network.compartment_ids(pathogen)} for band in BANDS}
                for band in BANDS:
                    counts[band][network.SUSCEPTIBLE] = people[band]
            patches = {band: Patch(counts=counts[band], seed=seeds[band]) for band in BANDS}
        tiles[tile] = patches
    return tiles


def _saved(tiles):
    return {tile: {band: dict(patch.counts) for band, patch in patches.items()} for tile, patches in tiles.items()}


# ---- stepping ----------------------------------------------------------------------------------------------

def infected_tiles(pathogen, tiles):
    """The tiles where anyone is infected now."""
    names = network.infected_ids(pathogen)
    return {tile for tile, patches in tiles.items() if any(patch.counts[name] for patch in patches.values() for name in names)}


def step_tiles(pathogen, tiles, contacts, density_factor, step, fatality_scale=None, transmission_scale=1.0,
               care_collapse=None, draw=binomial, infected=None):
    """One step over every tile. A tile is stepped when someone in it is infected or a joined tile's infection
    can reach it (or immunity wanes); the others cost nothing. All forces are read before any tile moves.
    `infected` is the set of tiles with anyone infected (found when not given); returns it as the step leaves it."""
    stages = network.substages(pathogen)
    infected_names = network.infected_ids(pathogen)
    waning = not pathogen.immunity_permanent and bool(pathogen.immunity_duration_in_days)
    infected = infected_tiles(pathogen, tiles) if infected is None else infected
    prevalence, exits = {}, {}
    for tile in infected:
        patches = tiles[tile]
        living = sum(patch.living() for patch in patches.values())
        exits[tile] = {band: [draw(patch.rng, patch.counts[name], _chance(rate, step)) if patch.counts[name] else 0
                              for name, _, rate in stages] for band, patch in patches.items()}
        infectious = sum(infectiousness * (patch.counts[name] - 0.5 * leaving)
                         for band, patch in patches.items()
                         for (name, infectiousness, _), leaving in zip(stages, exits[tile][band]))
        prevalence[tile] = infectious / living if living > 0 else 0.0
    if waning:
        active = set(tiles)
    else:
        active = set(prevalence)
        for tile in prevalence:
            active.update(other for other, _ in contacts.get(tile, ()) if other in tiles)
    idle_exits = [0] * len(stages)
    for tile in sorted(active):
        patches = tiles[tile]
        imported = sum(share * 0.5 * (density_factor[tile] + density_factor[other]) * prevalence[other]
                       for other, share in contacts.get(tile, ()) if other in prevalence)
        force = pathogen.transmissibility_per_day * transmission_scale * (
            density_factor[tile] * prevalence.get(tile, 0.0) + imported)
        care = care_collapse_multiplier(patches, care_collapse) if tile in exits else 1.0
        for band, patch in patches.items():
            leaving = exits[tile][band] if tile in exits else idle_exits
            _advance_one(pathogen, patch, stages, leaving, force, step,
                         fatality=min(1.0, pathogen.case_fatality * (fatality_scale or {}).get(band, 1.0) * care),
                         draw=draw)
        if any(patch.counts[name] for patch in patches.values() for name in infected_names):
            infected.add(tile)
        else:
            infected.discard(tile)
    return infected


def _chance(rate, days):
    return -math.expm1(-rate * days)


def advance_tiles(pathogen, tiles, contacts, crowding, days, fatality_scale=None, transmission_scale=1.0,
                  care_collapse=None, draw=binomial):
    """Run `days` in equal steps no longer than the pathogen's own step length."""
    steps = max(1, math.ceil(days / network.step_length_in_days(pathogen) - 1e-9))
    density_factor = {tile: max(crowding.get(tile, 1.0), 0.0) ** pathogen.density_exponent for tile in tiles}
    infected = infected_tiles(pathogen, tiles)
    for _ in range(steps):
        step_tiles(pathogen, tiles, contacts, density_factor, days / steps, fatality_scale, transmission_scale,
                   care_collapse, draw, infected)


def _deaths(tiles):
    by_tile = {tile: {band: patch.deaths_from_disease for band, patch in patches.items()} for tile, patches in tiles.items()}
    return {tile: bands for tile, bands in by_tile.items() if any(bands.values())}


def run_year(known, records, introduced, deaths, people_by_tile, contacts, crowding, fatality_scale, arrivals,
             seed_text, year, fatality_factor=None, transmission_scale=None, care_sensitivity=None, endemic=()):
    """Advance every pathogen in `records` or `arrivals` (`{pathogen id: tile it enters at}`) by a year over the
    tiles, rewriting `records` (`{pathogen id: {tile: {band: counts}}}`), the `introduced` years and the running
    `deaths` per pathogen in place. A pathogen in `endemic` with no record opens at its endemic equilibrium. Returns
    `{tile: {band: deaths}}` for the year. Does nothing, at no cost, when there is no arrival, no endemic
    pathogen and none under way."""
    if not arrivals and not records and not endemic:
        return {}
    sensitivity = DISEASE_CARE_COLLAPSE_SENSITIVITY if care_sensitivity is None else care_sensitivity
    transmission_scale, fatality_factor = transmission_scale or {}, fatality_factor or {}
    by_tile = {}
    for pathogen_id in sorted(set(records) | set(arrivals) | set(endemic)):
        pathogen = known[pathogen_id]
        tiles = patches_for(pathogen, records.get(pathogen_id), people_by_tile, crowding, seed_text, year,
                            endemic=pathogen_id in endemic)
        if pathogen_id in arrivals and arrivals[pathogen_id] in tiles:
            tiles[arrivals[pathogen_id]][INTRODUCTION_BAND].seed_infection(pathogen, DISEASE_CONTACT_INFECTED_PEOPLE)
            introduced.setdefault(pathogen_id, []).append(year)
        if any(patch.infected_now() for patches in tiles.values() for patch in patches.values()):
            scale = {band: fatality_scale.get(band, 1.0) * fatality_factor.get(pathogen_id, 1.0) for band in BANDS}
            advance_tiles(pathogen, tiles, contacts, crowding, DAYS_PER_YEAR, fatality_scale=scale,
                          transmission_scale=transmission_scale.get(pathogen_id, 1.0),
                          care_collapse=(CAREGIVER_BANDS, sensitivity))
        elif not pathogen.immunity_permanent:
            for patches in tiles.values():
                for patch in patches.values():
                    wane_idle(pathogen, patch, DAYS_PER_YEAR)
        killed = _deaths(tiles)
        for tile, bands in killed.items():
            for band, count in bands.items():
                by_tile.setdefault(tile, {}).setdefault(band, 0)
                by_tile[tile][band] += count
        deaths[pathogen_id] = deaths.get(pathogen_id, 0) + sum(sum(bands.values()) for bands in killed.values())
        records[pathogen_id] = _saved(tiles)
    return by_tile


def deaths_by_band(by_tile):
    """{band: deaths} of a year's `{tile: {band: deaths}}`."""
    total = {}
    for bands in by_tile.values():
        for band, count in bands.items():
            total[band] = total.get(band, 0.0) + float(count)
    return total


def forecast_year(known, records, people_by_tile, contacts, crowding, fatality_scale, seed_text, year,
                  fatality_factor=None, transmission_scale=None, care_sensitivity=None):
    """The model's own forecast of the coming year with no new arrival: `{pathogen id: {"infected": people now
    infected, "expected_deaths_by_tile": {tile: {band: deaths}}}}` for each pathogen with anyone infected, from the same
    stepping with expected values in place of draws. Nothing in `records` changes."""
    sensitivity = DISEASE_CARE_COLLAPSE_SENSITIVITY if care_sensitivity is None else care_sensitivity
    transmission_scale, fatality_factor = transmission_scale or {}, fatality_factor or {}
    forecast = {}
    for pathogen_id in sorted(records):
        if not is_circulating(records, pathogen_id):
            continue
        pathogen = known[pathogen_id]
        tiles = patches_for(pathogen, records[pathogen_id], people_by_tile, crowding, seed_text, year)
        scale = {band: fatality_scale.get(band, 1.0) * fatality_factor.get(pathogen_id, 1.0) for band in BANDS}
        advance_tiles(pathogen, tiles, contacts, crowding, DAYS_PER_YEAR, fatality_scale=scale,
                      transmission_scale=transmission_scale.get(pathogen_id, 1.0),
                      care_collapse=(CAREGIVER_BANDS, sensitivity), draw=expected)
        forecast[pathogen_id] = {
            "infected": infected_total(records, pathogen_id),
            "expected_deaths_by_tile": _deaths(tiles)}
    return forecast
