"""Held stock draws on feed, pasture and labour as it grows, and a partner that will not sell can be
robbed at a risk (Complaints/366). The engine mixins run on a small stand-in for the game: a ledger, a purse, a
labour market that prices an hour, and the real partner data; no whole game is built."""

import collections
import os

from .harness import NODES, ROOT, check

from sim.agents import government_foreign  # noqa: F401  (registers the foreign government)
from sim.agents.api import ActorRegistry, ActorsState, cast_from_civilisations, seed_cast
from sim.engine import living_stock_growth, living_stock_smuggling
from sim.engine.data import load_civ
from sim.engine.foreign_economies import ForeignEconomiesMixin
from sim.engine.living_stock import LivingStockMixin
from sim.engine.living_stock_smuggling import LivingStockSmugglingMixin
from sim.engine.living_stock_trade import LivingStockTradeMixin
from sim.engine.living_stock_yearly import LivingStockYearlyMixin, stock_rates
from sim.engine.material_units import tonnes_per_unit
from sim.geography.api import open_map, tiles_held

HOME, PARTNER = "rome_100ad", "han_china_100ad"
HERD, SUGAR, EGGS, TEA = "draught_animal_kg", "sugar_cane_sett_kg", "silkworm_eggs_kg", "tea_plant_stock_kg"
WAGE = 2.0


class Purse:
    def __init__(self, capital, game):
        self.capital, self.game, self.paid = capital, game, []

    def can_pay(self, money):
        return self.capital >= money

    def pay(self, money, purpose):
        self.capital -= money
        self.paid.append((purpose, money))

    def take_delivery(self, key, tonnes):
        self.game.ledger[key] = self.game.ledger.get(key, 0.0) + tonnes


class Market:
    def __init__(self):
        self.pressed = {}

    def quote(self, trade, hours=0.0, employer=None, pay_premium=0.0):
        return WAGE

    def press(self, trade, hours):
        self.pressed[trade] = self.pressed.get(trade, 0.0) + hours


class Game(LivingStockMixin, LivingStockTradeMixin, LivingStockSmugglingMixin, LivingStockYearlyMixin):
    """Just enough of the game for held stock: the home society is Rome, the partner is Han."""
    STATE_CAPACITY_DEFAULT = 0.7
    partner_refusal = ForeignEconomiesMixin.partner_refusal
    partner_government = ForeignEconomiesMixin.partner_government

    def __init__(self, capital=1e6, governed=True):
        self.civ = load_civ(HOME)
        self.world_map = open_map()
        self.ledger, self.opening = collections.defaultdict(float), {}
        self.scandal, self.scandal_last_year = 0.0, 0.0
        self.purse = Purse(capital, self)
        self.labour = type("Labour", (), {"market": Market()})()
        self.goods_market = type("GoodsMarket", (), {"acting": self.purse, "acting_party_id": "founder"})()
        self.state = type("State", (), {
            "scenario": type("Scenario", (), {"year": 100})(),
            "economy": type("Economy", (), {"wild_stock": {}})(),
            "household": type("Household", (), {})()})()
        self.actors = ActorRegistry(ActorsState())
        if governed:
            home, entries, profiles = cast_from_civilisations(self.civ, [load_civ(PARTNER)])
            seed_cast(self.actors, home, entries, profiles)

    @property
    def capital(self):
        return self.purse.capital

    def _material_tag(self, material):
        return (material,)

    def material_stock_t(self, key):
        return self.ledger.get(key, 0.0)

    def _material_stock(self):
        return self.ledger

    def _material_opening_stock(self):
        return self.opening

    def foreign_economies(self):
        return [PARTNER]

    def partner_gate_refusal(self, civilization_id):
        return None

    def _foreign_economy_facts(self, civilization_id):
        return {"route": None, "freight_per_tonne": 10.0}

    def _agent_cost_per_tonne(self, civilization_id, route):
        return 5.0

    def _cargo_lost_share(self, route, material=None, civilization_id=None, destination_demand_tonnes=None):
        return 0.1


