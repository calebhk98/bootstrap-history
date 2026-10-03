"""The `education` screen (Complaints/94): literacy against its ceiling, the
schools that are running, the pools literacy limits and the trainees in the
pipeline. Every figure is read from the functions the engine already uses.
"""


def _fraction_of(value, ceiling):
    return round(value / ceiling, 4) if ceiling > 1e-9 else None


def _schools(sim):
    rows = []
    for node_id, spec in sim._effect_terms("schooling_flow"):
        if sim.fog and not sim.is_visible(node_id):
            continue
        holds = sim.effect_holds(node_id, spec)
        rows.append({
            "id": node_id, "name": sim.nodes[node_id]["name"],
            "built": bool(sim.has(node_id)), "running": bool(sim.running(node_id)),
            "required_for_any_schooling": bool(spec.get("required")),
            "units": round(sim.institution_units(node_id), 2) if holds else 0,
            "flow_added": round(sim.effect_value(node_id, spec), 4) if holds else 0.0})
    return rows


def _enrolment(sim, schools):
    """Split the whole society's literacy gain between the running schools by their share of the flow."""
    running = [row for row in schools if row["flow_added"] > 0]
    total_flow = sum(row["flow_added"] for row in running)
    next_year = sim.literacy_next_year()
    gain = (next_year.get("literacy_general", 0.0)
            - float(sim.civ.get("literacy_general", 0.0))) * sim.population.total
    for row in schools:
        share = row["flow_added"] / total_flow if total_flow > 0 and row["flow_added"] > 0 else 0.0
        row["share_of_schooling_flow"] = round(share, 4)
        row["people_made_literate_next_year"] = round(share * gain, 1)


def _limited_by(sim, general_share):
    if sim.effective_schooling_flow() <= 0.0:
        return "no school running"
    if general_share is not None and general_share >= 0.98:
        return "the ceiling (farm share and unschooled share)"
    return "the schooling flow"


def _pools(sim):
    return [{"trade": trade, "literacy_factor": round(sim.labour.literacy_factor(trade), 4),
             "most_you_can_ever_have": round(sim.labour.literate_capacity(trade), 2),
             "you_employ": round(sim.state.household.employees.get(trade, 0.0), 2)}
            for trade in sorted(sim.labour.LITERATE_TRADES) if sim.labour.trade_available(trade)]


def _trainees(sim):
    return [{"trade": record[2], "count": record[3], "ready_in_year": record[1]}
            for record in sim.state.household.training if len(record) > 3]


def _recent_change(sim):
    from .economy import _changes_baseline, _changes_moved
    now, baseline, error = _changes_baseline(
        getattr(sim, "_dashboard_history", None) or [], sim.year - 10, sim.year)
    if error:
        return {"note": error["error"]}
    moved = _changes_moved(baseline, now)
    return {"since_year": baseline["year"],
            "general": moved["literacy_general"], "elite": moved["literacy_elite"]}


def education_report(sim):
    general = float(sim.civ.get("literacy_general", 0.0))
    elite = float(sim.civ.get("literacy_elite", 0.0))
    ceiling_general = sim.literacy_ceiling_general()
    ceiling_elite = sim.literacy_ceiling_elite()
    next_year = sim.literacy_next_year()
    schools = _schools(sim)
    _enrolment(sim, schools)
    return {
        "ok": True,
        "literacy": {
            "general": round(general, 4), "general_ceiling": round(ceiling_general, 4),
            "share_of_ceiling_general": _fraction_of(general, ceiling_general),
            "general_next_year": round(next_year.get("literacy_general", general), 4),
            "elite": round(elite, 4), "elite_ceiling": round(ceiling_elite, 4),
            "share_of_ceiling_elite": _fraction_of(elite, ceiling_elite),
            "elite_next_year": round(next_year.get("literacy_elite", elite), 4),
        },
        "recent_change": _recent_change(sim),
        "schooling_flow": round(sim._schooling_flow(), 4),
        "effective_schooling_flow": round(sim.effective_schooling_flow(), 4),
        "printing_adopted": round(sim.information_diffusion_index(), 4),
        "farm_share_of_hours": round(sim.labour.farm_share_of_hours(), 4),
        "schools": schools,
        "literacy_limited_by": _limited_by(sim, _fraction_of(general, ceiling_general)),
        "literate_trades": _pools(sim),
        "trade_schools": {trade: seats for trade, seats
                          in (sim.state.household.trade_schools or {}).items()},
        "trainees": _trainees(sim),
        "not_held": ["the game keeps no record of why literacy moved in a "
                     "given year beyond the census line in `log`",
                     "per-school pupils are an attribution of the whole society's gain by "
                     "each school's share of the flow, not a count of enrolled children"],
    }
