"""Buying living stock from a partner economy: one quote, the same figure charged.

A partner sells a stock material it holds and makes, at its price in home money plus the merchants'
terms and the route's freight (`partner_quote_per_tonne`), unless its own policy refuses
(`partner_refusal`). The payment and the delivery go through the one goods market
(`GoodsMarket.settle_import`); the quote a player reads is built by the function the charge uses.
"""
from .data import load_civ
from .material_units import tonnes_per_unit


class LivingStockTradeMixin:

    def _partner_holding(self, civilization_id, material):
        """Units of the material the partner held at its date (its `opening_stock`). TRANSITIONAL
        HEURISTIC: the partner's stock is not simulated, so what it can sell is what it started
        with, not what it still has; a partner's own ledger would replace this."""
        return float((load_civ(civilization_id).get("opening_stock") or {}).get(material, 0.0))

    def stock_purchase_quote(self, material, units, partner=None):
        """What buying `units` of a stock material costs, from the named partner or the cheapest that
        sells it: {"ok": True, partner, units, tonnes, per_tonne, cost}, else {"ok": False, "error"}."""
        units = float(units)
        if units <= 0.0:
            return {"ok": False, "error": "buy a positive amount of %s" % material}
        trading = self.foreign_economies()
        if partner and partner not in trading:
            return {"ok": False, "error": "%s is not trading with you this year; those that are: %s"
                    % (partner, ", ".join(trading) or "none")}
        refusals, offers, holdings = [], [], []
        for candidate in ([partner] if partner else trading):
            refusal = self.partner_refusal(candidate, material)
            per_tonne = None if refusal else self.partner_quote_per_tonne(material, candidate)
            if refusal:
                refusals.append(refusal)
            elif per_tonne is not None and self._partner_holding(candidate, material) > 0.0:
                if units > self._partner_holding(candidate, material) + 1e-9:
                    holdings.append("%s holds only %.6g %s" % (
                        candidate, self._partner_holding(candidate, material), material))
                else:
                    offers.append((per_tonne, candidate))
        if not offers:
            reason = (refusals or holdings or ["no partner you trade with sells %s" % material])[0]
            return {"ok": False, "error": reason}
        per_tonne, seller = min(offers)
        tonnes = units * tonnes_per_unit(material)
        return {"ok": True, "material": material, "units": units, "partner": seller,
                "tonnes": tonnes, "per_tonne": per_tonne, "cost": per_tonne * tonnes}

    def buy_stock_from_partner(self, material, units, civilization_id=None):
        """Buy units of a stock material from a partner economy; returns the units bought (0 when the
        partner refuses, cannot supply it, or the buyer cannot pay)."""
        quote = self.stock_purchase_quote(material, units, civilization_id)
        if not quote["ok"] or not self.settle_stock_purchase(quote):
            return 0.0
        return quote["units"]

    def settle_stock_purchase(self, quote):
        """Pay a quote through the goods market and receive the stock; False when the buyer cannot
        pay. The partner is paid in its own coin's metal, as every foreign payment is."""
        buyer = self.goods_market.acting
        if not buyer.can_pay(quote["cost"]):
            return False
        self.goods_market.settle_import(
            buyer, self._stock_key(quote["material"]), quote["tonnes"], quote["cost"], "stock bought abroad")
        coin = load_civ(quote["partner"])["coin_standard"]
        coin_price = self._coin_metal_price(coin["material"])
        if coin_price:
            self._settle_flow(quote["partner"], quote["tonnes"], quote["cost"],
                              coin["kg_per_unit"] * coin_price)
        return True
