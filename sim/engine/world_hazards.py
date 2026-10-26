"""Base-rate shocks for every country in the game, and famine watch, as yearly world phases (Complaint 493).

The kinds, rates and losses are data (data/world/world_hazards.json). A country's draw is a hash of the game's
seed, the country, the kind and the year, so it does not move when another country joins and uses no shared
dice. A hit cuts the country's people (the home society by its cohort shock, a partner by its strata) and
writes a record to the world event log (sim/engine/world_events.py); every seat's log carries a line."""
import random

from sim.refusal import LogLine

from . import mod_effects, world_events, world_hazard_data
from sim.reporting.api import RecordEvent


def countries_in_game(sim):
    """The home country, then every partner whose people live in the agent economy, sorted."""
    return [sim.civ["id"]] + list(sim.partners_in_agent_economy())


def draw(sim, country, kind, year):
    """The country's uniform draw for one kind in one year."""
    return random.Random("%s|%s|%s|%d" % (sim._farm_year_weather_seed(0), country, kind, year)).random()


def people_of(sim, country):
    return mod_effects.people_of(sim, country)


def hit(sim, country, hazard):
    """Apply one hazard to one country: people lost, a record in the log, a line in every playing seat's log."""
    entry = mod_effects.BASE_EFFECTS.kill_people(sim, country, hazard["population_loss"], hazard["cause"], kind=hazard["kind"],
                                                 population_loss=hazard["population_loss"])
    year, died = entry["year"], entry["facts"]["died"]
    for seat_id in sim.playing_seats():
        sim.send(RecordEvent.from_line(LogLine(
            "world_hazard", "%s in %s: about %d people die" % (hazard["cause"], country, round(died)),
            hazard=hazard["kind"], country=country, died=died), seat_id))
    return entry


def world_hazards_phase(sim, seats):
    """Each country draws each kind once; a hit applies to that country alone."""
    if not sim.events:
        return
    year = sim.state.scenario.year
    for country in countries_in_game(sim):
        for hazard in world_hazard_data.hazards():
            if draw(sim, country, hazard["kind"], year) < hazard["annual_chance"]:
                hit(sim, country, hazard)


def famine_watch_phase(sim, seats):
    """Write a famine record for each country whose people leave a large share of their food need unmet."""
    threshold = world_hazard_data.famine_food_shortfall()
    for country in countries_in_game(sim):
        strata = mod_effects.strata_of(sim, country)
        people = sum(actor.record.members for actor in strata)
        if people <= 0.0:
            continue
        shortfall = sum(actor.record.members * actor.record.shortfall.get("food", 0.0) for actor in strata) / people
        if shortfall >= threshold:
            mod_effects.BASE_EFFECTS.record_event(sim, "famine", "food unmet", actors=[country],
                                                  food_shortfall=shortfall, people=people)


class WorldHazardsMixin:
    """The world phases and the yearly checks as `Sim` methods, so the year calls them as it calls every phase."""

    def step_world_hazards(self, seats):
        return world_hazards_phase(self, seats)

    def step_famine_watch(self, seats):
        return famine_watch_phase(self, seats)

    def check_yearly_world(self):
        """The yearly invariants, run in every game of more than one country."""
        from . import invariants
        if len(countries_in_game(self)) > 1:
            invariants.check_yearly_invariants(self)
