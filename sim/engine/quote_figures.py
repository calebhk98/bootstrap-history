"""The figure every screen quotes for a project: the cost of starting now (a concern's running cost is the ventures module's)."""


def cost_if_started_now(cost_without_materials, missing_materials_cost, material_cost_factor, opposition_factor):
    """Labour and capital plus the materials not already held, at the geography and opposition factors."""
    return (cost_without_materials + missing_materials_cost) * material_cost_factor * opposition_factor
