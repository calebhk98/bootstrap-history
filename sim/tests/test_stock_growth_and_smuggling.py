"""Held stock draws on feed, pasture and labour as it grows, and a partner that will not sell can be
robbed at a risk (Complaints/366). The living-stock module runs over a small stand-in for the game: a ledger, a purse, a
labour market that prices an hour, and the real partner data, which the engine bridge's views read as in a game; no whole
game is built."""

QUICK_TOPIC = True

import collections
import os
import types

from .harness import NODES, ROOT, check
from .ledger_host import apply_to_own_stock
from sim.refusal import Refusal, cause_of
from sim.agents.no_country_economy import NoCountryEconomy
from sim.unit_conversions import HOURS_PER_PERSON_YEAR

from sim.actors.world import ActorWorld
from sim.agents.api import ActorRegistry, ActorsState, cast_from_civilisations, seed_cast
from sim.tests.world_stand_in import fake_needs
from sim.engine import bridge_living_stock as bridge
from sim.polity.state import PolitySeat
from sim.tests import land_host, polity_host
from sim.engine.data import load_civ
from sim.ledger.api import ChangeStock, PayEdge
from sim.living_stock.api import ChangeHeld, SmuggleStock, stock_entry, stock_rates
from sim.living_stock.module import LivingStock
from sim.living_stock.state import LivingStockWorld
from sim.polity.api import RaiseScandal
from sim.tests import module_harness
from sim.workforce.api import PressLabour
from sim.workforce.module import Workforce
from sim.foreign_trade.api import CloseMarketsTo, RecordStockTaken
from sim.foreign_trade.module import ForeignTrade
from sim.agents.api import GOVERNMENT_PREFIX
from sim.world.material_units import tonnes_per_unit
from sim.geography import stock_land
from sim.geography.api import Geography, open_map, tiles_held

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


class CountryAnswers:
    """A country's labour markets pay every trade the same hourly wage the founder's does."""
    def pay_per_person_year(self, trade):
        return WAGE * HOURS_PER_PERSON_YEAR

    def __getattr__(self, name):
        raise NoCountryEconomy("stub", name)


class StubEconomy:
    def agent_country(self, country):
        return CountryAnswers()


class StubbedPartners(ForeignTrade):
    """The foreign-trade module with the facts of the partner's economy written out: no route, a stated freight."""

    def partner_facts(self, civilization_id):
        return {"route": None, "freight_per_tonne": 10.0}


