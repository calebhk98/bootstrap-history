"""Complaint 649: a country has interest groups of its own, formed by the rule the home country's are (from the sectors of the
country's own bodies of people, read at its own pay) and pressing its own state; the home state sees none of them. The rules are
called on a registry and stand-in worlds, with no game."""

QUICK_TOPIC = True

from .harness import check

from sim.agents import budget
from sim.agents.api import (CONCESSION_PREFIX, ActorRecord, ActorRegistry, ActorsState, CastEntry, CountryProfile, CountryWorld, Sector,
							seed_cast, stratum_id)
from sim.agents.group import InterestGroup
from sim.agents.stratum_year import WAGES
from sim.agents.tuning_strata import STRATUM_WORKING_SHARE

from .country_state_world import StateWorld

WAGE = 10.0
MEMBERS = 1000.0
EXPECTED_WAGES = 2.0 * MEMBERS * STRATUM_WORKING_SHARE * WAGE      # the pay the stratum's trade had come to expect: twice the going pay
FORMS = [{"form": "poll_tax", "basis": "adult_labour_years", "rate": 0.2}]


class Answers:
	def pay_per_person_year(self, trade):
		return WAGE

	def society_output(self):
		return 1.0e6

	def need_floor_costs_per_person_year(self):
		return {"food": 5.0}

	def idle_hours_by_trade(self):
		return {"labourer": (0.0, 100.0)}

	def land_rent_curve(self, tiles=None):
		return []

	def working_people(self):
		return 5000.0

	def people_of_trade(self, trade):
		return 100.0

	def trade_value(self, direction):
		return 0.0


class Shared(StateWorld):
	def __init__(self):
		super().__init__()
		self.sector_table = {}

	def country_economy(self, country):
		return Answers()

	def sectors(self):
		return self.sector_table

	def scope_revenue(self, scope):
		return 1.0e6 * scope

	def state_reach(self):
		return 0.9

	def state_in_deficit(self):
		return False

	def concession_paid(self, line_name):
		return 0.0

	def founder_protection(self):
		return 0.0

	def lodge_blame(self, amount, text, year_gap, group_record):
		self.blamed = True

	def say(self, text):
		self.said = True

	def displacing_technique(self, trade):
		return None

	def land_rent_paid_by_tile(self):
		return {}


def build():
	registry = ActorRegistry(ActorsState(home_country="home"))
	entry = CastEntry(actor_id="government:far", country="far", kind="government", money=1.0e6,
					  params={"revenue_forms": list(FORMS)})
	profile = CountryProfile(country="far", population=24000.0, tax_share=0.1, extra={"state_revenue": list(FORMS)})
	profile.cohorts = {"children": 8000.0, "working_age": 12000.0, "elderly": 4000.0}
	seed_cast(registry, "home", [entry], {"home": CountryProfile(country="home"), "far": profile})
	poor = registry.add(stratum_id("far", "poor"), ActorRecord(kind="stratum", country="far", stratum="poor", name="the poor of far",
															   members=MEMBERS, plan={"trade": "labourer"}))
	poor.record.income_reference[WAGES] = EXPECTED_WAGES
	home_poor = registry.add(stratum_id("home", "peasants"), ActorRecord(kind="stratum", stratum="peasants", name="the peasants of home",
																	 members=MEMBERS, plan={"trade": "labourer"}))
	home_poor.record.income_reference[WAGES] = EXPECTED_WAGES
	shared = Shared()
	return registry, shared, CountryWorld(shared, registry.state.countries["far"], registry)


registry, shared, far = build()
sectors = far.sectors()
check("the country's falling incomes are read at its own pay: workers whose trade pays half what they expected are a sector",
	  list(sectors) == ["displaced_workers:poor"], list(sectors))
sector = sectors["displaced_workers:poor"]
expected_fall = EXPECTED_WAGES - MEMBERS * STRATUM_WORKING_SHARE * WAGE
check("...of the people of the country alone and the income they lost", abs(sector.lost_income - expected_fall) < 1e-6, sector.lost_income)
check("none of the loss is laid at the founder's door", sector.blame_share == 0.0)
check("the country's sectors are read once a year", far.sectors() is sectors)
check("...and the home stratum, whose pay fell as far, is not among them (only the country's own people are read)",
	  "displaced_workers:peasants" not in sectors and sector.members == MEMBERS * STRATUM_WORKING_SHARE, sector.members)

formed = registry.consider_groups(shared)
group = registry.actors.get("group:far:displaced_workers:poor")
check("a group of the country forms, named for the country, and answers to it",
	  formed == ["group:far:displaced_workers:poor"] and group is not None and group.record.country == "far", formed)
check("the home country's groups are those with no country: the foreign group is not among them",
	  [each.actor_id for each in registry.home_actors("interest_group")] == [] and registry.country_of(group) == "far")
check("the home state's own bans do not include a foreign group's", registry.prohibitions() == {})

group.record.claim = 321.0
claims = far.group_claims()
check("a country's state owes what it has undertaken to its own groups", claims == {CONCESSION_PREFIX + group.actor_id: 321.0}, claims)
lines = budget.concession_lines(claims)
check("the claim reaches the country's budget as a requisition line", [(line.name, line.money) for line in lines] == [(CONCESSION_PREFIX + group.actor_id, 321.0)])
check("a country with no group owes none", build()[2].group_claims() == {})

government = registry.actors["government:far"]
government.record.need = {CONCESSION_PREFIX + group.actor_id: 321.0}
government.record.unfunded = {CONCESSION_PREFIX + group.actor_id: 100.0}
check("what the country's state paid on a line is its need less what it left unfunded, from its own government",
	  far.concession_paid(CONCESSION_PREFIX + group.actor_id) == 221.0 and far.state_in_deficit())
government.record.unfunded = {}
check("a state that paid all it set out to is not in deficit", not far.state_in_deficit())
check("its revenue from a territory is its own", far.scope_revenue(0.5) == max(1e-9, 0.5 * far.state_revenue()))

# the group's year runs against the country's world: the compensation it receives is the country's state's payment
group.advance(far)
check("a group of the country takes its pull and claim from the country's own revenue and reach",
	  group.record.strength > 0.0 and group.record.claim > 0.0 and group.record.members == sector.members, (group.record.strength, group.record.claim))
check("the founder's log hears nothing of a foreign group, and no blame is lodged", not getattr(shared, "said", False) and not getattr(shared, "blamed", False))

# ---- the group's own record carries its country --------------------------------------------------------------
founded = InterestGroup.founded_by(Sector("falling_incomes", "poor", "the poor", "their earnings fell", 1.0, 2.0, 3.0, 1.0), "far")
check("a group founded for a country records the country; the home country's records none",
	  founded["country"] == "far" and InterestGroup.founded_by(Sector("falling_incomes", "poor", "the poor", "x", 1.0, 2.0, 3.0, 1.0))["country"] is None)

# ---- the home country's own readings leave the country's actors out ------------------------------------------
check("the home state reads only the bodies of people that answer to it",
	  [each.actor_id for each in registry.home_actors("stratum")] == [stratum_id("home", "peasants")]
	  and [each.actor_id for each in registry.of_kind("stratum")] == sorted([stratum_id("home", "peasants"), stratum_id("far", "poor")]))
