"""Complaint 626: a state's tax rates are its own. The civilisation file's rates are copied into the state's record
once, at setup; every later year reads the record. A rate the state sets changes what a form yields, an AI state
raises one under a shortfall (test_state_fiscal_response), and the state's rates survive a save."""
QUICK_TOPIC = True

import copy

from .harness import check

from sim.agents import cast, government_levers, revenue
from sim.agents.api import ActorRecord, ActorRegistry, ActorsState, seed_cast
from sim.economy import taxes
from sim.engine.state import deserialize_state, serialize_state

from .agents_fake_world import FakeWorld

POLL = {"form": "poll_tax", "basis": "adult_labour_years", "rate": 0.02}
DUTY = {"form": "import_duty", "basis": "imports_value", "rate": 0.025}
WORKING_AGE, LABOUR_YEAR, IMPORTS = 2.0e6, 900.0, 6.0e9


class Bases(FakeWorld):
	"""A country that answers two bases from numbers; it reads its forms from a government's record."""

	def __init__(self, record):
		super().__init__()
		self.record = record

	def revenue_forms(self):
		return government_levers.revenue_forms(self.record)

	def national_people(self, trade):
		return WORKING_AGE

	def soldiers_under_arms(self):
		return 0.0

	def pay_per_person_year(self, trade):
		return LABOUR_YEAR

	def trade_value(self, direction):
		return IMPORTS if direction == "in" else 0.0

	def collectible_share(self, tiles=None):
		return 1.0


def yields(world):
	return {assessed.form: assessed for assessed in revenue.assess(world)}


# ---- the file's rate is read at setup only ----------------------------------------------------------------------
civ = {"id": "home", "name": "Home", "state_revenue": [dict(POLL), dict(DUTY)]}
home_country, entries, profiles = cast.cast_from_civilisations(civ, [])
registry = ActorRegistry(ActorsState(home_country=home_country))
seed_cast(registry, home_country, entries, profiles)
record = registry.government("home").record
check("setup copies the file's forms into the state's record", record.revenue_forms == civ["state_revenue"], record.revenue_forms)
civ["state_revenue"][0]["rate"] = 0.5
civ["state_revenue"].pop()
check("the file is not read again: a later change to it does not reach the state",
	  [form["rate"] for form in government_levers.revenue_forms(record)] == [0.02, 0.025], government_levers.revenue_forms(record))

# ---- a rate the state sets changes what the form yields --------------------------------------------------------------
world = Bases(record)
before = yields(world)
check("the starting rate yields the rate times the base",
	  abs(before["poll_tax"].money - 0.02 * WORKING_AGE * LABOUR_YEAR) < 1e-6 * before["poll_tax"].money, before["poll_tax"].money)
record.revenue_forms[0]["rate"] = 0.04
after = yields(world)
check("a rate in the state's own record doubles the yield of a form with the same base",
	  abs(after["poll_tax"].money - 2.0 * before["poll_tax"].money) < 1e-6 * before["poll_tax"].money, (before["poll_tax"].money, after["poll_tax"].money))
check("a form the state did not change yields as it did", after["import_duty"].money == before["import_duty"].money)

# ---- the economy collects at the state's rates, not the file's ------------------------------------------------------
setup_forms = taxes.forms_from_civ_data([dict(POLL, basis="harvest"), dict(DUTY)])
held = taxes.with_rates(setup_forms, [("import_duty", 0.1)])
check("the economy's coin form is collected at the rate the state holds",
	  [form.rate for form in held] == [0.02, 0.1] and [form.rate for form in setup_forms] == [0.02, 0.025],
	  ([form.rate for form in held], [form.rate for form in setup_forms]))

# ---- the state's rates are saved ----------------------------------------------------------------------------------------
saved = ActorsState(home_country="home")
saved.records["government:home"] = ActorRecord(kind="government", revenue_forms=copy.deepcopy(record.revenue_forms),
												levers={"revenue": {"import_duty": {"rate": 0.07}}})
loaded = deserialize_state(serialize_state(saved), ActorsState).records["government:home"]
check("a state's rates survive save and load", loaded.revenue_forms == record.revenue_forms
	  and government_levers.revenue_forms(loaded)[1]["rate"] == 0.07, government_levers.revenue_forms(loaded))
