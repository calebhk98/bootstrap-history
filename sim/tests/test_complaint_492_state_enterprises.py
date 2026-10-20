"""Complaint 492: a state's monopolies and arsenals are plants it owns, run through the same business object a firm uses.

A monopoly's takings are the state's revenue; a plant with no crew or no inputs makes nothing; an arsenal's output is
goods the state holds for its army instead of selling them."""

QUICK_TOPIC = True

from .harness import check

from sim.agents import budget, firm_entry, state_enterprises
from sim.agents.api import ActorRecord, Government

from .agents_fake_world import FakeWorld, make_node

OPENING_MONEY = 1000.0
TAKINGS = 20000.0
UPKEEP = 60.0


class StateWorld(FakeWorld):
	def __init__(self):
		super().__init__()
		self.state = Government("government:home", ActorRecord(kind="government", money=OPENING_MONEY))
		self.nodes["salt_works"] = make_node("salt_works", hours=4000.0, revenue=TAKINGS, upkeep=UPKEEP, makes=["salt_kg"])
		self.nodes["arsenal"] = make_node("arsenal", hours=2000.0, revenue=TAKINGS, upkeep=UPKEEP, makes=["weapons_kg"])
		self.baseline = {"salt_works", "arsenal"}
		self.free_people["labourer"] = 100.0
		self.prices = {"brine_kg": 1.0}

	def government(self):
		return self.state

	def commodity_of(self, material):
		return material


def state_with(monopolies=(), enterprises=(), money=OPENING_MONEY):
	world = StateWorld()
	world.state.record.state_monopolies = set(monopolies)
	world.state.record.state_enterprises = set(enterprises)
	world.state.money = money
	return world, world.state


# ---- a monopoly is a plant the state opens and runs -----------------------------------------------------
world, state = state_with(monopolies=["salt_kg"])
state_enterprises.open_enterprises(state, world)
check("a state holding the salt monopoly opens a plant of the entry that makes salt",
	  list(state.business.operating()) == ["salt_works"], list(state.business.operating()))
state_enterprises.open_enterprises(state, world)
check("opening again adds no second plant", len(state.business.plants) == 1)
state_enterprises.run(state, world)
crew = world.concern_staff("salt_works")["labourer"]
check("the plant's crew is taken from the labour pool", state.workforce.get("labourer") == crew, state.workforce)
check("the state's takings are the plant's takings", abs(state.record.enterprise_takings - TAKINGS) < 1e-6,
	  state.record.enterprise_takings)
check("the monopoly revenue read for the budget is those takings",
	  state_enterprises.monopoly_revenue(state.record) == state.record.enterprise_takings)
wages = world.concern_wage_bill("salt_works")
management = firm_entry.management_cost(world, "salt_works", 1.0)
check("the purse gained takings less upkeep, wages and a manager's hours",
	  abs(state.money - (OPENING_MONEY + TAKINGS - UPKEEP - wages - management)) < 1e-6, state.money)
state.sell_output(world)
check("what the plant made went to market", world.sales == [(state.actor_id, "salt_kg", 1.0)], world.sales)

# ---- without a crew nothing is made -----------------------------------------------------------------------
world, state = state_with(monopolies=["salt_kg"])
world.free_people["labourer"] = 0.0
state_enterprises.open_enterprises(state, world)
state_enterprises.run(state, world)
state.sell_output(world)
management = firm_entry.management_cost(world, "salt_works", 1.0)
check("with nobody to hire the state's works takes nothing and pays no wages, only upkeep and a manager",
	  state.record.enterprise_takings == 0.0 and abs(state.money - (OPENING_MONEY - UPKEEP - management)) < 1e-6,
	  (state.record.enterprise_takings, state.money))
check("...and puts no goods on the market", all(tonnes == 0.0 for _seller, _material, tonnes in world.sales), world.sales)

# ---- without inputs nothing is made; stores supply them -----------------------------------------------------
world, state = state_with(monopolies=["salt_kg"], money=0.0)
world.nodes["salt_works"]["inputs"] = {"brine_kg": 10.0}
state_enterprises.open_enterprises(state, world)
state_enterprises.run(state, world)
check("a works with no inputs held and no money to buy them makes nothing",
	  state.record.enterprise_takings == 0.0 and state.business.crew_found_of("salt_works") == 0.0,
	  state.record.enterprise_takings)
world, state = state_with(monopolies=["salt_kg"])
world.nodes["salt_works"]["inputs"] = {"brine_kg": 10.0}
state.record.stores["brine_kg"] = 10.0
state_enterprises.open_enterprises(state, world)
state_enterprises.run(state, world)
check("inputs in the stores are consumed and the works runs", state.record.stores["brine_kg"] == 0.0
	  and state.business.crew_found_of("salt_works") == 1.0 and state.record.enterprise_takings > 0.0, state.record.stores)
world, state = state_with(monopolies=["salt_kg"])
world.nodes["salt_works"]["inputs"] = {"brine_kg": 10.0}
state_enterprises.open_enterprises(state, world)
state_enterprises.run(state, world)
check("inputs the stores lack are bought at the market's price with the purse",
	  world.purchases == [(state.actor_id, "brine_kg", 10.0)] and state.business.crew_found_of("salt_works") == 1.0,
	  world.purchases)

# ---- an arsenal's output is goods the state holds ----------------------------------------------------------
world, state = state_with(enterprises=["arsenal"])
state_enterprises.open_enterprises(state, world)
check("a declared enterprise is opened too", list(state.business.operating()) == ["arsenal"])
state.record.material_need = {"weapons_kg": 0.4}
state_enterprises.run(state, world)
state.sell_output(world)
check("the arsenal's goods go to the stores up to what the army lines draw",
	  abs(state.record.stores["weapons_kg"] - 0.4) < 1e-9, state.record.stores)
check("...and only the rest is sold", len(world.sales) == 1 and abs(world.sales[0][2] - 0.6) < 1e-9, world.sales)
line = budget.Line("army", "requisition", {}, 0.0, {"weapons_kg": 0.5}, 1.5)
drawn = state.draw_stores([line], world)[0]
check("the army line then draws on the stores before buying",
	  abs(drawn.materials["weapons_kg"] - 0.1) < 1e-9 and state.record.stores["weapons_kg"] < 1e-9, drawn.materials)

# ---- a state does not levy its own works ----------------------------------------------------------------
world, state = state_with(monopolies=["salt_kg"])
asked = []
world.government_actor = type("Taxman", (), {"collect": lambda self, actor, takings, w: asked.append(actor) or 0.0})()
state_enterprises.open_enterprises(state, world)
state_enterprises.run(state, world)
check("the state's own plant is not assessed for the state's levy", asked == [], asked)

# ---- an entry with no takings is not opened for a monopoly -------------------------------------------------
world, state = state_with(monopolies=["salt_kg"])
world.nodes["salt_works"]["rev"] = 0.0
check("a monopoly whose only entry earns nothing opens no plant", state_enterprises.open_enterprises(state, world) == [])
