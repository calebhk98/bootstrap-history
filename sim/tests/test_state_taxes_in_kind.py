"""Complaint 622: a state levies any good its revenue forms declare in kind, not grain only. The levy is a
share of what the country's producers made of the good; the tonnes go to the state's stores, the budget lines
draw on them before they buy, and they are valued at the price the market quotes."""

QUICK_TOPIC = True

from .harness import check

from sim.agents import revenue
from sim.agents.api import ActorRecord
from sim.agents.budget_line import Line
from sim.agents.government import Government

from .agents_fake_world import FakeWorld

WINE_PRICE = 40.0
WINE_LEVY = {"form": "vintage_levy", "basis": "harvest", "rate": 0.1, "paid_in": "wine_kg"}
OIL_LEVY = {"form": "oil_levy", "basis": "harvest", "rate": 0.2, "paid_in": "olive_oil_kg", "tiles": ["a"]}


class LevyWorld(FakeWorld):
	"""A country that makes wine on two tiles and oil on one."""

	output_by_tile = {"a": {"wine_kg": 3000.0, "olive_oil_kg": 100.0}, "b": {"wine_kg": 2000.0}}

	def __init__(self, forms):
		super().__init__()
		self.forms = forms
		self.prices = {"wine_kg": WINE_PRICE, "olive_oil_kg": 90.0, "wheat_kg": 10.0}

	def revenue_forms(self):
		return self.forms

	def held_tiles(self):
		return ["a", "b"]

	def output_tonnes(self, material, tiles=None):
		return sum(row.get(material, 0.0) for tile, row in self.output_by_tile.items() if tiles is None or tile in tiles)

	def trade_value(self, direction):
		return 1000.0

	def material_price(self, material):
		return self.prices[material]

	def commodity_of(self, material):
		return material.replace("_kg", "")

	def revenue_assessments(self):
		return revenue.assess(self)


# ---- the levy is a share of the good the form names, valued at the quoted price ----------------------
world = LevyWorld([WINE_LEVY, OIL_LEVY])
by_form = {assessed.form: assessed for assessed in revenue.assess(world)}
wine = by_form["vintage_levy"]
check("a levy on wine takes its rate of the wine made, in tonnes",
	  wine.in_kind and wine.material == "wine_kg" and abs(wine.tonnes - 0.1 * 5000.0) < 1e-9, wine)
check("the wine taken is valued at the price the market quotes",
	  abs(wine.money - wine.tonnes * WINE_PRICE) < 1e-9, wine)
oil = by_form["oil_levy"]
check("a levy limited to tiles takes its rate of what those tiles made",
	  abs(oil.tonnes - 0.2 * 100.0) < 1e-9, oil)

# ---- the tonnes move into the stores, and the lines draw on them before they buy ------------------------
state = Government("government:home", ActorRecord(kind="government"))
state.receive_revenue(world)
check("a levy on a non-grain good puts that good in the state's stores",
	  abs(state.record.stores.get("wine_kg", 0.0) - 500.0) < 1e-9
	  and abs(state.record.stores.get("olive_oil_kg", 0.0) - 20.0) < 1e-9, state.record.stores)
check("goods taken in kind are recorded as received, in tonnes",
	  abs(state.record.in_kind_received["wine_kg"] - 500.0) < 1e-9, state.record.in_kind_received)
check("goods taken in kind are not booked as coin taxation",
	  state.record.income.get("taxation", 0.0) == 0.0, state.record.income)

ration = Line("army rations", "requisition", materials={"wine": 800.0}, material_cost=800.0 * WINE_PRICE)
drawn = state.draw_stores([ration], world)[0]
check("a budget line draws the stored wine before it buys", abs(drawn.materials.get("wine", 0.0) - 300.0) < 1e-9, drawn)
check("the line buys only the rest, at the same price", abs(drawn.material_cost - 300.0 * WINE_PRICE) < 1e-9, drawn)
check("what a line drew has left the stores", state.record.stores.get("wine_kg", 0.0) == 0.0, state.record.stores)

# ---- a form that names a good its basis cannot yield is refused ---------------------------------------
bad = LevyWorld([{"form": "poll_levy", "basis": "imports_value", "rate": 0.1, "paid_in": "wine_kg"}])
try:
	revenue.assess(bad)
	refused = False
except ValueError:
	refused = True
check("a form paid in a good its basis does not yield is refused", refused)
