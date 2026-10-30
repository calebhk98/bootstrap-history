"""Complaints/147: where the project material bill reaches the player and the books. Each method runs on a stand-in `self` carrying only
what it reads: the quote and the purchase charge one figure (`_quote_material`, `GoodsMarket.buy`), `why` shows the engine's cost
(`_explain_cost`), a project's cost is its frozen bill once it runs (`project_cost`), starting pays the up-front materials and fixes
the bill (`settle_project_materials`, `initialize_project`), and a saved game keeps the bill. The bill's own rules are
test_complaint_147_project_materials."""

QUICK_TOPIC = True

from sim.tests import market_stand_in
from types import SimpleNamespace

from .harness import check

from sim.markets.goods_market import GoodsMarket
from sim.markets.module import Markets
from sim.tests import finance_host, module_harness, projects_host
from sim.materials.api import SettleProjectMaterials as SettleCommand
from sim.tests import materials_stand_in
from sim.engine.state import deserialize_state, serialize_state
from sim.invalidating import ActiveProjectState
from sim.projects.state import ProjectsSeat
from sim.projects.api import SettleProjectMaterials
from sim.tests import projects_host
from sim.ui.proto.quote_purchases import _quote_material
from sim.ui.proto.techtree import _explain_cost
from sim.tests.ui_stand_in import Game


class Buyer:
    party_id = "buyer"

    def __init__(self):
        self.paid, self.delivered = [], []

    def can_pay(self, money):
        return True


# ---- the quote is what buying charges
def stand_in_market(room):
    settled = []
    market = Game(
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
game = Game(
    material_trade_quote=lambda material: {"material": material, "buy_per_tonne": 7.0, "sell_per_tonne": 6.0,
                                           "market_available_tonnes_per_year": 100.0},
    material_purchase_cost=lambda material, tonnes: quoted_orders.append((material, tonnes)) or (170.0, 17.0),
    capital=1000.0, spending_power=lambda kind: 1500.0,
    view=finance_host.purchase_views(lambda kind: 1500.0))
reply = _quote_material(game, {"material": "coal_kg"}, 10.0)
check("the material quote's cost for an order is the purchase cost of that order", reply["to_buy_it"] == 170.0
      and quoted_orders == [("coal_kg", 10.0)], reply)
reply = _quote_material(game, {"material": "coal_kg"}, 500.0)
check("the quote is for the order cut to what the market offers a year", quoted_orders[-1] == ("coal_kg", 100.0), quoted_orders)
check("the quote's average a tonne is its cost over the tonnes", reply["average_per_tonne_for_this_order"] == 1.7, reply)
unpriced = Game(material_trade_quote=lambda material: None)
check("a material nobody sells is refused", _quote_material(unpriced, {"material": "ghost_kg"}, 1.0)["ok"] is False, None)

# ---- the material cost reaches the market's quote
asked = []
game = Game(goods_market=Game(quote_buy=lambda material, tonnes, already: asked.append((material, tonnes, already)) or (1.0, 1.0)))
market_stand_in.markets_over(goods_market=game.goods_market).purchase_quote("coal_kg", 3.0, 2.0)
check("the bill's price of an order is the goods market's quote for it", asked == [("coal_kg", 3.0, 2.0)], asked)

# ---- why shows the engine's cost
BILL = {"rows": [], "cost_of_missing": 123.456}
game = Game(
    project_material_bill=lambda node_id: BILL, civ_cost_factor=lambda node_id: 1.1, geography=Game(material_cost_factor=lambda node_id: 1.2),
    opposition_factor=lambda node_id: 1.0, rebuild_work_factor=lambda node_id: 1.0, cost_money_factor=lambda: 1.0, money_real=1.0, project_cost=lambda node_id: 987.654, year=100,
    done=set(), active={}, paid_towards={})
cost = _explain_cost(game, {}, "node", {"_labour_cost": 10.0, "cap": 5.0})
check("why's headline total is the cost the engine charges", cost["total"] == 987.7, cost)
check("why's materials line is the cost of the missing part of the bill and the base total adds it to labour and capital",
      cost["materials"] == 123.5 and cost["base_total"] == 138.5, cost)

# ---- what a project costs
def costing(active, now=None, **views):
    """The projects module over a record of projects in hand; `now` stands in for what starting today would cost."""
    module = projects_host.build(projects_record=projects_host.projects_state(active=active), **views)
    if now is not None:
        module.project_cost_now = lambda node_id: now
    return module


check("a running project costs its frozen bill whatever the market does since", costing({"node": {"bill": 500.0}}, now=900.0).project_cost("node") == 500.0, None)
check("a running project with no frozen bill costs what starting today would", costing({"node": {}}, now=900.0).project_cost("node") == 900.0, None)
check("a project not yet started costs what starting today would", costing({}, now=900.0).project_cost("node") == 900.0, None)
module = costing({}, project_material_parts=lambda node_id: (40.0, 30.0), project_cost_without_materials=lambda node_id: 60.0,
                 material_cost_factor=lambda node_id: 1.5, state_interest=lambda node: -4.0)
module.opposition_factor = lambda node_id: 2.0
check("starting today costs labour, capital and missing materials times the distance and opposition factors",
      module.project_cost_now("node") == (60.0 + 40.0) * 1.5 * 2.0, None)

# ---- starting pays for the materials and fixes the bill
def settling(up_front, paid):
    bought = []
    module = materials_stand_in.build(project_cost_now=lambda node_id: 1000.0)
    module.up_front_materials_money = lambda node_id: up_front
    module.buy_project_materials = lambda node_id: bought.append(node_id) or paid
    return module, bought


game, bought = settling(up_front=300.0, paid=300.0)
check("starting pays the up-front materials and leaves the rest of the cost to pay in instalments",
      game.settle_project_materials(SettleCommand("node")) == (700.0, 300.0) and bought == ["node"], bought)
game, bought = settling(up_front=0.0, paid=0.0)
check("with no materials to buy up front nothing is bought and the whole cost is left", game.settle_project_materials(SettleCommand("node")) == (1000.0, 0.0)
      and bought == [], bought)

module = projects_host.build(
    answers={SettleProjectMaterials: (700.0, 300.0)}, tree={"node": {"ph": 10.0, "lab": {"smith": 4.0}}},
    projects_record=projects_host.projects_state(), own_output_claim=lambda node_id: {"forest": 2.0})
record = module.initialize_project("node")
check("a started project's bill is fixed at what was left after paying the materials", record["bill"] == 700.0 and record["cost_left"] == 700.0
      and module.seat.active["node"] is record, record)
check("a started project records the own output it claims and the labour it needs", record["own_output_claim"] == {"forest": 2.0}
      and record["lab_left"] == {"smith": 4.0} and record["ph_left"] == 10.0, record)

# ---- a save keeps the bill
loaded = deserialize_state(serialize_state(ProjectsSeat(active={"node": ActiveProjectState.from_dict(dict(record))})), ProjectsSeat)
check("a saved game keeps a running project's frozen bill", loaded.active["node"]["bill"] == 700.0, loaded.active)
