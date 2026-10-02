import sys
sys.path.insert(0,'.')
from sim.tests.harness import *
P="han_china_100ad"
s=sim(civ="rome_100ad", capital=1e9)
f=s._foreign_economy_facts(P)
r=f["route"]
print("carriers",s._route_carriers(P,r),"cycle",s._trader_cycle_years(r,P),"voy",s._route_voyage_years(r))
print("lift",s.foreign_lift_capacity_tonnes(P,r),"capPerLift",s._route_capital_per_lift_tonne(r))
print("capital",s.merchant_capital_left(P),"room",s.market_credit_room("merchants"))
print("agent/t",s._agent_cost_per_tonne(P,r),"margin",s._trader_margin_share(P,r),"share",s._trader_cost_share(r,None,P))
t=s.trader_terms(P,f,100.0,10.0); print(t)
print("old coin capital", 0.05*s.home_coin_stock_units())
print("freight",f["freight_per_tonne"], "prices",s._foreign_price_pair("silk_kg",f))
coin=s.civ["coin_standard"]; print("old capital money", 0.05*s.home_coin_stock_units()*coin["kg_per_unit"]*s._material_prices().get(coin["material"],0))
print("merchant annual wage", s.labour_market.quote_annual("merchant"), "labourer", s.labour_market.quote_annual("labourer"))
rec=s.capital_market(); print("supply",rec.supply, "capacity", rec.capacity)
from sim.engine.actors import SimWorld
w=SimWorld(s); print("saving",w.household_saving(), "output", w.society_output())
print([k for k in dir(s) if "trade_hours" in k or "workforce" in k][:10])
for name in ("workforce","labour_pool","trade_headcount"):
    print(name, hasattr(s,name))
wf=getattr(s,"workforce",None)
print(type(wf), getattr(wf,"hours_by_trade",None) and {k:round(v) for k,v in wf.hours_by_trade.items() if v>0})
print(s.population.working_age, s.state.scenario.year)
