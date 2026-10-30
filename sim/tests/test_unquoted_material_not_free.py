"""Complaint 663: a material no market quotes is not on sale, and a state's need for it is unmet, not free.
`material_cost` says "not on sale" as None; each budget line that buys goods books the unbuyable tonnes on the line
(`Line.unbuyable`) and prices only what is on sale; the state records them as unmet goods, an army equipped short
of iron shrinks, and a state with unmet goods lends nothing. Each caller is called on a stand-in world; no game is played."""

QUICK_TOPIC = True

import types

from .harness import check

from sim.agents import budget, budget_lines, budget_works, government_levers, state_enterprises
from sim.agents.api import ActorRecord, Government
from sim.agents.budget_line import Line
from sim.actors.world_budget import BudgetView
from sim.tests.world_stand_in import fake_needs

from .agents_fake_world import FakeWorld

IRON = budget.EQUIPMENT_MATERIAL
GRAIN = budget_lines.DOLE_MATERIAL
IRON_PRICE = 10.0
GRAIN_PRICE = 4.0
SHIP_PRICE = 10000.0
WAGE = 100.0


class Market(FakeWorld):
	"""A world whose market quotes only what `quoted` names; every other material is not on sale."""

	def __init__(self, quoted):
		super().__init__()
		self.prices = dict(quoted)
		self.state = Government("government:home", ActorRecord(kind="government", money=1.0e6))

	def commodity_of(self, material):
		return material

	def material_cost(self, material, tonnes):
		return self.prices[material] * tonnes if material in self.prices else None

	def pay_per_person_year(self, trade):
		return WAGE

	def government(self):
		return self.state

	def equipment_kg_per_soldier(self):
		return 20.0

	def urban_population(self):
		return 10000.0

	def subsistence_kg_per_person_year(self):
		return 200.0

	def national_people(self, trade):
		return 1.0e6

	def threat_pressure(self):
		return 1.0

	def territory(self):
		return types.SimpleNamespace(frontier_km=600.0, coast_km=300.0, road_km=0.0)

	def trade_exists(self, trade):
		return True

	def concern_inputs(self, entry_key):
		return {IRON: 5.0}


class Shipyard(Market):
	def fleet_goods(self, holder_id=None):
		return [{"material": "galley", "life": 20.0, "held": 0.0, "crew": {"sailor": 10.0}},
				{"material": "cog", "life": 20.0, "held": 0.0, "crew": {"sailor": 10.0}}]


# ---- the home market port: no quote is no price, not a free one -----------------------------------------------
def port_with(quote):
	return types.SimpleNamespace(needs=fake_needs(material_purchase_cost=lambda material, tonnes: quote))


check("the home port prices a quoted material at the quote", BudgetView.material_cost(port_with((42.0, "home")), IRON, 3.0) == 42.0)
check("the home port answers not on sale (None) for a material nobody quotes",
	  BudgetView.material_cost(port_with(None), IRON, 3.0) is None)

# ---- the army's equipment ----------------------------------------------------------------------------------------
bare = Market({})
army, unsold_army = budget.army_line(Market({IRON: IRON_PRICE}), 1000.0)[0], budget.army_line(bare, 1000.0)[0]
check("an army's iron on sale is priced and not unbuyable", army.material_cost > 0.0 and not army.unbuyable, army)
check("an army's iron nobody sells is booked unbuyable, in the tonnes the army wears, and costs nothing to buy",
	  unsold_army.unbuyable == {IRON: 1000.0 * 20.0 / 1000.0} and unsold_army.material_cost == 0.0 and not unsold_army.materials,
	  unsold_army)
check("an army with its iron unbuyable is supplied none of it", budget.supplied_share(unsold_army) == 0.0 and budget.supplied_share(army) == 1.0)
check("an army that cannot be supplied shrinks as an unfunded one does",
	  budget.army_next_year(1000.0, 1000.0, budget.supplied_share(unsold_army)) < 1000.0)

