"""The two figures every screen quotes for a project or a concern: the cost of starting now, the yearly running cost."""


def cost_if_started_now(cost_without_materials, missing_materials_cost, material_cost_factor, opposition_factor):
    """Labour and capital plus the materials not already held, at the geography and opposition factors."""
    return (cost_without_materials + missing_materials_cost) * material_cost_factor * opposition_factor


def upkeep_quote(upkeep_now, upkeep_at_full_staffing, price_index):
    """Yearly running cost at the current price level: as staffed today (what the ledger charges) and with every place filled."""
    return {"now": upkeep_now * price_index, "at_full_staffing": upkeep_at_full_staffing * price_index}
