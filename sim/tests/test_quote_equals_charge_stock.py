"""Stock bought from a partner is charged what it was quoted. The quote handlers (`quote_living_stock`, `quote_smuggled_stock`) and the
settlements (`BuyStock`, `SmuggleStock`, applied by the living-stock module) read one terms dict, so the figure the quote shows is the figure the
buyer pays, caught or not. The module is built by the harness, the screen runs on a stand-in game; the dispatcher-wide table is test_quote_matches_charge_scenario."""
QUICK_TOPIC = True

from types import SimpleNamespace
from unittest import mock

from .harness import check

from sim.agents.api import edges
from sim.foreign_trade.api import SettleFlow
from sim.ledger.api import ChangeStock, PayEdge
from sim.living_stock.api import BuyStock, SmuggleStock
from sim.living_stock.module import LivingStock
from sim.polity.api import RaiseScandal
from sim.refusal import Refusal
from sim.tests import module_harness
from sim.ui.proto import stock_purchases
from sim.tests.ui_stand_in import Game

MATERIAL = "ramie_stock_kg"
COST = 123.456


def terms(**more):
    return dict(ok=True, material=MATERIAL, units=100.0, tonnes=0.1, partner="han_china_100ad", cost=COST, per_tonne=1234.56,
                chance_caught=0.25, arrives_units=90.0, **more)


def stock_module(can_pay=True, has_government=False):
    return module_harness.build(LivingStock, views={
        "can_pay": lambda cost: can_pay, "material_commodity": lambda material: material, "year": 100,
        "acting_balance": 500.0, "partner": lambda partner: {"has_government": has_government, "civ": {}, "stock_taken": {}}})


# --- stock bought from a partner that sells it
paying = stock_module()
bought = terms()
check("the purchase settles the quoted cost, not a second estimate",
      paying.buy_stock(BuyStock(bought["material"], bought["partner"], bought["tonnes"], bought["cost"])) is True
      and module_harness.sent(paying) == [PayEdge(edges.EDGE_MARKET, COST, "stock bought abroad"),
                                          ChangeStock(MATERIAL, 0.1), SettleFlow("han_china_100ad", 0.1, COST)],
      module_harness.sent(paying))
broke = stock_module(can_pay=False)
check("a buyer who cannot pay the quote is refused and charged nothing",
      isinstance(broke.buy_stock(BuyStock(bought["material"], bought["partner"], bought["tonnes"], bought["cost"])), Refusal)
      and module_harness.sent(broke) == [])


class Screen:
    """The game as the purchase screen reads it: one quote view."""

    def __init__(self, quote):
        self.quote, self.capital = quote, 1000.0

    def view(self, name):
        return (lambda: self.capital) if name == "acting_balance" else (lambda *arguments: self.quote)


from sim.engine.ui_port import purchase_rule  # noqa: E402
with mock.patch.object(purchase_rule, "purchase_budget", lambda sim: 1000.0):
    reply = stock_purchases.quote_living_stock(Screen(terms()), {"material": MATERIAL}, 100.0)
check("the living-stock quote shows the terms' cost", reply["ok"] and reply["to_buy_it"] == round(COST, 1), reply)
refusal = stock_purchases.quote_living_stock(
    Screen({"ok": False, "cause": "no_partner_sells", "error": "nobody sells it"}), {"material": MATERIAL}, 100.0)
check("a quote no partner can fill carries the cause and changes nothing", refusal["ok"] is False and refusal["cause"] == "no_partner_sells", refusal)


# --- stock smuggled: the carrying is charged whether or not the taker is caught
def smuggle(caught):
    taker = stock_module()
    taker.smuggling_draw = lambda quoted: 0.0 if caught else 0.99
    quoted = terms()
    outcome = taker.smuggle_stock(SmuggleStock(quoted["material"], quoted["partner"], quoted["units"], quoted["tonnes"],
                                               quoted["cost"], quoted["arrives_units"], quoted["chance_caught"]))
    return module_harness.sent(taker), outcome


for caught in (False, True):
    sent, outcome = smuggle(caught)
    check("smuggling charges the quoted carrying once (caught: %s)" % caught,
          sent.count(PayEdge(edges.EDGE_MARKET, COST, "stock smuggled")) == 1 and outcome["caught"] is caught, (sent, outcome))
check("...and delivers the stock less the route's loss only when not caught",
      any(isinstance(sent, ChangeStock) and sent.tonnes > 0.0 for sent in smuggle(False)[0]) and smuggle(False)[1]["delivered_units"] == 90.0
      and not any(isinstance(sent, ChangeStock) for sent in smuggle(True)[0]) and smuggle(True)[1]["delivered_units"] == 0.0)
check("a caught smuggler's scandal rises", any(isinstance(sent, RaiseScandal) for sent in smuggle(True)[0])
      and not any(isinstance(sent, RaiseScandal) for sent in smuggle(False)[0]))
broke = stock_module(can_pay=False)
check("a taker who cannot pay the carrying is refused and charged nothing",
      isinstance(broke.smuggle_stock(SmuggleStock(MATERIAL, "han_china_100ad", 100.0, 0.1, COST, 90.0, 0.25)), Refusal)
      and module_harness.sent(broke) == [])
quoted = stock_purchases.quote_smuggled_stock(Screen(terms()), {"material": MATERIAL}, 100.0)
check("the smuggling quote shows the terms' cost and chance of capture", quoted["to_buy_it"] == round(COST, 1) and quoted["chance_caught"] == 0.25, quoted)


# --- stock sold at the market: the receipt is the figure the cash-raising refusal quoted
class Seller:
    party_id = "seller"

    def __init__(self):
        self.received, self.handed = [], []

    def hand_over(self, key, tonnes):
        self.handed.append((key, tonnes))

    def receive(self, money, purpose):
        self.received.append((money, purpose))


from sim.markets.goods_market import GoodsMarket  # noqa: E402

market = Game(quote_sell=lambda material, tonnes, seller=None: ("iron_stock", 25.0, 750.0), note_sale=lambda *args: None)
seller = Seller()
sold = GoodsMarket.sell(market, seller, "iron", 40.0)
check("a sale hands over what the market took and is paid what the sale quote said",
      sold == 25.0 and seller.handed == [("iron_stock", 25.0)] and seller.received == [(750.0, "materials sold")], (sold, seller.handed, seller.received))
nothing = Game(quote_sell=lambda material, tonnes, seller=None: (None, 0.0, 0.0))
check("a sale the market will not take pays nothing", GoodsMarket.sell(nothing, Seller(), "iron", 40.0) == 0.0)