class Game:
    """Just enough of the game for held stock: the home society is Rome, the partner is Han. `module` is the living-stock
    module whose views are the engine bridge's, read from this stand-in as the bridge reads a game."""
    STATE_CAPACITY_DEFAULT = 0.7
    HOURS_PER_PERSON_YEAR = HOURS_PER_PERSON_YEAR

    def __init__(self, capital=1e6, governed=True):
        self.civ = load_civ(HOME)
        self.world_map = open_map()
        self.geography = Geography(types.SimpleNamespace(civ=self.civ, world_map=self.world_map))
        self.land = land_host.build(self.civ, views={"wild_stock": lambda: {}})
        self.land._geography_cache = self.geography
        self.ledger, self.opening = collections.defaultdict(float), {}
        self.standing = PolitySeat(scandal=0.0, scandal_last_year=0.0)
        self.polity = polity_host.build(seat=self.standing)
        self.purse = Purse(capital, self)
        self.labour = type("Labour", (), {"market": Market()})()
        self.workforce = module_harness.build(Workforce)
        self.workforce.labour = self.labour
        self.goods_market = type("GoodsMarket", (), {"acting": self.purse, "acting_party_id": "founder"})()
        self.state = type("State", (), {
            "scenario": type("Scenario", (), {"year": 100})(),
            "household": type("Household", (), {})()})()
        self.actors = ActorRegistry(ActorsState())
        self.economy = StubEconomy()
        if governed:
            home, entries, profiles = cast_from_civilisations(self.civ, [load_civ(PARTNER)])
            seed_cast(self.actors, home, entries, profiles)
        self.trade = module_harness.build(StubbedPartners, views={
            "foreign_economy_records": [{"civilization": PARTNER, "enabled": True, "from_year": -1000, "until_year": 3000}],
            "year": 100, "civilisation": {"id": HOME}, "civilisation_record": load_civ, "partner_reached": lambda civ: True,
            "cast": self.actors,
            "acting_seat": lambda: self.goods_market.acting_party_id,
            "trader_agent_cost": lambda civilization_id, route: 5.0,
            "cargo_lost_share": lambda route, material=None, civilization_id=None, demand=None: 0.1})
        views = {
            "goods_stock": lambda key: self.ledger.get(key, 0.0), "material_commodity": lambda material: material,
            "stock_land": self.land.stock_land, "year": 100, "acting_balance": lambda: self.purse.capital,
            "endemic_stock_loss": self.land.endemic_stock_loss,
            "nursery_room_units": self.land.nursery_room_units,
            "hour_wage": self.workforce.hour_wage, "can_pay": self.purse.can_pay,
            "partners": self.trade.partners, "partner": self.trade.partner,
            "partner_refusal": self.trade.partner_refusal, "partner_gate": self.trade.partner_gate,
            "partner_carry": self.trade.partner_carry,
            "partner_catch_chance": lambda civ, share: bridge.partner_catch_chance(self, civ, share)}
        answers = {
            ChangeStock: lambda command: apply_to_own_stock(self, command),
            PayEdge: lambda command: self.purse.pay(command.amount, command.purpose),
            PressLabour: self.workforce.press_labour,
            RaiseScandal: self.polity.raise_scandal,
            CloseMarketsTo: self.trade.apply_close_markets_to,
            RecordStockTaken: self.trade.apply_record_stock_taken}
        self.module = module_harness.build(LivingStock, views=views, answers=answers, world=LivingStockWorld())
        self.module.clock.act_as("founder")

    @property
    def scandal(self):
        return self.standing.scandal

    @property
    def scandal_last_year(self):
        return self.standing.scandal_last_year

    def grant(self, material, units):
        self.module.change_held(ChangeHeld(material, units))

    def held(self, material):
        return self.module.held(material)

    def smuggle(self, terms):
        """Settle the quoted terms: the outcome, or the refusal when the taker cannot pay."""
        return self.module.smuggle_stock(SmuggleStock(
            terms["material"], terms["partner"], terms["units"], terms["tonnes"], terms["cost"],
            terms["arrives_units"], terms["chance_caught"]))

    @property
    def capital(self):
        return self.purse.capital

    def _material_stock(self):
        return self.ledger

    def _material_opening_stock(self):
        return self.opening

    def partner_government(self, civilization_id):
        return self.actors.get(GOVERNMENT_PREFIX + civilization_id)

    def partner_refusal(self, civilization_id, material):
        return self.trade.partner_refusal(civilization_id, material)

    def view(self, name):
        """The views the bridge reads of a game: the wild stock (whole here), the seeded cast and the actors' world over this game."""
        needs = fake_needs(labour_market=lambda: self.labour.market, civilisation=self.civ, hours_per_person_year=HOURS_PER_PERSON_YEAR,
                           year=100, agent_country=lambda country: self.economy.agent_country(country))
        world = ActorWorld(types.SimpleNamespace(needs=needs, cast=lambda: self.actors))
        return {"wild_stock": lambda: {}, "seeded_actor_registry": lambda: self.actors, "actor_world": lambda: world}[name]


# ---- the stock stands on a tile of the holder's -----------------------------------------------
game = Game()
place = game.land.stock_land()["place"]
check("held stock stands on one of the tiles its holder holds", place in tiles_held(game.civ, game.world_map), place)
check("...the same one each time", game.land.stock_land()["place"] == place)

# ---- a herd grows by its rule when feed and purse allow, and pays its labour ------------------
rates = stock_rates()[HERD]
check("the herd row says it grazes", rates.get("grows_on") == "pasture", rates)
game.grant(HERD, 10000.0)
game.module.step_living_stock("founder")
growth = 10000.0 * rates["natural_increase"]
check("an ample pasture and purse give the stated rule",
      abs(game.held(HERD) - (10000.0 + growth - 10000.0 * rates["annual_loss"])) < 1e-6, game.held(HERD))
entry = stock_entry(HERD)
hours = growth / entry["outputs"][HERD] * sum(entry["labour_hours"].values())   # whichever trades raise the herd
check("the growth is paid for in labour at the going wage",
      game.purse.paid and abs(game.purse.paid[0][1] - hours * WAGE) < 1e-6, game.purse.paid)
check("...and the hours press on the labour market",
      abs(sum(game.labour.market.pressed.values()) - hours) < 1e-6, game.labour.market.pressed)

# ---- pasture limits the increase ------------------------------------------------------------------
_shipped_capacity = stock_land.pasture_capacity_kg
try:
    stock_land.pasture_capacity_kg = lambda tile, wild, world_map: 10500.0 if tile == place else 0.0
    tight = Game()
    tight.grant(HERD, 10000.0)
    tight.module.step_living_stock("founder")
    check("a pasture that carries 500 kg more lets the herd grow by 500 kg less its loss",
          abs(tight.held(HERD) - (10500.0 - 10000.0 * rates["annual_loss"])) < 1e-6, tight.held(HERD))
    stock_land.pasture_capacity_kg = lambda tile, wild, world_map: 9000.0 if tile == place else 0.0
    full = Game()
    full.grant(HERD, 10000.0)
    full.module.step_living_stock("founder")
    check("a herd on pasture with no room gains nothing and still suffers its loss",
          abs(full.held(HERD) - 10000.0 * (1.0 - rates["annual_loss"])) < 1e-6, full.held(HERD))
    check("...and buys no labour for growth it did not make", not full.purse.paid, full.purse.paid)
