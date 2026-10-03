"""Net yearly return, payback and foreman columns of an `available` row."""

_PAYBACK_HORIZON_YEARS = 100


def net_per_year(sim, node_id):
    return sim.venture_real_earnings(node_id) - sim.venture_real_upkeep(node_id)


def payback_years(sim, node_id, cost):
    """Years until the outlay is earned back, or None if it never is.

    Upkeep is paid in full from the first year while takings ramp up over
    the configured ramp, the same shape as Sim.venture_ramp.
    """
    full_earnings = sim.venture_real_earnings(node_id)
    upkeep = sim.venture_real_upkeep(node_id)
    if full_earnings <= 0 or full_earnings - upkeep <= 0:
        return None
    ramp_years = sim.cfg["revenue_ramp_years"]
    earned = 0.0
    for age in range(_PAYBACK_HORIZON_YEARS):
        year_net = full_earnings * min(1.0, (age + 1) / ramp_years) - upkeep
        if year_net > 0 and earned + year_net >= cost:
            return round(age + (cost - earned) / year_net, 1)
        earned += year_net
    return None


def specialist_foreman(sim, node_id):
    trade, fte = sim.venture_foreman(node_id)
    return {"trade": trade, "fte": round(fte, 2)} if trade else None


def sort_payback(sim, nodes, node_id):
    """Sort key: quickest payback first, never-paying rows last."""
    years = payback_years(sim, node_id, sim.project_cost(node_id))
    return float("inf") if years is None else years


def row_fields(sim, node_id, node):
    """The extra `available` row fields; empty ones are left out to keep
    the digest replies short.
    """
    fields = {"net_per_year": round(net_per_year(sim, node_id), 1),
              "payback_years": payback_years(sim, node_id, sim.project_cost(node_id)),
              "specialist_foreman": specialist_foreman(sim, node_id),
              "living_stock": sim.stock_needed_by(node_id) or None}
    return {key: value for key, value in fields.items() if value is not None}
