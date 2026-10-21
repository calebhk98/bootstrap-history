"""Complaint 649: what a country's state is asked to give the clients of its own is the home rule at the country's pay,
reach, size and real output per head; with no client it gives nothing, and where the economy has no pay or output for the
country it refuses with a cause and grants nothing. The rules are called on built inputs and stand-ins."""

QUICK_TOPIC = True

from types import SimpleNamespace

from .harness import check

from sim.agents import patronage
from sim.agents.api import ActorRegistry, ActorsState, CastEntry, CountryProfile, CountryWorld, seed_cast
from sim.agents.no_country_economy import NoCountryEconomy
from sim.engine.agents_port_patronage import PatronageView
from sim.engine.economy_production import ProductionMixin

from .country_state_world import StateWorld

TERMS = {"base_hours": 100.0, "population_scale": 4.0, "exponent": 0.5, "governance_scale": 25.0}
BASE_PAY = 10.0       # money for a person-year of unskilled work in the country
HOURS = StateWorld.hours_per_person_year
OUTPUT_PER_HEAD, REACH = 1.5, 0.9

# ---- the rule --------------------------------------------------------------------------------------------
direct = patronage.ask(1000.0, 2.0, 0.5, 4.0, 0.5, 25.0, 25.0, 1.1)
check("the ask is the base at the output per head and reach, the size to the exponent, the governance and the reputation",
	  abs(direct - 1000.0 * 2.0 * 0.5 * 2.0 * 2.0 * 1.1) < 1e-9, direct)
check("a negative governance adds nothing", patronage.ask(1.0, 1.0, 1.0, 1.0, 1.0, -5.0, 25.0, 1.0) == 1.0)
two = patronage.ask_of_country(TERMS, 0.05, OUTPUT_PER_HEAD, REACH, [(0.0, 1.0), (25.0, 1.2)])
one_each = [patronage.ask(100.0 * 0.05, OUTPUT_PER_HEAD, REACH, 4.0, 0.5, governance, 25.0, reputation) for governance, reputation in [(0.0, 1.0), (25.0, 1.2)]]
check("a country's ask is its clients' asks added, each at the country's pay for an hour", abs(two - sum(one_each)) < 1e-9, (two, one_each))
check("a country with no client is asked for nothing", patronage.ask_of_country(TERMS, 0.05, OUTPUT_PER_HEAD, REACH, []) == 0.0)


# ---- the country's world -------------------------------------------------------------------------------------
class Answers:
	def __init__(self, pay):
		self.pay = pay

	def pay_per_person_year(self, trade):
		return self.pay


class Shared(StateWorld):
	clients = [(0.0, 1.0), (25.0, 1.2)]
	pay = BASE_PAY
	per_head = OUTPUT_PER_HEAD

	def patron_clients(self, country):
		return list(self.clients)

	def state_funding_terms(self, people):
		return dict(TERMS)

	def country_output_per_head(self, country, opening_people, people):
		return self.per_head

	def country_economy(self, country):
		return None if self.pay is None else Answers(self.pay)


def build(shared):
	registry = ActorRegistry(ActorsState(home_country="home"))
	entry = CastEntry(actor_id="government:far", country="far", kind="government", money=1.0e6, params={})
	seed_cast(registry, "home", [entry], {"home": CountryProfile(country="home"), "far": CountryProfile(country="far", population=24000.0)})
	world = CountryWorld(shared, registry.state.countries["far"], registry)
	world.state_reach = lambda: REACH
	return world, registry


world, registry = build(Shared())
expected = patronage.ask_of_country(TERMS, BASE_PAY / HOURS, OUTPUT_PER_HEAD, REACH, Shared.clients)
check("a country's patron ask is its clients' at its own pay, reach and real output per head", abs(world.patron_ask() - expected) < 1e-9 and expected > 0.0, world.patron_ask())


class NoClients(Shared):
	clients = []


check("a country none of whose seats runs the mechanic is asked for nothing", build(NoClients())[0].patron_ask() == 0.0)


class NoOutput(Shared):
	per_head = None


class NoPart(Shared):
	pay = None


def refuses(shared):
	try:
		build(shared)[0].patron_ask()
	except NoCountryEconomy as error:
		return error.country
	return None


check("where the economy has no real output per head for the country it refuses, naming it", refuses(NoOutput()) == "far")
check("where the economy has no part for the country it refuses", refuses(NoPart()) == "far")

