"""Pure, opt-in validation of state produced by one simulation turn."""
import math

VALID_PROJECT_STATUSES = frozenset(("ACTIVE", "PAUSED", "BLOCKED", "BLOCKED_INPUTS"))


def check_simulation_invariants(state):
    """Assert cross-subsystem rules without repairing or consulting globals."""
    demographics = {
        "children": state.population.pop_children,
        "working_age": state.population.pop_working_age,
        "elderly": state.population.pop_elderly,
    }
    for key, value in demographics.items():
        assert math.isfinite(value) and value >= 0.0, \
            "invalid demographic %s=%r" % (key, value)
    economy = state.economy
    for key, value in (economy._material_stock_ledger or {}).items():
        assert math.isfinite(value) and value >= -1e-9, \
            "negative or non-finite physical stockpile %s=%r" % (key, value)
    assert math.isfinite(economy.farm_stock_kg) and economy.farm_stock_kg >= -1e-9, \
        "negative or non-finite physical stockpile grain=%r" % economy.farm_stock_kg
    for key, value in (getattr(economy, "commodity_prices", None) or {}).items():
        assert math.isfinite(value) and value >= 0.0, \
            "negative or non-finite commodity price %s=%r" % (key, value)
    allocated_fte = 0.0
    for project_id, project in state.projects.active.items():
        status = project.get("status")
        assert status in VALID_PROJECT_STATUSES, \
            "active project %s has invalid status %r" % (project_id, status)
        for field in ("hours_offered_this_year", "hours_directed_this_year",
                      "hours_effective_this_year"):
            value = project.get(field)
            if value is not None:
                assert math.isfinite(value) and value >= -1e-9, \
                    "active project %s has invalid %s=%r" % (project_id, field, value)
        allocated_fte += max(0.0, project.get("hours_effective_this_year") or 0.0) / 2000.0
        for trade, value in (project.get("lab_left") or {}).items():
            assert math.isfinite(value) and value >= -1e-9, \
                "active project %s has invalid assigned %s labor=%r" % (project_id, trade, value)
    assert allocated_fte <= demographics["working_age"] + 1e-6, \
        "allocated project labor %.3f FTE exceeds working population %.3f" % (
            allocated_fte, demographics["working_age"])
    return True
