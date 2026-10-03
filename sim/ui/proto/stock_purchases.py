"""`buy living_stock` and its quote: stock bought from a partner economy that sells it.

The quote and the charge are one figure, `Sim.stock_purchase_quote`; a partner that will not sell
refuses with its reason in both.
"""
from sim.engine.ui_port import purchase_rule


def _stock_request(sim, cmd, quantity):
    """(quote, None) for a stock purchase, or (None, error reply)."""
    material = str(cmd.get("material") or "").strip().lower()
    if not material:
        return None, {"ok": False, "error": "say which stock, e.g. buy living_stock ramie_stock_kg 100"}
    partner = str(cmd.get("partner") or "").strip().lower() or None
    quote = sim.stock_purchase_quote(material, quantity, partner)
    if not quote["ok"]:
        return None, {"ok": False, "error": quote["error"] + ". Nothing was changed."}
    return quote, None


def quote_living_stock(sim, cmd, quantity):
    quote, error = _stock_request(sim, cmd, quantity)
    if error:
        return error
    return {"ok": True, "what": "living_stock", "material": quote["material"], "units": quote["units"],
            "partner": quote["partner"], "per_tonne": round(quote["per_tonne"], 2),
            "to_buy_it": round(quote["cost"], 1),
            "you_have": round(sim.capital, 1),
            "you_could_raise": round(purchase_rule.purchase_budget(sim), 1),
            "afford_means": purchase_rule.afford_means(),
            "note": "The partner's own price in your money, plus the merchants' terms and the freight "
                    "over the route. It sells no more than it holds."}


def buy_living_stock(sim, cmd, quantity):
    quote, error = _stock_request(sim, cmd, quantity)
    if error:
        return error
    before = sim.capital
    if not sim.settle_stock_purchase(quote):
        return {"ok": False, "error": "cannot pay %.1f for %s of %s; you could raise %.1f. Nothing was "
                "changed." % (quote["cost"], quote["units"], quote["material"],
                              purchase_rule.purchase_budget(sim))}
    return {"ok": True, "material": quote["material"], "bought_units": quote["units"],
            "partner": quote["partner"], "paid": round(before - sim.capital, 1),
            "held_now": round(sim.stock_held(quote["material"]), 3), "capital": round(sim.capital, 1)}
