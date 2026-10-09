"""The `market` screen's numbers: material prices and wages.

Everything here is read from figures the engine already computes
(material_trade_quote, annual_wage); nothing is new economics.
"""

import sim.engine.ui_port as ui_port
from sim.engine.ui_port import WAGES

DEFAULT_MATERIAL_PAGE = 40


def priceable_materials(sim):
    """Every material key the game can quote a price for, sorted."""
    keys = set(ui_port.material_prices(sim)) | set(ui_port.commodity_ledger(sim).commodities)
    keys |= set(ui_port.material_stock(sim)) | set(sim.mine_capacity)
    keys |= {pair[0] for pair in sim.MATERIAL_CHECKS.values()}
    return sorted(key for key in keys if sim.material_trade_quote(key) is not None)



def material_rows(sim, offset, limit):
    """Buy price and own-supply flag for one page of the priceable materials."""
    materials = priceable_materials(sim)
    own_keys = {emp for emp, tag in ui_port.own_production_tags(sim)
                if ui_port.own_material_supply(sim, tag) > 0}
    own = own_keys | {key for key, (emp, _tag) in sim.MATERIAL_CHECKS.items()
                      if emp in own_keys}
    rows = []
    for material in materials[offset:offset + limit]:
        quote = sim.material_trade_quote(material)
        rows.append({"material": material,
                     "buy_per_tonne": round(quote["buy_per_tonne"], 2),
                     "sell_per_tonne": round(quote["sell_per_tonne"], 2),
                     "price_over_long_run_cost": round(quote["market_price_ratio"], 3),
                     "market_available_tonnes_per_year":
                         round(quote["market_available_tonnes_per_year"], 2),
                     "own_supply": material in own,
                     "price_basis": sim.material_price_basis(material)})
    return {"total": len(materials), "offset": offset, "limit": limit, "rows": rows}


def wage_rows(sim):
    """A year of one person of every trade, as `labour <trade>` reports it."""
    return [{"trade": trade, "a_year_of_one": round(sim.labour.market.quote_annual(trade), 0),
             "available_here": bool(sim.labour.trade_available(trade)),
             "you_employ": round(sim.employees.get(trade, 0.0), 2)}
            for trade in sorted(WAGES)]


def market_report(sim, offset=0, limit=DEFAULT_MATERIAL_PAGE):
    return {"ok": True,
            "materials": material_rows(sim, max(0, offset), max(1, limit)),
            "wages": wage_rows(sim)}

