"""The `market` screen's numbers: material prices and wages.

Everything here is read from figures the engine already computes
(material_trade_quote, annual_wage); nothing is new economics.
"""

import difflib

import sim.engine.ui_port as ui_port
from sim.engine.ui_port import WAGES

DEFAULT_MATERIAL_PAGE = 40


def priceable_materials(sim):
    """Every material key the game can quote a price for, sorted."""
    keys = set(ui_port.material_prices(sim)) | set(ui_port.commodity_ledger(sim).commodities)
    keys |= set(ui_port.material_stock(sim)) | set(sim.view("mine_capacity")())
    keys |= {pair[0] for pair in sim.view("material_checks")().values()}
    return sorted(key for key in keys if sim.view("goods_quote")[key] is not None)



def material_rows(sim, offset, limit, only=None):
    """Buy price and own-supply flag for one page of the priceable materials, or for the one named."""
    materials = [only] if only else priceable_materials(sim)
    if only:
        offset, limit = 0, 1
    own_keys = {emp for emp, tag in ui_port.own_production_tags(sim)
                if ui_port.own_material_supply(sim, tag) > 0}
    own = own_keys | {key for key, (emp, _tag) in sim.view("material_checks")().items()
                      if emp in own_keys}
    rows = []
    for material in materials[offset:offset + limit]:
        quote = sim.view("goods_quote")[material]
        rows.append({"material": material,
                     "buy_per_tonne": round(quote["buy_per_tonne"], 2),
                     "sell_per_tonne": round(quote["sell_per_tonne"], 2),
                     "price_over_long_run_cost": (
                         None if not quote["making_cost_per_tonne"]
                         else round(quote["price_at_tile_per_tonne"] / quote["making_cost_per_tonne"], 3)),
                     "market_available_tonnes_per_year":
                         round(quote["market_available_tonnes_per_year"], 2),
                     "own_supply": material in own,
                     "price_basis": sim.view("material_price_basis")[material],
                     "price_kind": quote["price_kind"]})
    return {"total": len(materials), "offset": offset, "limit": limit, "rows": rows}


def wage_rows(sim):
    """A year of one person of every trade, as `labour <trade>` reports it."""
    return [{"trade": trade, "a_year_of_one": round(sim.labour.market.quote_annual(trade), 0),
             "available_here": bool(sim.labour.trade_available(trade)),
             "you_employ": round(sim.view("staff")()["employees"].get(trade, 0.0), 2)}
            for trade in sorted(WAGES)]


def unknown_material_reply(material, known):
    """The refusal of a material with no price: the near misses among the `known` ones, and where to see them all."""
    wanted = str(material).strip().lower()
    near = difflib.get_close_matches(wanted, known, n=5, cutoff=0.5) or [key for key in known if wanted in key][:5]
    return {"ok": False, "error": "no material called %r has a price here%s. 'market' lists them all."
            % (material, "; did you mean: " + ", ".join(near) if near else "")}


def market_report(sim, offset=0, limit=DEFAULT_MATERIAL_PAGE, material=None):
    """The market screen; `material` narrows the table to that one (and drops the wages), or is refused with suggestions."""
    if material:
        known = priceable_materials(sim)
        wanted = str(material).strip().lower()
        if wanted not in known:
            return unknown_material_reply(material, known)
        return {"ok": True, "materials": material_rows(sim, 0, 1, only=wanted), "wages": []}
    return {"ok": True,
            "materials": material_rows(sim, max(0, offset), max(1, limit)),
            "wages": wage_rows(sim)}

