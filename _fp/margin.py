import sys
sys.path.insert(0, ".")
from sim import foreign_trade_report as r
P = "han_china_100ad"
g = r.build("rome_100ad", P)
print("year carriers cycle_y markup cost_share(silk) agent/t capital_left retained silk_t cassia_t cloth_t lift")
for y in range(1, 101):
    g.step()
    if y % 10 == 0 or y == 1:
        f = g._foreign_economy_facts(P); rt = f["route"]
        led = g._foreign_ledger(P)
        book = g.state.economy.market_book
        t = lambda c: book.get(c, {}).get("trade_tonnes", 0.0)
        print(y, round(g._route_carriers(P, rt), 1), round(g._trader_cycle_years(rt, P), 3),
              round(g._trader_margin_share(P, rt), 4), round(g._trader_cost_share(rt, "silk_kg", P), 4),
              round(g._agent_cost_per_tonne(P, rt), 1), "%.3g" % g.merchant_class_capital(),
              "%.3g" % led["merchant_retained"], round(t("silk_kg"), 1), round(t("cassia_kg"), 1),
              round(t("cloth"), 1), round(led["lift_tonnes_per_year"], 0))