# ---- the stock stands on a tile of the holder's -----------------------------------------------
game = Game()
place = game.stock_place()
check("held stock stands on one of the tiles its holder holds", place in tiles_held(game.civ, game.world_map), place)
check("...the same one each time", game.stock_place() == place)

# ---- a herd grows by its rule when feed and purse allow, and pays its labour ------------------
rates = stock_rates()[HERD]
check("the herd row says it grazes", rates.get("grows_on") == "pasture", rates)
game.grant_stock(HERD, 10000.0)
game.step_living_stock()
growth = 10000.0 * rates["natural_increase"]
check("an ample pasture and purse give the stated rule",
      abs(game.stock_held(HERD) - (10000.0 + growth - 10000.0 * rates["annual_loss"])) < 1e-6, game.stock_held(HERD))
entry = living_stock_growth.stock_entry(HERD)
hours = growth / entry["outputs"][HERD] * entry["labour_hours"]["labourer"]
check("the growth is paid for in labour at the going wage",
      game.purse.paid and abs(game.purse.paid[0][1] - hours * WAGE) < 1e-6, game.purse.paid)
check("...and the hours press on the labour market",
      abs(game.labour.market.pressed.get("labourer", 0.0) - hours) < 1e-6, game.labour.market.pressed)

# ---- pasture limits the increase ------------------------------------------------------------------
_shipped_capacity = living_stock_growth.pasture_capacity_kg
living_stock_growth.pasture_capacity_kg = lambda tile, wild, world_map: 10500.0
tight = Game()
tight.grant_stock(HERD, 10000.0)
tight.step_living_stock()
check("a pasture that carries 500 kg more lets the herd grow by 500 kg less its loss",
      abs(tight.stock_held(HERD) - (10500.0 - 10000.0 * rates["annual_loss"])) < 1e-6, tight.stock_held(HERD))
living_stock_growth.pasture_capacity_kg = lambda tile, wild, world_map: 9000.0
full = Game()
full.grant_stock(HERD, 10000.0)
full.step_living_stock()
check("a herd on pasture with no room gains nothing and still suffers its loss",
      abs(full.stock_held(HERD) - 10000.0 * (1.0 - rates["annual_loss"])) < 1e-6, full.stock_held(HERD))
check("...and buys no labour for growth it did not make", not full.purse.paid, full.purse.paid)
living_stock_growth.pasture_capacity_kg = _shipped_capacity

# ---- the purse limits it too ----------------------------------------------------------------------
poor = Game(capital=0.0)
poor.grant_stock(HERD, 10000.0)
poor.step_living_stock()
check("a holder who cannot pay for the labour gets no growth",
      abs(poor.stock_held(HERD) - 10000.0 * (1.0 - rates["annual_loss"])) < 1e-6, poor.stock_held(HERD))
partly = Game(capital=hours * WAGE / 2.0)
partly.grant_stock(HERD, 10000.0)
partly.step_living_stock()
check("a holder who can pay for half of it gets half of the growth",
      abs(partly.stock_held(HERD) - (10000.0 + growth / 2.0 - 10000.0 * rates["annual_loss"])) < 1e-6, partly.stock_held(HERD))

# ---- a nursery is held to the arable land of its place ---------------------------------------------
sugar = stock_rates()[SUGAR]
check("the cane row is raised on arable land and no longer capped at a doubling",
      sugar.get("grows_on") == "arable" and sugar["natural_increase"] > 1.0, sugar)
_shipped_arable = living_stock_growth.arable_hectares
living_stock_growth.arable_hectares = lambda tile, world_map: 0.01
small = Game()
small.grant_stock(SUGAR, 5000.0)
small.step_living_stock()
sett = living_stock_growth.stock_entry(SUGAR)
room = 0.01 * sett["outputs"][SUGAR] / sett["land_hectare_years"]
check("a hundredth of a hectare of land raises only what its output per hectare allows",
      abs(small.stock_held(SUGAR) - (5000.0 + room - 5000.0 * sugar["annual_loss"])) < 1e-6, small.stock_held(SUGAR))
