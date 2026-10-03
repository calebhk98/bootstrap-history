"""The `market` screen's numbers: goods saturation, material prices, wages.

Everything here is read from figures the engine already computes
(goods_market_factor, material_trade_quote, annual_wage); nothing is new
economics.
"""

from sim.engine.data import WAGES

DEFAULT_MATERIAL_PAGE = 40


def priceable_materials(sim):
    """Every material key the game can quote a price for, sorted."""
    keys = set(sim._material_prices()) | set(sim._commodity_ledger().commodities)
    keys |= set(sim._material_stock()) | set(sim.mine_capacity)
    keys |= {pair[0] for pair in sim.MATERIAL_CHECKS.values()}
    return sorted(key for key in keys if sim.material_trade_quote(key) is not None)


def goods_saturation(sim):
    """One row per goods category the player's operating concerns sell into."""
    by_category = {}
    for node_id in sorted(sim.state.projects.operating):
        category = sim.nodes[node_id].get("cat")
        if category in sim.GOODS_CATEGORIES:
            by_category.setdefault(category, []).append(node_id)
    rows = []
    for category, concerns in sorted(by_category.items()):
        quoted = earned = 0.0
        for node_id in concerns:
            node_quoted = sim.nodes[node_id]["rev"] * sim.venture_ramp(node_id) * sim.price_index
            quoted += node_quoted
            earned += node_quoted * sim.goods_market_factor(node_id)
        rows.append({"category": category, "concerns": concerns,
                     "quoted_per_year": round(quoted, 1),
                     "earned_per_year": round(earned, 1),
                     "share_of_quoted_earned": round(earned / quoted, 3) if quoted > 0 else 1.0})
    return rows


def goods_demand(sim):
    """One row per goods category in the game, whether or not you sell there yet."""
    rows = []
    for category in sorted(sim.GOODS_CATEGORIES):
        mine = sum(1 for node_id in sim.state.projects.operating
                   if sim.nodes[node_id].get("cat") == category)
        ratios = sim._goods_category_ratios(category) if mine else None
        rows.append({"category": sim.fog_scrub(category), "concerns_of_yours": mine,
                     "sale_price_vs_opening": round(ratios[0], 3) if ratios else None,
                     "quantity_vs_opening": round(ratios[1], 3) if ratios else None,
                     "new_concern_earns_share":
                         round(sim.goods_category_factor_with_entrants(category, 1), 3)})
    return rows


def material_rows(sim, offset, limit):
    """Buy price and own-supply flag for one page of the priceable materials."""
    materials = priceable_materials(sim)
    own_keys = {emp for emp, tag in sim._own_production_tags()
                if sim._own_material_supply(tag) > 0}
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
    return [{"trade": trade, "a_year_of_one": round(sim.labour_market.quote_annual(trade), 0),
             "available_here": bool(sim.labour.trade_available(trade)),
             "you_employ": round(sim.employees.get(trade, 0.0), 2)}
            for trade in sorted(WAGES)]


def market_report(sim, offset=0, limit=DEFAULT_MATERIAL_PAGE):
    return {"ok": True, "goods": goods_saturation(sim),
            "demand": goods_demand(sim),
            "materials": material_rows(sim, max(0, offset), max(1, limit)),
            "wages": wage_rows(sim)}


def goods_market_line(sim, node_id):
    """One sentence on the goods category a concern sells into and how
    saturated it is, or None for a node that is not a goods concern."""
    category = sim.nodes[node_id].get("cat")
    if category not in sim.GOODS_CATEGORIES or not sim.nodes[node_id].get("rev"):
        return None
    factor = sim.goods_market_factor_if_opened(node_id)
    if factor is None:
        return None
    rivals = [other for other in sim.state.projects.operating
              if other != node_id and sim.nodes[other].get("cat") == category]
    verb = "earns" if node_id in sim.state.projects.operating else "would earn"
    return ("Sells into the %s market, where %d other concern%s of yours also sell; it %s "
            "about %d%% of its quoted figure there. 'market' shows every category."
            % (category, len(rivals), "" if len(rivals) == 1 else "s", verb,
               round(factor * 100)))


def opening_effect(sim, node_id):
    """What opening an unopened goods concern would do to revenue: its own take,
    and what the concerns of yours already selling in the category would lose."""
    category = sim.nodes[node_id].get("cat")
    if (category not in sim.GOODS_CATEGORIES or not sim.nodes[node_id].get("rev")
            or node_id in sim.state.projects.operating):
        return None
    factor_new = sim.goods_category_factor_with_entrants(category, 1)
    rivals = [other for other in sorted(sim.state.projects.operating)
              if sim.nodes[other].get("cat") == category]
    factor_now = sim.goods_category_factor(category) if rivals else factor_new
    changes = [{"id": other, "change_per_year": round(
        sim.nodes[other]["rev"] * sim.venture_ramp(other) * sim.price_index * (factor_new - factor_now), 1)}
        for other in rivals]
    existing = sum(row["change_per_year"] for row in changes)
    own = round(sim.nodes[node_id]["rev"] * sim.price_index * factor_new, 1)
    return {"category": category, "new_concern_earns_per_year": own,
            "existing_concerns_change_per_year": round(existing, 1),
            "net_change_per_year": round(own + existing, 1),
            "existing_concerns": changes,
            "basis": "at maturity, before upkeep; the same market curve 'market' shows"}
