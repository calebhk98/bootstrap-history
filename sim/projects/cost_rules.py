"""The figures every screen quotes for a project, as plain functions: the cost of starting now and what opposition adds
(a concern's running cost is the ventures module's)."""


def cost_if_started_now(cost_without_materials, missing_materials_cost, material_cost_factor, opposition_factor):
    """Labour and capital plus the materials not already held, at the geography and opposition factors."""
    return (cost_without_materials + missing_materials_cost) * material_cost_factor * opposition_factor


def opposition_factor(state_interest, cost_per_unit):
    """Opposed work costs more: bribes, delay, a provincial site, a front man."""
    return 1.0 + cost_per_unit * max(0.0, -state_interest)
