"""`quote` for the `buy` targets whose price is a flat unit price.

Each quoter mirrors the price its `buy` handler charges and the rule that
handler refuses on, and returns a reply dict (or an error dict).
"""

from sim.engine.ui_port import purchase_rule
from .stock_purchases import quote_living_stock


def _flat_unit_quote(sim, what, unit_name, unit_price, quantity, note, **extra):
    total = unit_price * quantity
    return dict({
        "ok": True, "what": what, unit_name: quantity,
        "to_buy_it": round(total, 1),
        "per_unit": round(unit_price, 2),
        "you_have": round(sim.capital, 1),
        "you_can_afford_about": (int(sim.capital / unit_price) if unit_price > 0 else None),
        "note": note}, **extra)


def _quote_farm(sim, cmd, quantity):
    return _flat_unit_quote(
        sim, "farm", "hectares", sim.farm_price_per_hectare(), quantity,
        "Farmland is bought once and lowers the staple price for everyone you feed.")


def _quote_housing(sim, cmd, quantity):
    return _flat_unit_quote(
        sim, "housing", "places", sim.housing_price_per_place(), quantity,
        "Worker housing is bought once and adds places for people you employ.")


def _quote_school(sim, cmd, quantity):
    trade = str(cmd.get("trade") or cmd.get("material") or "").lower()
    if not trade:
        return {"ok": False, "error": "say which trade, e.g. quote school smith 2"}
    reply = _flat_unit_quote(
        sim, "school", "seats", sim.trade_school_price_per_seat(),
        quantity, "Each seat widens the annual supply of that trade locally.",
        trade=trade)
    if not sim.labour.trade_available(trade):
        reply["warning"] = ("%s is not available here yet, so a school for it "
                            "would be refused; teach or discover it first" % trade)
    return reply


def _quote_material(sim, cmd, quantity):
    quote = sim.material_trade_quote(cmd.get("material"))
    if quote is None:
        return {"ok": False, "error": "material %r cannot be bought: no one in reach makes or sells it, so it has "
                                      "no price (a technique that makes it, a route to a partner that does, or "
                                      "a partner that gains it would give it one); 'materials' lists the ones "
                                      "with a market" % (cmd.get("material"),)}
    tonnes = min(quantity, quote["market_available_tonnes_per_year"])
    total = sim.material_purchase_cost(quote["material"], tonnes)[0]
    return {"ok": True, "what": "material", "material": quote["material"],
            "tonnes": quantity, "per_tonne": round(quote["buy_per_tonne"], 2),
            "average_per_tonne_for_this_order": round(total / tonnes, 2) if tonnes > 0 else None,
            "to_buy_it": round(total, 1),
            "sells_back_per_tonne": round(quote["sell_per_tonne"], 2),
            "market_available_tonnes_per_year":
                round(quote["market_available_tonnes_per_year"], 2),
            "you_have": round(sim.capital, 1),
            "you_could_raise": round(purchase_rule.purchase_budget(sim), 1),
            "afford_means": purchase_rule.afford_means(),
            "note": ("The market will sell at most %.1f tonnes a year, so a larger "
                     "order is cut to that." % quote["market_available_tonnes_per_year"]
                     if quantity > quote["market_available_tonnes_per_year"] else
                     "The price rises as the order is filled, and moves as you and others buy.")}


def _quote_manumit(sim, cmd, quantity):
    return {"ok": True, "what": "manumit", "people": quantity, "to_buy_it": 0.0,
            "you_hold": sim.slaves,
            "note": "Freeing people costs no money; they then work better."}


# canonical buy target -> quoter, for the targets not quoted in dispatch_money itself
FLAT_QUOTERS = {
    "farm": _quote_farm,
    "housing": _quote_housing,
    "school": _quote_school,
    "material": _quote_material,
    "manumit": _quote_manumit,
    "living_stock": quote_living_stock,
}
