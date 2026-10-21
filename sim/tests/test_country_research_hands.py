"""Complaint 649: the hands a country's actor can put on research are the people its own labour markets hold in the trades of
the family (less what the country's other employers have), never the founder's pool; where the economy has no part for the
country the start gate refuses with a cause. The rules are called on stand-ins."""

QUICK_TOPIC = True

from .harness import check

from sim.agents import research_gate
from sim.agents.api import ActorRecord, ActorRegistry, ActorsState, CastEntry, CountryProfile, CountryWorld, seed_cast
from sim.agents.no_country_economy import NoCountryEconomy

from .country_state_world import StateWorld

PEOPLE = {"scholar": 5.0, "mason": 40.0, "smith": 12.0}
EMPLOYED_ELSEWHERE = {"smith": 2.0}
HOME_POOL = 1000.0     # the founder's pool, which a country's actor must not draw on


class Answers:
	def people_of_trade(self, trade):
		return PEOPLE.get(trade, 0.0)


class Shared(StateWorld):
	hands = {}

	def country_economy(self, country):
		return Answers()

	def research_trades(self, family):
		return ["scholar"] if family == "scholar" else ["mason", "smith"]

	def free_fte(self, trade, actor_id=None):
		return HOME_POOL


class NoPart(Shared):
	def country_economy(self, country):
		return None


def build(shared):
	registry = ActorRegistry(ActorsState(home_country="home"))
	entry = CastEntry(actor_id="government:far", country="far", kind="government", money=1.0, params={})
	seed_cast(registry, "home", [entry], {"home": CountryProfile(country="home"), "far": CountryProfile(country="far", population=24000.0)})
	registry.staff_fte_in_country = lambda trade, country, actor_id: EMPLOYED_ELSEWHERE.get(trade, 0.0)
	return CountryWorld(shared, registry.state.countries["far"], registry), registry


world, registry = build(Shared())
actor = registry.actors["government:far"]
actor.workforce.update({"mason": 3.0})
check("scholar hands are the scholars the country's labour markets hold, plus the actor's own staff in the trade",
	  world.research_hands(actor, "scholar") == PEOPLE["scholar"], world.research_hands(actor, "scholar"))
check("craft hands are the markets' people in the craft trades less the other employers', plus the actor's staff",
	  world.research_hands(actor, "craft") == 3.0 + PEOPLE["mason"] + (PEOPLE["smith"] - EMPLOYED_ELSEWHERE["smith"]),
	  world.research_hands(actor, "craft"))
check("the founder's pool is not counted", world.research_hands(actor, "craft") < HOME_POOL)

no_part_world, no_part_registry = build(NoPart())
no_part_actor = no_part_registry.actors["government:far"]
try:
	no_part_world.research_hands(no_part_actor, "scholar")
	raised = None
except NoCountryEconomy as error:
	raised = error.country
check("a country the economy has no part for refuses for its hands, naming the country", raised == "far", raised)

node = {"sch": 2, "art": 0, "pre": []}


class GateWorld(NoPart):
	def __init__(self):
		super().__init__()
		self.nodes["idea"] = node

	def purchasable_substitute_discount(self):
		return 0.9

	def unsold_materials(self, actor, node_id):
		return []


gate_world, gate_registry = build(GateWorld())
found = research_gate.refusals(gate_registry.actors["government:far"], "idea", gate_world)
check("the start gate refuses with the cause no_country_hands where the country has no record of its people",
	  [refusal.cause for refusal in found] == ["no_country_hands"] and found[0].facts["country"] == "far", [(r.cause, r.facts) for r in found])