finally:
    stock_land.pasture_capacity_kg = _shipped_capacity

# ---- the purse limits it too ----------------------------------------------------------------------
poor = Game(capital=0.0)
poor.grant(HERD, 10000.0)
poor.module.step_living_stock("founder")
check("a holder who cannot pay for the labour gets no growth",
      abs(poor.held(HERD) - 10000.0 * (1.0 - rates["annual_loss"])) < 1e-6, poor.held(HERD))
partly = Game(capital=hours * WAGE / 2.0)
partly.grant(HERD, 10000.0)
partly.module.step_living_stock("founder")
check("a holder who can pay for half of it gets half of the growth",
      abs(partly.held(HERD) - (10000.0 + growth / 2.0 - 10000.0 * rates["annual_loss"])) < 1e-6, partly.held(HERD))

# ---- a nursery is held to the arable land of its place ---------------------------------------------
sugar = stock_rates()[SUGAR]
check("the cane row is raised on arable land and no longer capped at a doubling",
      sugar.get("grows_on") == "arable" and sugar["natural_increase"] > 1.0, sugar)
_shipped_arable = stock_land.arable_hectares
try:
    stock_land.arable_hectares = lambda tile, world_map: 0.01
    small = Game()
    small.grant(SUGAR, 5000.0)
    small.module.step_living_stock("founder")
    sett = stock_entry(SUGAR)
    room = 0.01 * sett["outputs"][SUGAR] / sett["land_hectare_years"]
    check("a hundredth of a hectare of land raises only what its output per hectare allows",
          abs(small.held(SUGAR) - (5000.0 + room - 5000.0 * sugar["annual_loss"])) < 1e-6, small.held(SUGAR))
    stock_land.arable_hectares = lambda tile, world_map: 1e9
    wide = Game()
    wide.grant(SUGAR, 5000.0)
    wide.module.step_living_stock("founder")
    check("with land enough the cane multiplies by its sourced rate",
          abs(wide.held(SUGAR) - 5000.0 * (1.0 + sugar["natural_increase"] - sugar["annual_loss"])) < 1e-6,
          wide.held(SUGAR))
finally:
    stock_land.arable_hectares = _shipped_arable
eggs = Game()
eggs.grant(EGGS, 1.0)
eggs.module.step_living_stock("founder")
check("stock that does not breed buys no labour", not eggs.purse.paid and eggs.held(EGGS) < 1.0, eggs.purse.paid)

# ---- the partner sells what it holds and does not hold back -----------------------------------------
buyer = Game()
check("the partner's state holds the eggs back, from its own record",
      cause_of(buyer.partner_refusal(PARTNER, EGGS)) == "partner_export_held_back", buyer.partner_refusal(PARTNER, EGGS))
check("...and does not hold back tea", buyer.partner_refusal(PARTNER, TEA) is None, buyer.partner_refusal(PARTNER, TEA))
check("the partner holds tea stock and cane setts at its date, as data",
      load_civ(PARTNER)["opening_stock"].get(TEA, 0) > 0 and load_civ(PARTNER)["opening_stock"].get(SUGAR, 0) > 0)
quote = buyer.module.stock_smuggle_quote(TEA, 1.0, PARTNER)
check("a partner that sells is not robbed: the quote says to buy",
      not quote["ok"] and quote["cause"] == "partner_sells", quote)

# ---- smuggling what it will not sell ----------------------------------------------------------------
terms = buyer.module.stock_smuggle_quote(EGGS, 0.1, PARTNER)
check("a partner that holds eggs and will not sell them can be robbed", terms["ok"], terms)
tonnes = 0.1 * tonnes_per_unit(EGGS)
check("the carrying is agents and freight over the tonnes, and not the price",
      abs(terms["cost"] - 15.0 * tonnes) < 1e-12, terms["cost"])
check("what the route loses is lost from what arrives", abs(terms["arrives_units"] - 0.09) < 1e-12, terms)
capacity = bridge.partner_catch_chance(buyer, PARTNER, 1.0)
check("the chance of being caught is the state's reach times how much of its holding goes",
      0.0 < terms["chance_caught"] <= capacity, terms["chance_caught"])
