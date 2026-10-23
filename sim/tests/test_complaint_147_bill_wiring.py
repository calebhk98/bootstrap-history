"""Complaints/147: where the project material bill reaches the player and the books. Each method runs on a stand-in `self` carrying only
what it reads: the quote and the purchase charge one figure (`_quote_material`, `GoodsMarket.buy`), `why` shows the engine's cost
(`_explain_cost`), a project's cost is its frozen bill once it runs (`project_cost`), starting pays the up-front materials and fixes
the bill (`settle_project_materials`, `initialize_project`), and a saved game keeps the bill. The bill's own rules are
test_complaint_147_project_materials."""

QUICK_TOPIC = True

from types import SimpleNamespace

from .harness import check

from sim.engine.economy import EconomyMixin
from sim.engine.goods_market_api import GoodsMarket
from sim.engine.project_materials import ProjectMaterialsMixin
from sim.engine.projects_starting import StartingMixin
from sim.engine.state import SimulationState, deserialize_state, serialize_state
from sim.engine.state_seat import seat_from_template
from sim.ui.proto.quote_purchases import _quote_material
from sim.ui.proto.techtree import _explain_cost


class Buyer:
    party_id = "buyer"

    def __init__(self):
        self.paid, self.delivered = [], []

    def can_pay(self, money):
        return True


# ---- the quote is what buying charges
def stand_in_market(room):
    settled = []
    market = SimpleNamespace(
        quote=lambda material: {"material": material, "stock_key": "coal"},
        bought_tonnes=lambda key, party: 0.0, market_room_tonnes=lambda quote, bought: room,
        purchase_cost=lambda material, tonnes, already=0.0: (7.0 * tonnes + tonnes * tonnes, 7.0 + tonnes),
        settle_purchase=lambda buyer, key, tonnes, money: settled.append((key, tonnes, money)))
    return market, settled


market, settled = stand_in_market(room=100.0)
got = GoodsMarket.buy(market, Buyer(), "coal_kg", 10.0)
check("buying settles the tonnes at the money purchase_cost gives for that order", got == 10.0 and settled == [("coal", 10.0, 170.0)], settled)
market, settled = stand_in_market(room=4.0)
got = GoodsMarket.buy(market, Buyer(), "coal_kg", 10.0)
check("an order beyond the market's room is cut and the cut order is what is charged", got == 4.0 and settled == [("coal", 4.0, 44.0)], settled)

quoted_orders = []
game = SimpleNamespace(
    material_trade_quote=lambda material: {"material": material, "buy_per_tonne": 7.0, "sell_per_tonne": 6.0,
                                           "market_available_tonnes_per_year": 100.0},
    material_purchase_cost=lambda material, tonnes: quoted_orders.append((material, tonnes)) or (170.0, 17.0),
    capital=1000.0, spending_power=lambda kind: 1500.0)
reply = _quote_material(game, {"material": "coal_kg"}, 10.0)
check("the material quote's cost for an order is the purchase cost of that order", reply["to_buy_it"] == 170.0
      and quoted_orders == [("coal_kg", 10.0)], reply)
reply = _quote_material(game, {"material": "coal_kg"}, 500.0)
check("the quote is for the order cut to what the market offers a year", quoted_orders[-1] == ("coal_kg", 100.0), quoted_orders)
check("the quote's average a tonne is its cost over the tonnes", reply["average_per_tonne_for_this_order"] == 1.7, reply)
unpriced = SimpleNamespace(material_trade_quote=lambda material: None)
check("a material nobody sells is refused", _quote_material(unpriced, {"material": "ghost_kg"}, 1.0)["ok"] is False, None)

# ---- the material cost reaches the market's quote
asked = []
game = SimpleNamespace(goods_market=SimpleNamespace(quote_buy=lambda material, tonnes, already: asked.append((material, tonnes, already)) or (1.0, 1.0)))
ProjectMaterialsMixin.material_purchase_cost(game, "coal_kg", 3.0, 2.0)
check("the bill's price of an order is the goods market's quote for it", asked == [("coal_kg", 3.0, 2.0)], asked)