living_stock_growth.arable_hectares = lambda tile, world_map: 1e9
wide = Game()
wide.grant_stock(SUGAR, 5000.0)
wide.step_living_stock()
check("with land enough the cane multiplies by its sourced rate",
      abs(wide.stock_held(SUGAR) - 5000.0 * (1.0 + sugar["natural_increase"] - sugar["annual_loss"])) < 1e-6,
      wide.stock_held(SUGAR))
living_stock_growth.arable_hectares = _shipped_arable
eggs = Game()
eggs.grant_stock(EGGS, 1.0)
eggs.step_living_stock()
check("stock that does not breed buys no labour", not eggs.purse.paid and eggs.stock_held(EGGS) < 1.0, eggs.purse.paid)

# ---- the partner sells what it holds and does not hold back -----------------------------------------
buyer = Game()
check("the partner's state holds the eggs back, from its own record",
      "will not sell" in (buyer.partner_refusal(PARTNER, EGGS) or ""), buyer.partner_refusal(PARTNER, EGGS))
check("...and does not hold back tea", buyer.partner_refusal(PARTNER, TEA) is None, buyer.partner_refusal(PARTNER, TEA))
check("the partner holds tea stock and cane setts at its date, as data",
      load_civ(PARTNER)["opening_stock"].get(TEA, 0) > 0 and load_civ(PARTNER)["opening_stock"].get(SUGAR, 0) > 0)
quote = buyer.stock_smuggle_quote(TEA, 1.0, PARTNER)
check("a partner that sells is not robbed: the quote says to buy",
      not quote["ok"] and "buy it" in quote["error"], quote)

# ---- smuggling what it will not sell ----------------------------------------------------------------
terms = buyer.stock_smuggle_quote(EGGS, 0.1, PARTNER)
check("a partner that holds eggs and will not sell them can be robbed", terms["ok"], terms)
tonnes = 0.1 * tonnes_per_unit(EGGS)
check("the carrying is agents and freight over the tonnes, and not the price",
      abs(terms["cost"] - 15.0 * tonnes) < 1e-12, terms["cost"])
check("what the route loses is lost from what arrives", abs(terms["arrives_units"] - 0.09) < 1e-12, terms)
capacity = load_civ(PARTNER)["state_capacity"]
check("the chance of being caught is the state's reach times how much of its holding goes",
      0.0 < terms["chance_caught"] <= capacity, terms["chance_caught"])
bigger = buyer.stock_smuggle_quote(EGGS, 0.4, PARTNER)
check("a bigger bite out of its holding is likelier seen", bigger["chance_caught"] > terms["chance_caught"], bigger)
check("more than the partner holds cannot be taken",
      not buyer.stock_smuggle_quote(EGGS, 100.0, PARTNER)["ok"])
check("a bad amount is refused", not buyer.stock_smuggle_quote(EGGS, 0.0, PARTNER)["ok"])

# not caught
_shipped_draw = LivingStockSmugglingMixin._smuggling_draw
living_stock_smuggling.LivingStockSmugglingMixin._smuggling_draw = lambda self, terms: 0.999999
thief = Game()
terms = thief.stock_smuggle_quote(EGGS, 0.1, PARTNER)
outcome = thief.settle_stock_smuggle(terms)
check("a smuggler not caught receives the stock less the route's loss",
      outcome and not outcome["caught"] and abs(thief.stock_held(EGGS) - 0.09) < 1e-9, outcome)
check("...pays the carrying", thief.purse.paid == [("stock smuggled", terms["cost"])], thief.purse.paid)
check("...and the partner has that much less to sell",
      abs(thief._partner_holding(PARTNER, EGGS) - (load_civ(PARTNER)["opening_stock"][EGGS] - 0.1)) < 1e-9,
      thief._partner_holding(PARTNER, EGGS))
