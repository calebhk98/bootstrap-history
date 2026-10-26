"""The nation's people by age: the opening, the counts others read, and what cuts them (a shock, a death, settlers)."""
from sim.actors.api import ScaleStrata
from sim.agents import api as agents_api
from sim.hazards.api import RecordWorldEvent
from sim.refusal import Refusal
from sim.reporting.api import RecordEvent
from sim.unit_conversions import PERCENT_SCALE
from sim.world import demography

from . import rules
from .constants import DEFAULT_POPULATION_100AD, POP_SCALE_FLOOR
from .people import People


class Counts:

    def _bands(self):
        """The three age bands as they stand."""
        world = self.world
        return People(world.pop_children, world.pop_working_age, world.pop_elderly)

    def _store(self, children, working_age, elderly):
        world = self.world
        world.pop_children = float(children)
        world.pop_working_age = float(working_age)
        world.pop_elderly = float(elderly)

    # ---- views ----

    def population(self):
        """The nation's people in the three age bands (`total`, `adult_equivalents`, `nutrition_ratio(food)`)."""
        return self._bands()

    def population_total(self):
        return self._bands().total

    def working_age(self):
        return self.world.pop_working_age

    def pop_scale(self):
        """The nation's people against the reference population, never below the floor."""
        return rules.pop_scale(self._bands().total, DEFAULT_POPULATION_100AD, POP_SCALE_FLOOR)

    def default_population(self):
        """The population the reference tables (national outputs of the tracked commodities) are stated for."""
        return DEFAULT_POPULATION_100AD

    def population_change_last_year(self):
        return self.world.population_change_last_year

    def yearly_record(self):
        """One dict per simulated year: year, population, births, deaths, nutrition_ratio."""
        return self.world.yearly_record

    # ---- commands ----

    def open_population(self, command):
        """The age structure the civilisation's size settles into when fed exactly at its need. The seed comes from the
        civilisation's id; nothing draws from it."""
        civilisation = self.needs.civilisation()
        stationary = demography.Population.stationary(
            float(civilisation.get("population", DEFAULT_POPULATION_100AD)),
            seed=rules.population_seed(civilisation.get("id", "civ")))
        self._store(stationary.children, stationary.working_age, stationary.elderly)

    def cut_population(self, command):
        """Cut the cohorts by `share` of the whole, unevenly by age, so the population-weighted loss is `share` exactly and two
        losses of equal headcount diverge afterwards by who survived. The age pattern is the starvation vulnerability the cohort
        model declares for its own nutrition-driven deaths (sim/world/demography.py, after Watkins and Menken 1985, for caloric
        shortfall). Reusing it for disease and war deaths is a temporary heuristic: the direction (the young and the old die more)
        is general, the magnitudes are not sourced for these causes. It retires when a hazard is expressed in calories or
        carries its own age pattern (docs/architecture/WIRING_MILESTONE_4.md, section 1.3)."""
        people = self._bands()
        rules.cut_cohorts(people, command.share, demography.STARVATION_VULNERABILITY_CHILD,
                          demography.STARVATION_VULNERABILITY_WORKING_AGE, demography.STARVATION_VULNERABILITY_ELDERLY)
        self._store(people.children, people.working_age, people.elderly)

    def send_settlers(self, command):
        people = self._bands()
        self._store(people.children, people.working_age - command.people, people.elderly)

    def note_population_change(self, command):
        self.world.population_change_last_year = command.change

    def kill_people(self, command):
        """`share` of a country's people die: the home people by cohort, a partner's by its strata."""
        if not 0.0 <= command.share <= 1.0:
            return Refusal("bad_share", "a death share is between 0 and 1, not %r" % (command.share,))
        before = self._people_of(command.country)
        if command.country == self.needs.civilisation()["id"]:
            self.cut_population(command)
        else:
            self.needs.send(ScaleStrata(command.country, command.share))
        return self.needs.send(RecordWorldEvent(command.kind, actors=(command.country,), tiles=tuple(command.tiles),
                                                cause=command.cause,
                                                facts=dict(died=before - self._people_of(command.country), **command.facts)))

    def _people_of(self, country):
        """How many people the country holds: the home people, or a partner's strata."""
        if country == self.needs.civilisation()["id"]:
            return float(self._bands().total)
        return sum(stratum["members"] for stratum in self.needs.country_strata[country])

    def add_captives(self, command):
        return agents_api.add_captives(self.needs.legacy_actor_registry(), command.winner, command.people)

    def refresh_demographic_indexes(self, command):
        self._refresh_indexes(command.year)

    def _refresh_indexes(self, year):
        """Say why the wage bill moved, if it moved enough to be worth saying: a shock's effects are visible at once, not a
        step later."""
        terms = self.needs.wage_index_terms()
        premium, shortfall = rules.wage_cascade(self.needs.wage_index(), terms["base"], terms["elasticity"])
        if rules.wage_cascade_due(premium, year, self.world.said_wage_cascade):
            self.world.said_wage_cascade = year
            self.needs.send(RecordEvent.in_year(year, "wage_cascade", "population still %d%% below trend: wages "
                "(and anything billed in them) are running "
                "%d%% above normal for here, and will ease "
                "as the population does"
                % (round(shortfall * PERCENT_SCALE), round(premium)), population_below_trend_percent=round(shortfall * PERCENT_SCALE), wage_premium_percent=round(premium)))