# ---- why shows the engine's cost
BILL = {"rows": [], "cost_of_missing": 123.456}
game = SimpleNamespace(
    project_material_bill=lambda node_id: BILL, civ_cost_factor=lambda node_id: 1.1, geography=SimpleNamespace(material_cost_factor=lambda node_id: 1.2),
    opposition_factor=lambda node_id: 1.0, cost_money_factor=lambda: 1.0, money_real=1.0, project_cost=lambda node_id: 987.654, year=100,
    done=set(), active={}, paid_towards={})
cost = _explain_cost(game, {}, "node", {"_labour_cost": 10.0, "cap": 5.0})
check("why's headline total is the cost the engine charges", cost["total"] == 987.7, cost)
check("why's materials line is the cost of the missing part of the bill and the base total adds it to labour and capital",
      cost["materials"] == 123.5 and cost["base_total"] == 138.5, cost)

# ---- what a project costs
frozen = SimpleNamespace(state=SimpleNamespace(projects=SimpleNamespace(active={"node": {"bill": 500.0}})), project_cost_now=lambda node_id: 900.0)
check("a running project costs its frozen bill whatever the market does since", EconomyMixin.project_cost(frozen, "node") == 500.0, None)
frozen.state.projects.active = {"node": {}}
check("a running project with no frozen bill costs what starting today would", EconomyMixin.project_cost(frozen, "node") == 900.0, None)
frozen.state.projects.active = {}
check("a project not yet started costs what starting today would", EconomyMixin.project_cost(frozen, "node") == 900.0, None)
game = SimpleNamespace(project_material_parts=lambda node_id: (40.0, 30.0), project_cost_without_materials=lambda node_id: 60.0,
                       geography=SimpleNamespace(material_cost_factor=lambda node_id: 1.5), opposition_factor=lambda node_id: 2.0)
check("starting today costs labour, capital and missing materials times the distance and opposition factors",
      EconomyMixin.project_cost_now(game, "node") == (60.0 + 40.0) * 1.5 * 2.0, None)

# ---- starting pays for the materials and fixes the bill
def settling(up_front, paid):
    bought = []
    return SimpleNamespace(project_cost_now=lambda node_id: 1000.0, _up_front_materials_money=lambda node_id: up_front,
                           buy_project_materials=lambda node_id: bought.append(node_id) or paid), bought


game, bought = settling(up_front=300.0, paid=300.0)
check("starting pays the up-front materials and leaves the rest of the cost to pay in instalments",
      ProjectMaterialsMixin.settle_project_materials(game, "node") == (700.0, 300.0) and bought == ["node"], bought)
game, bought = settling(up_front=0.0, paid=0.0)
check("with no materials to buy up front nothing is bought and the whole cost is left", ProjectMaterialsMixin.settle_project_materials(game, "node") == (1000.0, 0.0)
      and bought == [], bought)

game = SimpleNamespace(nodes={"node": {"ph": 10.0, "lab": {"smith": 4.0}}}, state=SimpleNamespace(projects=SimpleNamespace(active={})),
                       project_own_output_claim=lambda node_id: {"forest": 2.0}, rebuild_work_factor=lambda node_id: 1.0,
                       settle_project_materials=lambda node_id: (700.0, 300.0))
record = StartingMixin.initialize_project(game, "node")
check("a started project's bill is fixed at what was left after paying the materials", record["bill"] == 700.0 and record["cost_left"] == 700.0
      and game.state.projects.active["node"] is record, record)
check("a started project records the own output it claims and the labour it needs", record["own_output_claim"] == {"forest": 2.0}
      and record["lab_left"] == {"smith": 4.0} and record["ph_left"] == 10.0, record)

# ---- a save keeps the bill
seat = seat_from_template({}, 10.0, 1e9, {})
state = SimulationState(household=seat.household, projects=seat.projects, founder=seat.founder)
state.projects.active["node"] = dict(record)
loaded = deserialize_state(serialize_state(state))
check("a saved game keeps a running project's frozen bill", loaded.projects.active["node"]["bill"] == 700.0, loaded.projects.active)