refused_world, refused_registry = build(NoOutput())
state = refused_registry.actors["government:far"]
state.pay_patron(1.0, refused_world)
check("a state whose ask refuses grants nothing", state.record.patron_grant == 0.0)
funded_world, funded_registry = build(Shared())
funded = funded_registry.actors["government:far"]
funded.pay_patron(1.0, funded_world)
check("a state that can pay grants what it is asked, within its purse", abs(funded.record.patron_grant - min(expected, 1.0e6)) < 1e-9, funded.record.patron_grant)
unpaid = build(Shared())
unpaid[1].actors["government:far"].pay_patron(0.5, unpaid[0])
check("a state that left need unpaid funds nobody", unpaid[1].actors["government:far"].record.patron_grant == 0.0)


# ---- the engine's side ---------------------------------------------------------------------------------------
class Engine:
	STATE_FUNDING_BASE_LABOUR_HOURS = 100.0
	STATE_FUNDING_POP_SCALE_EXPONENT = 0.4
	STATE_FUNDING_GOV_QUALITY_SCALE = 25.0
	POP_SCALE_FLOOR = 0.05
	DEFAULT_POPULATION_100AD = 1000.0

	def patron_clients(self, country):
		return [("a", 3.0, 1.1), ("b", 0.0, 1.0)]


view = PatronageView()
view._sim = Engine()
check("the funding terms carry the size of the country against the reference one, floored",
	  view.state_funding_terms(500.0)["population_scale"] == 0.5 and view.state_funding_terms(1.0)["population_scale"] == Engine.POP_SCALE_FLOOR)
check("the clients a country's state is asked about are the seats' governance and reputation", view.patron_clients("far") == [(3.0, 1.1), (0.0, 1.0)])


class FakeEconomy:
	def __init__(self, units, prices, baseline, traded):
		self.opening = (units, prices)
		self.baseline, self.traded = baseline, traded

	def agent_opening_basket(self, country):
		return self.opening

	def agent_volume_baseline(self, country):
		return self.baseline

	def agent_traded_volumes(self, country):
		return self.traded


def output_per_head(economy, opening_people, people):
	view._sim = SimpleNamespace(economy=economy)
	return view.country_output_per_head("far", opening_people, people)


basket = ({"grain": 100.0, "cloth": 10.0}, {"grain": 1.0, "cloth": 5.0})
check("a country that trades what it did in its baseline year has the opening's output per head",
	  abs(output_per_head(FakeEconomy(*basket, {"grain": 80.0, "cloth": 8.0}, {"grain": 80.0, "cloth": 8.0}), 1000.0, 1000.0) - 1.0) < 1e-9)
check("trading more of what it opened with raises it, and more people lower it per head",
	  abs(output_per_head(FakeEconomy(*basket, {"grain": 80.0, "cloth": 8.0}, {"grain": 160.0, "cloth": 16.0}), 1000.0, 1000.0) - 2.0) < 1e-9
	  and abs(output_per_head(FakeEconomy(*basket, {"grain": 80.0, "cloth": 8.0}, {"grain": 160.0, "cloth": 16.0}), 1000.0, 2000.0) - 1.0) < 1e-9)
check("a country the economy has no basket for has no output per head (None)",
	  output_per_head(FakeEconomy(*basket, {}, {}), 1000.0, 1000.0) is not None and output_per_head(SimpleNamespace(agent_opening_basket=lambda country: None), 1.0, 1.0) is None)
check("...nor one with no people", output_per_head(FakeEconomy(*basket, {}, {}), 1000.0, 0.0) is None)


# ---- the seat of another country is paid by that country's state ---------------------------------------------
class Funding:
	"""What `state_funding` reads: the acting seat's country, the governments' records and the seats a state funds."""
	state_funding = ProductionMixin.state_funding

	def __init__(self, acting, seats_funded, grant):
		self.civ = {"id": "home"}
		self.state = SimpleNamespace(
			acting_seat=acting, seats={"founder": SimpleNamespace(country=None), "visitor": SimpleNamespace(country="far"),
									   "friend": SimpleNamespace(country="far")},
			actors=SimpleNamespace(records={"government:home": SimpleNamespace(patron_grant=500.0),
											"government:far": SimpleNamespace(patron_grant=grant)}))
		self._funded = seats_funded

	def patron_clients(self, country):
		return [(seat, 0.0, 1.0) for seat in self._funded]


check("the home seat is paid the home state's grant", Funding("founder", [], 90.0).state_funding() == 500.0)
check("a seat of another country is paid that country's grant, shared among the seats its state funds",
	  Funding("visitor", ["visitor", "friend"], 90.0).state_funding() == 45.0)
check("a seat of another country its state does not fund is paid nothing", Funding("visitor", ["friend"], 90.0).state_funding() == 0.0)