bigger = buyer.module.stock_smuggle_quote(EGGS, 0.4, PARTNER)
check("a bigger bite out of its holding is likelier seen", bigger["chance_caught"] > terms["chance_caught"], bigger)
check("more than the partner holds cannot be taken",
      not buyer.module.stock_smuggle_quote(EGGS, 100.0, PARTNER)["ok"])
check("a bad amount is refused", not buyer.module.stock_smuggle_quote(EGGS, 0.0, PARTNER)["ok"])

# not caught
thief = Game()
thief.module.smuggling_draw = lambda terms: 0.999999
terms = thief.module.stock_smuggle_quote(EGGS, 0.1, PARTNER)
outcome = thief.smuggle(terms)
check("a smuggler not caught receives the stock less the route's loss",
      outcome and not outcome["caught"] and abs(thief.held(EGGS) - 0.09) < 1e-9, outcome)
check("...pays the carrying", thief.purse.paid == [("stock smuggled", terms["cost"])], thief.purse.paid)
check("...and the partner has that much less to sell",
      abs(thief.module.partner_holding(PARTNER, EGGS) - (load_civ(PARTNER)["opening_stock"][EGGS] - 0.1)) < 1e-9,
      thief.module.partner_holding(PARTNER, EGGS))
check("...with no scandal and its markets still open", thief.scandal == 0.0
      and thief.partner_government(PARTNER).markets_closed_until("founder", 100) == 0)

# caught
caught = Game()
caught.module.smuggling_draw = lambda terms: 0.0
terms = caught.module.stock_smuggle_quote(EGGS, 0.1, PARTNER)
outcome = caught.smuggle(terms)
check("a smuggler caught is left with nothing", outcome["caught"] and caught.held(EGGS) == 0.0, outcome)
check("...still pays the carrying", caught.purse.paid == [("stock smuggled", terms["cost"])], caught.purse.paid)
check("...has the partner's state shut its markets to him for years",
      caught.partner_government(PARTNER).markets_closed_until("founder", 100) == outcome["closed_until"]
      and outcome["closed_until"] > 100, outcome)
check("...so the partner refuses him, naming the year",
      cause_of(caught.partner_refusal(PARTNER, TEA)) == "partner_market_shut", caught.partner_refusal(PARTNER, TEA))
check("...and the partner still holds all its eggs",
      abs(caught.module.partner_holding(PARTNER, EGGS) - load_civ(PARTNER)["opening_stock"][EGGS]) < 1e-12)
check("...and his scandal at home rises", caught.scandal > 0.0 and caught.scandal_last_year > 0.0, caught.scandal)
check("...but not for another party's purchase", "shut" not in (
    (lambda game: (setattr(game.goods_market, "acting_party_id", "other"), game.partner_refusal(PARTNER, TEA))[1])(caught) or ""))

# cannot pay
broke = Game(capital=0.0)
terms = broke.module.stock_smuggle_quote(EGGS, 0.1, PARTNER)
check("a taker who cannot pay the carrying is refused and nothing happens",
      isinstance(broke.smuggle(terms), Refusal) and broke.held(EGGS) == 0.0 and broke.scandal == 0.0)

# before the roster is seeded the same policy answers from the country's data
unseeded = Game(governed=False)
check("before the roster is seeded the policy answers from the country's data",
      cause_of(unseeded.partner_refusal(PARTNER, EGGS)) == "partner_export_held_back" and unseeded.partner_refusal(PARTNER, TEA) is None)

# ---- planted rubber -------------------------------------------------------------------------------------
RUBBER = "rubber_planting_stock_kg"
rubber_node = NODES.get("ag2_rubber_plantation") or {}
check("a planted-rubber node grants the rubber stock", (rubber_node.get("grants") or {}).get(RUBBER, 0) > 0, rubber_node.get("grants"))
check("it needs a way to the Amazon and the practice of moving a crop",
      {"exp_americas_factory", "exp_transplant_botany"} <= set(rubber_node.get("pre") or ()), rubber_node.get("pre"))
check("the rubber row is a living-stock row with a source and a grade", RUBBER in stock_rates()
      and stock_rates()[RUBBER].get("confidence") in ("C", "D") and len(stock_rates()[RUBBER].get("source", "")) > 40)
check("its nursery entry is gated on the node and works land and labour",
      (stock_entry(RUBBER) or {}).get("requires_node") == "ag2_rubber_plantation"
      and stock_entry(RUBBER).get("land_hectare_years", 0) > 0)
with open(os.path.join(ROOT, "docs", "knowledge", "76_farming_food_deep.md"), encoding="utf-8") as _handle:
    _doc = _handle.read()
check("the node's knowledge section exists and names budding and tapping",
      "### ag2_rubber_plantation" in _doc and "bud" in _doc.split("### ag2_rubber_plantation")[1].lower()
      and "tap" in _doc.split("### ag2_rubber_plantation")[1].lower())
