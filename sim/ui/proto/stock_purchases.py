"""`buy living_stock` and its quote: stock bought from a partner economy that sells it.

The quote and the charge are one figure, `Sim.stock_purchase_quote`; a partner that will not sell
refuses with its reason in both.
"""
from sim.engine.ui_port import money_text, purchase_rule


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
        return {"ok": False, "error": "cannot pay %s for %s of %s; you could raise %s. Nothing was "
                "changed." % (money_text(quote["cost"], sim, digits=1), quote["units"], quote["material"],
                              money_text(purchase_rule.purchase_budget(sim), sim, digits=1))}
    return {"ok": True, "material": quote["material"], "bought_units": quote["units"],
            "partner": quote["partner"], "paid": round(before - sim.capital, 1),
            "held_now": round(sim.stock_held(quote["material"]), 3), "capital": round(sim.capital, 1)}


def _smuggle_request(sim, cmd, quantity):
    """(terms, None) for a smuggling attempt, or (None, error reply)."""
    material = str(cmd.get("material") or "").strip().lower()
    if not material:
        return None, {"ok": False, "error": "say which stock, e.g. buy smuggled_stock silkworm_eggs_kg 0.1"}
    partner = str(cmd.get("partner") or "").strip().lower() or None
    terms = sim.stock_smuggle_quote(material, quantity, partner)
    if not terms["ok"]:
        return None, {"ok": False, "error": terms["error"] + ". Nothing was changed."}
    return terms, None


def quote_smuggled_stock(sim, cmd, quantity):
    terms, error = _smuggle_request(sim, cmd, quantity)
    if error:
        return error
    return {"ok": True, "what": "smuggled_stock", "material": terms["material"], "units": terms["units"],
            "partner": terms["partner"], "to_buy_it": round(terms["cost"], 1),
            "chance_caught": round(terms["chance_caught"], 3),
            "arrives_units": round(terms["arrives_units"], 6),
            "you_have": round(sim.capital, 1),
            "note": "Taking stock from a partner that will not sell it. You pay the carrying whatever happens. "
                    "If the partner's state catches you the stock is seized, it shuts its markets to you for "
                    "years and your scandal rises; if not, the stock arrives less what the route loses."}


def buy_smuggled_stock(sim, cmd, quantity):
    terms, error = _smuggle_request(sim, cmd, quantity)
    if error:
        return error
    before = sim.capital
    outcome = sim.settle_stock_smuggle(terms)
    if not outcome:
        return {"ok": False, "error": "cannot pay %s to carry %s of %s. Nothing was changed."
                % (money_text(terms["cost"], sim, digits=1), terms["units"], terms["material"])}
    reply = {"ok": True, "material": terms["material"], "partner": terms["partner"], "caught": outcome["caught"],
             "delivered_units": round(outcome["delivered_units"], 6), "paid": round(before - sim.capital, 1),
             "held_now": round(sim.stock_held(terms["material"]), 3), "capital": round(sim.capital, 1)}
    if outcome["caught"]:
        reply["note"] = ("Caught: the stock was seized, %s has shut its markets to you until year %d, and your "
                         "scandal rose." % (terms["partner"], outcome["closed_until"] or 0))
    return reply