check("...with no scandal and its markets still open", thief.scandal == 0.0
      and thief.partner_government(PARTNER).markets_closed_until("founder", 100) == 0)

# caught
living_stock_smuggling.LivingStockSmugglingMixin._smuggling_draw = lambda self, terms: 0.0
caught = Game()
terms = caught.stock_smuggle_quote(EGGS, 0.1, PARTNER)
outcome = caught.settle_stock_smuggle(terms)
check("a smuggler caught is left with nothing", outcome["caught"] and caught.stock_held(EGGS) == 0.0, outcome)
check("...still pays the carrying", caught.purse.paid == [("stock smuggled", terms["cost"])], caught.purse.paid)
check("...has the partner's state shut its markets to him for years",
      caught.partner_government(PARTNER).markets_closed_until("founder", 100) == outcome["closed_until"]
      and outcome["closed_until"] > 100, outcome)
check("...so the partner refuses him, naming the year",
      "shut its markets" in (caught.partner_refusal(PARTNER, TEA) or ""), caught.partner_refusal(PARTNER, TEA))
check("...and the partner still holds all its eggs",
      abs(caught._partner_holding(PARTNER, EGGS) - load_civ(PARTNER)["opening_stock"][EGGS]) < 1e-12)
check("...and his scandal at home rises", caught.scandal > 0.0 and caught.scandal_last_year > 0.0, caught.scandal)
check("...but not for another party's purchase", "shut" not in (
    (lambda game: (setattr(game.goods_market, "acting_party_id", "other"), game.partner_refusal(PARTNER, TEA))[1])(caught) or ""))

# cannot pay
broke = Game(capital=0.0)
terms = broke.stock_smuggle_quote(EGGS, 0.1, PARTNER)
check("a taker who cannot pay the carrying is refused and nothing happens",
      broke.settle_stock_smuggle(terms) is False and broke.stock_held(EGGS) == 0.0 and broke.scandal == 0.0)

# before the roster is seeded the same policy answers from the country's data
unseeded = Game(governed=False)
check("before the roster is seeded the policy answers from the country's data",
      "will not sell" in (unseeded.partner_refusal(PARTNER, EGGS) or "") and unseeded.partner_refusal(PARTNER, TEA) is None)

LivingStockSmugglingMixin._smuggling_draw = _shipped_draw

# ---- planted rubber -------------------------------------------------------------------------------------
RUBBER = "rubber_planting_stock_kg"
rubber_node = NODES.get("ag2_rubber_plantation") or {}
check("a planted-rubber node grants the rubber stock", (rubber_node.get("grants") or {}).get(RUBBER, 0) > 0, rubber_node.get("grants"))
check("it needs a way to the Amazon and the practice of moving a crop",
      {"exp_americas_factory", "exp_transplant_botany"} <= set(rubber_node.get("pre") or ()), rubber_node.get("pre"))
check("the rubber row is a living-stock row with a source and a grade", RUBBER in stock_rates()
      and stock_rates()[RUBBER].get("confidence") in ("C", "D") and len(stock_rates()[RUBBER].get("source", "")) > 40)
check("its nursery entry is gated on the node and works land and labour",
      (living_stock_growth.stock_entry(RUBBER) or {}).get("requires_node") == "ag2_rubber_plantation"
      and living_stock_growth.stock_entry(RUBBER).get("land_hectare_years", 0) > 0)
with open(os.path.join(ROOT, "docs", "knowledge", "76_farming_food_deep.md"), encoding="utf-8") as _handle:
    _doc = _handle.read()
check("the node's knowledge section exists and names budding and tapping",
      "### ag2_rubber_plantation" in _doc and "bud" in _doc.split("### ag2_rubber_plantation")[1].lower()
      and "tap" in _doc.split("### ag2_rubber_plantation")[1].lower())
