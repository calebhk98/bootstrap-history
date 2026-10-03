"""Merchants' terms come from what being a merchant costs (Complaints/346): money tied up at the
market rate over the voyage and the wait, agents' wages from the labour market, expected loss, the
capital a merchant class can raise, and competition that shrinks the margin above cost."""
from .harness import *  # noqa: F401,F403

from sim.world import market, merchant_terms, trader_response

PARTNER = "han_china_100ad"


def stubbed(simulation, home_price=100.0, foreign_price=10.0):
    simulation._foreign_price_pair = lambda commodity, facts: (home_price, foreign_price)
    simulation._foreign_sides = lambda commodity, facts: (True, True)
    simulation._output_is_sourced = lambda commodity: True
    simulation.foreign_opening = lambda civilization_id, commodity, solved: (500.0, 500.0)
    simulation.foreign_economies = lambda: [PARTNER]
    simulation.household._foreign_facts_cache = None
    return simulation


# --- pure terms.
check("more competing merchants shrink the markup toward zero",
      merchant_terms.competition_markup_share(1) > merchant_terms.competition_markup_share(5)
      > merchant_terms.competition_markup_share(50) > 0.0
      and merchant_terms.competition_markup_share(10 ** 9) < 1e-6, None)
check("the markup is the monopoly markup for one merchant",
      abs(merchant_terms.competition_markup_share(1) - merchant_terms.MONOPOLY_MARKUP_SHARE) < 1e-12, None)
check("goods wait less for a sailing when more carriers serve the route",
      merchant_terms.wait_years(2.0, 10.0) > merchant_terms.wait_years(2.0, 40.0) > 0.0
      and merchant_terms.wait_years(2.0, float("inf")) == 0.0, None)
check("a carrier on a longer round trip redirects a smaller share of the flow in a year",
      merchant_terms.redirect_share_per_year(0.5) == 1.0
      and merchant_terms.redirect_share_per_year(4.0) < merchant_terms.redirect_share_per_year(2.0) < 1.0, None)
check("merchants borrow against their own capital, up to what lenders will advance",
      merchant_terms.capital_to_finance(100.0, credit_room=None) > 100.0
      and merchant_terms.capital_to_finance(100.0, credit_room=10.0) == 110.0
      and merchant_terms.capital_to_finance(0.0, credit_room=1e9) == 0.0, None)

# --- a dearer cost of capital raises the charge over freight.
cheap_money = stubbed(sim(civ="rome_100ad", capital=1e9))
dear_money = stubbed(sim(civ="rome_100ad", capital=1e9))
cheap_money.market_rate = lambda: 0.04
dear_money.market_rate = lambda: 0.20
facts = cheap_money._foreign_economy_facts(PARTNER)
check("a dearer cost of capital raises the merchants' charge over freight",
      dear_money.trader_terms(PARTNER, facts, 100.0, 10.0).cost_share_of_price
      > cheap_money.trader_terms(PARTNER, facts, 100.0, 10.0).cost_share_of_price, None)

# --- more merchants on a route lower the margin above cost.
few = stubbed(sim(civ="rome_100ad", capital=1e9))
many = stubbed(sim(civ="rome_100ad", capital=1e9))
many._foreign_ledger(PARTNER, create=True)["lift_tonnes_per_year"] = (
    20.0 * few.foreign_lift_capacity_tonnes(PARTNER, facts["route"]))
check("a larger fleet means more merchants",
      many._route_carriers(PARTNER, facts["route"]) > 10.0 * few._route_carriers(PARTNER, facts["route"]), None)
check("more competing merchants on a route lower the margin above cost",
      many._trader_margin_share(PARTNER, facts["route"]) < few._trader_margin_share(PARTNER, facts["route"]), None)
check("...and the goods wait less to be shipped",
      many._trader_cycle_years(facts["route"], PARTNER) < few._trader_cycle_years(facts["route"], PARTNER), None)
check("agents' pay comes from the labour market: a dearer merchant costs more per tonne",
      few._agent_cost_per_tonne(PARTNER, facts["route"]) > 0.0, None)
dearer_agents = stubbed(sim(civ="rome_100ad", capital=1e9))
dearer_agents.labour.market.quote = lambda trade, hours=0.0, employer=None: 2.0 * few.labour.market.quote(trade)
check("...and doubling merchants' wage doubles it",
      abs(dearer_agents._agent_cost_per_tonne(PARTNER, facts["route"])
          - 2.0 * few._agent_cost_per_tonne(PARTNER, facts["route"])) < 1e-9, None)

# --- trade grows no faster than lift and merchants' capital allow.
terms = few.trader_terms(PARTNER, facts, 100.0, 10.0)
home = market.MarketConditions(household_demand_at_anchor_tonnes=1e6, committed_demand_tonnes=0.0,
                               society_capacity_tonnes=0.0, actor_supply_tonnes=0.0,
                               founder_sales_tonnes=0.0, stock_tonnes=0.0)
abroad = market.MarketConditions(household_demand_at_anchor_tonnes=1.0, committed_demand_tonnes=0.0,
                                 society_capacity_tonnes=1e6, actor_supply_tonnes=0.0,
                                 founder_sales_tonnes=0.0, stock_tonnes=0.0)
lift = few.foreign_lift_capacity_tonnes(PARTNER, facts["route"])
flows = []
previous = 0.0
for _year in range(6):
    outcome = trader_response.clear_with_traders(home, abroad, 100.0, 10.0, 1.0, terms, previous, lift, lift)
    previous = outcome.flow_tonnes
    flows.append(previous)
check("whatever the gap, the flow stays within the lift and the capital merchants can raise",
      max(flows) <= min(lift, terms.capital_tonnes_in) * (1.0 + 1e-9) and max(flows) > 0.0, (flows, lift, terms))
check("a merchant class with no capital moves no goods",
      few.merchant_capital_left(PARTNER) > 0.0
      and trader_response.clear_with_traders(
          home, abroad, 100.0, 10.0, 1.0,
          trader_response.TraderTerms(0.1, 1.0, capital_tonnes_in=0.0), 0.0, lift, lift).flow_tonnes == 0.0, None)
larger = stubbed(sim(civ="rome_100ad", capital=1e9))
larger._foreign_ledger(PARTNER, create=True)["merchant_retained"] = 10.0 * few.merchant_capital_left(PARTNER)
check("retained earnings raise the capital merchants can put into goods",
      larger.merchant_capital_left(PARTNER) > few.merchant_capital_left(PARTNER), None)
check("the speed of adjustment is the share of carriers that can change cargo in a year, not a fixed share",
      terms.adjustment_share == merchant_terms.redirect_share_per_year(
          2.0 * sum(leg.travel_days for leg in facts["route"].legs) / 365.0), terms)
