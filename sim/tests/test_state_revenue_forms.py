"""Complaint 315: a state's revenue is what its declared forms yield on the bases the simulation models
(harvest, people, trade, coin held), not a fitted share of labour value. Some forms are paid in kind and
arrive as goods in the state's stores, to be used or sold through the goods market."""
from .harness import *  # noqa: F401,F403
from functools import partial

sim = partial(sim, agent_economy=False)   # these checks pin the engine's own loanable-funds market, wage table and state budget


from sim.agents import SimWorld
from sim.agents import budget_lines, revenue

HARVEST_KG = 4.0e9


def one_year(game):
    game.state.scenario.year += 1
    game.advance_actors(game.state.scenario.year)


def declared(game, forms):
    game.civ["state_revenue"] = forms
    return SimWorld(game)


LAND = {"form": "land_tax", "basis": "harvest", "rate": 0.1, "paid_in": "wheat_kg"}
POLL = {"form": "poll_tax", "basis": "adult_labour_years", "rate": 0.02}
IMPORTS = {"form": "import_duty", "basis": "imports_value", "rate": 0.025}
EXPORTS = {"form": "export_duty", "basis": "exports_value", "rate": 0.05}
WEALTH = {"form": "wealth_tax", "basis": "coin_stock", "rate": 0.01}

# ---- every civilisation declares its forms, each with a rate, a basis and a source ----------------
for civ_id in ("rome_100ad", "han_china_100ad", "norse_900ad", "mexica_1500", "england_1300"):
    forms = sim(civ=civ_id).civ.get("state_revenue")
    check("%s declares the forms its state raises revenue by" % civ_id, bool(forms), forms)
    check("%s's forms each name a basis the engine models, a rate and where the rate comes from" % civ_id,
          all(form["basis"] in revenue.BASES and form["rate"] > 0.0 and form.get("_internal", {}).get("source")
              for form in forms or []), forms)

# ---- revenue is the sum of the forms assessed on their bases --------------------------------------
game = sim()
game.state.economy.farm_last_harvest_kg = HARVEST_KG
year = game.state.scenario.year
game.state.economy.foreign_trade_by_year = {str(year - 1): {"in": 6.0e9, "out": 2.0e9}}
world = declared(game, [LAND, POLL, IMPORTS, EXPORTS, WEALTH])
wheat_price = game.material_purchase_cost("wheat_kg", 1.0)[0]
labour_year = world.pay_per_person_year("labourer")
coin = game.civ["coin_standard"]
coin_value = game.home_coin_stock_units() * coin["kg_per_unit"] * game._material_prices()[coin["material"]]
expected = {
    "land_tax": 0.1 * HARVEST_KG / 1000.0 * wheat_price,
    "poll_tax": 0.02 * (game.population.working_age - world.soldiers_under_arms()) * labour_year,
    "import_duty": 0.025 * 6.0e9,
    "export_duty": 0.05 * 2.0e9,
    "wealth_tax": 0.01 * coin_value,
}
by_form = {assessed.form: assessed for assessed in revenue.assess(world)}
check("each declared form is assessed once", sorted(by_form) == sorted(expected), sorted(by_form))
for form, money in expected.items():
    check("%s is its rate times the modelled base" % form,
          abs(by_form[form].money - money) < 1e-6 * money, (form, by_form[form].money, money))
check("the state's revenue is the sum of the forms",
      abs(world.state_revenue() - sum(expected.values())) < 1e-6 * sum(expected.values()),
      (world.state_revenue(), sum(expected.values())))

# ---- nothing declared, nothing raised; the old fitted share no longer sets it ----------------------
none = declared(sim(), [])
check("a state that declares no form raises no revenue", none.state_revenue() == 0.0, none.state_revenue())
fitted = sim()
before = declared(fitted, [POLL]).state_revenue()
fitted.civ["starting_tax_share"] = 0.9
check("the civilisation's fitted tax share does not set the state's revenue",
      abs(SimWorld(fitted).state_revenue() - before) < 1e-9 * before, (SimWorld(fitted).state_revenue(), before))
bigger = sim()
bigger.state.economy.farm_last_harvest_kg = 2.0 * HARVEST_KG
smaller = sim()
smaller.state.economy.farm_last_harvest_kg = HARVEST_KG
check("a larger harvest yields a larger land tax",
      declared(bigger, [LAND]).state_revenue() > 1.9 * declared(smaller, [LAND]).state_revenue())
quiet = sim()
busy = sim()
busy.state.economy.foreign_trade_by_year = {str(busy.state.scenario.year - 1): {"in": 6.0e9, "out": 2.0e9}}
check("trade duties follow the trade that crossed the border",
      declared(quiet, [IMPORTS, EXPORTS]).state_revenue() == 0.0 < declared(busy, [IMPORTS, EXPORTS]).state_revenue())

# ---- in-kind revenue arrives as goods and goes through the goods market ---------------------------
kind = sim()
kind.state.economy.farm_last_harvest_kg = HARVEST_KG
treasury = kind.state_treasury()
treasury.money = 0.0
declared(kind, [LAND])
tithe = 0.1 * HARVEST_KG / 1000.0
one_year(kind)
check("a share of the harvest taken in kind is recorded as goods received, in tonnes",
      abs(treasury.record.in_kind_received.get("wheat_kg", 0.0) - tithe) < 1e-6 * tithe,
      treasury.record.in_kind_received)
check("in-kind revenue is not booked as coin taxation", treasury.record.income.get("taxation", 0.0) == 0.0,
      treasury.record.income)
check("the revenue by form is recorded in money's worth, for the audit",
      treasury.record.revenue_by_form.get("land_tax", 0.0) > 0.0, treasury.record.revenue_by_form)
commodity = SimWorld(kind).commodity_of("wheat_kg")
dole = budget_lines.dole_line(SimWorld(kind))[0].materials[commodity]
sold = kind._market_flows()["sold"].get(commodity, {}).get(treasury.actor_id, 0.0)
bought = kind._market_flows()["bought"].get(commodity, {}).get(treasury.actor_id, 0.0)
check("grain the dole needs comes out of the stores, so the state buys none of it", bought == 0.0, (bought, dole))
check("grain beyond what its lines use is sold into the goods market",
      sold > 0.0 and abs(sold + dole + treasury.record.stores.get("wheat_kg", 0.0) - tithe) < 1e-6 * tithe,
      (sold, dole, treasury.record.stores, tithe))
check("the sale is paid into the purse at the market's price",
      treasury.record.income.get("sale of stores", 0.0) > 0.0, treasury.record.income)
check("the purse still equals income less outlays",
      abs(treasury.money - (sum(treasury.record.income.values()) - sum(treasury.record.outlays.values())))
      < 1e-6 * abs(treasury.record.income.get("sale of stores", 1.0)), treasury.money)
