"""Stock bought from a partner is charged what it was quoted. The quote handlers (`quote_living_stock`, `quote_smuggled_stock`) and the
settlements (`settle_stock_purchase`, `settle_stock_smuggle`) read one terms dict, so the figure the quote shows is the figure the
buyer pays, caught or not. Each runs on a stand-in `self`; the dispatcher-wide table is test_quote_matches_charge_scenario."""
QUICK_TOPIC = True

from types import SimpleNamespace
from unittest import mock

from .harness import check

from sim.engine.living_stock_smuggling import LivingStockSmugglingMixin
from sim.engine.living_stock_trade import LivingStockTradeMixin
from sim.ui.proto import stock_purchases

MATERIAL = "ramie_stock_kg"
COST = 123.456


class Buyer:
    def __init__(self, can_pay=True):
        self.paid, self.can = [], can_pay
        self.delivered = []

    def can_pay(self, money):
        return self.can

    def pay(self, money, purpose):
        self.paid.append((money, purpose))

    def take_delivery(self, key, tonnes):
        self.delivered.append((key, tonnes))


def terms(**more):
    return dict(ok=True, material=MATERIAL, units=100.0, tonnes=0.1, partner="han_china_100ad", cost=COST, per_tonne=1234.56,
                chance_caught=0.25, arrives_units=90.0, **more)


# --- stock bought from a partner that sells it
class Trade(LivingStockTradeMixin):
    pass


trade = Trade()
buyer = Buyer()
imports = []
trade.goods_market = SimpleNamespace(acting=buyer, settle_import=lambda who, key, tonnes, cost, purpose: imports.append((cost, purpose)),
                                     home_unit_price=lambda material: None)
trade._stock_key = lambda material: material
trade.partner_civ = lambda partner: {"coin_standard": {"material": "silver_kg", "kg_per_unit": 0.01}}
check("the purchase settles the quoted cost, not a second estimate", trade.settle_stock_purchase(terms()) and imports == [(COST, "stock bought abroad")], imports)
check("a buyer who cannot pay the quote is refused and charged nothing", Trade.settle_stock_purchase(
    SimpleNamespace(goods_market=SimpleNamespace(acting=Buyer(can_pay=False), settle_import=lambda *args: imports.append("charged"))), terms()) is False
      and imports == [(COST, "stock bought abroad")], imports)

quoting = SimpleNamespace(stock_purchase_quote=lambda material, quantity, partner: terms(), capital=1000.0)
from sim.engine.ui_port import purchase_rule  # noqa: E402
with mock.patch.object(purchase_rule, "purchase_budget", lambda sim: 1000.0):
    reply = stock_purchases.quote_living_stock(quoting, {"material": MATERIAL}, 100.0)
check("the living-stock quote shows the terms' cost", reply["ok"] and reply["to_buy_it"] == round(COST, 1), reply)
refusal = stock_purchases.quote_living_stock(
    SimpleNamespace(stock_purchase_quote=lambda *args: {"ok": False, "cause": "no_partner_sells", "error": "nobody sells it"}),
    {"material": MATERIAL}, 100.0)
check("a quote no partner can fill carries the cause and changes nothing", refusal["ok"] is False and refusal["cause"] == "no_partner_sells", refusal)


# --- stock smuggled: the carrying is charged whether or not the taker is caught
class Smuggle(LivingStockSmugglingMixin):
    pass


def smuggle(caught):
    taker = Buyer()
    host = Smuggle()
    host.goods_market = SimpleNamespace(acting=taker)
    host._smuggling_draw = lambda quoted: 0.0 if caught else 0.99
    host.partner_government = lambda partner: None
    host._stock_key = lambda material: material
    host._punish_smuggler = lambda government, outcome: outcome.update(closed_until=200)
    return taker, host.settle_stock_smuggle(terms())


for caught in (False, True):
    taker, outcome = smuggle(caught)
    check("smuggling charges the quoted carrying once (caught: %s)" % caught,
          taker.paid == [(COST, "stock smuggled")] and outcome["caught"] is caught, (taker.paid, outcome))
check("...and delivers the stock less the route's loss only when not caught",
      smuggle(False)[0].delivered[0][1] > 0.0 and smuggle(False)[1]["delivered_units"] == 90.0
      and smuggle(True)[0].delivered == [] and smuggle(True)[1]["delivered_units"] == 0.0)
quoted = stock_purchases.quote_smuggled_stock(SimpleNamespace(stock_smuggle_quote=lambda material, quantity, partner: terms(), capital=1.0),
                                              {"material": MATERIAL}, 100.0)
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


from sim.engine.goods_market_api import GoodsMarket  # noqa: E402

market = SimpleNamespace(quote_sell=lambda material, tonnes, seller=None: ("iron_stock", 25.0, 750.0), note_sale=lambda *args: None)
seller = Seller()
sold = GoodsMarket.sell(market, seller, "iron", 40.0)
check("a sale hands over what the market took and is paid what the sale quote said",
      sold == 25.0 and seller.handed == [("iron_stock", 25.0)] and seller.received == [(750.0, "materials sold")], (sold, seller.handed, seller.received))
nothing = SimpleNamespace(quote_sell=lambda material, tonnes, seller=None: (None, 0.0, 0.0))
check("a sale the market will not take pays nothing", GoodsMarket.sell(nothing, Seller(), "iron", 40.0) == 0.0)