# ---- the dole and the campaign (grain) -----------------------------------------------------------------------------
dole = budget_lines.dole_line(bare)[0]
check("a dole of grain nobody sells is unbuyable, not free", dole.unbuyable != {} and dole.material_cost == 0.0 and not dole.materials, dole)
check("a dole of grain on sale is priced", budget_lines.dole_line(Market({GRAIN: GRAIN_PRICE}))[0].material_cost > 0.0)
campaign = budget_works.campaign_line(bare, 1000.0)[0]
check("a campaign's grain nobody sells is unbuyable, not free", campaign.unbuyable != {} and campaign.material_cost == 0.0, campaign)

# ---- a mandate (a lever's purchase) ---------------------------------------------------------------------------------
record = ActorRecord(kind="government", levers={government_levers.MANDATE: {GRAIN: 50.0}})
mandate = government_levers.lever_lines(record, bare)[0]
check("a mandate for a material nobody sells is unbuyable, not free", mandate.unbuyable == {GRAIN: 50.0} and mandate.material_cost == 0.0, mandate)
check("a mandate for a material on sale is priced",
	  government_levers.lever_lines(record, Market({GRAIN: GRAIN_PRICE}))[0].material_cost == 50.0 * GRAIN_PRICE)

# ---- the navy: a ship type with no seller is not the cheapest ----------------------------------------------------------
for_sale = Shipyard({"cog": SHIP_PRICE})
for_sale.state.record.levers = {"navy": 4.0}
navy = budget_lines.navy_line(for_sale)[0]
check("the navy buys the ship type that is on sale", set(navy.materials) == {"cog"} and not navy.unbuyable, navy)
none_sold = Shipyard({})
none_sold.state.record.levers = {"navy": 4.0}
navy = budget_lines.navy_line(none_sold)[0]
check("with no ship type on sale the navy's ships are unbuyable, not free",
	  navy.material_cost == 0.0 and sum(navy.unbuyable.values()) > 0.0 and not navy.materials, navy)

# ---- stores supply what the market will not ---------------------------------------------------------------------------------
state = Government("government:home", ActorRecord(kind="government", money=1.0e6))
state.record.stores = {GRAIN: 30.0}
drawn = state.draw_stores([Line("dole", "requisition", unbuyable={GRAIN: 100.0})], bare)[0]
check("what the stores hold meets unbuyable need first", drawn.unbuyable == {GRAIN: 70.0} and state.record.stores[GRAIN] == 0.0, drawn)

# ---- the consequence: unmet goods are recorded and a state with any lends nothing ---------------------------------------------
check("the unmet goods of the lines are the unbuyable tonnes by line name",
	  budget.unmet_goods([unsold_army, Line("roads", "requisition")]) == {"army": 20.0})
check("a line's unbuyable tonnes are part of what its own plants are asked to make",
	  state_enterprises.needs_of([unsold_army]) == {IRON: 20.0})
state = Government("government:home", ActorRecord(kind="government", money=1.0e6))
check("a state with no unmet goods and no unfunded need can lend", not state.cannot_meet_own_need())
state.record.unmet_goods = {"army": 20.0}
check("a state with unmet goods cannot meet its own need, so it lends nothing", state.cannot_meet_own_need())

# ---- a state's plant: an input nobody sells limits what it can make --------------------------------------------------------------
plant_world = Market({})
share = state_enterprises.input_share(plant_world.state, "arsenal", 1.0, plant_world)
check("a plant whose input nobody sells and the stores lack makes nothing", share == 0.0, share)
check("...and bought nothing", plant_world.purchases == [], plant_world.purchases)
plant_world.state.record.stores = {IRON: 2.0}
share = state_enterprises.input_share(plant_world.state, "arsenal", 1.0, plant_world)
check("a plant makes what the stores' stock of an unsold input allows", abs(share - 0.4) < 1e-9, share)
priced_world = Market({IRON: IRON_PRICE})
share = state_enterprises.input_share(priced_world.state, "arsenal", 1.0, priced_world)
check("a plant whose input is on sale and affordable runs in full", share == 1.0, share)

# ---- the granary buys no grain nobody sells --------------------------------------------------------------------------------------------
granary_world = Market({})
granary_world.material_price = lambda material: 1.0
granary_world.state.record.grain_price_reference = 5.0
spent = granary_world.state.restock_granary(1.0e6, granary_world)
check("a granary cannot restock with grain nobody sells", spent == 0.0 and granary_world.purchases == [], (spent, granary_world.purchases))
