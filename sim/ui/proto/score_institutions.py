"""The institutions component of the score: the share of the capability institutions open and running."""


def institutions_component(sim):
    """The score's institutions entry. The sums run over the institutions in sorted order, so the figure does not
    depend on the iteration order of the set that holds them."""
    inst_keys = sorted(sim.CAPABILITY_INSTITUTIONS)
    inst_vals = []
    for institution_id in inst_keys:
        if institution_id in sim.SCALABLE_INSTITUTIONS:
            ceiling = max(1.0, sim.institution_unit_ceiling(institution_id))
            inst_vals.append(min(1.0, sim.institution_units(institution_id) / ceiling))
        else:
            inst_vals.append(1.0 if sim.running(institution_id) else 0.0)
    inst_norm = (sum(inst_vals) / len(inst_vals)) if inst_vals else 0.0
    finished_but_closed = [institution_id for institution_id in inst_keys
                           if sim.has(institution_id) and not sim.running(institution_id)]
    return {
        "counts": ("the fixed list of capability institutions, each counted only while it is "
                   "OPEN and running (those that scale count by units against a ceiling); "
                   "finished knowledge and a finished but shut concern score nothing"),
        "raw": sum(1 for value in inst_vals if value > 0.0),
        "of_total": len(inst_vals), "normalized": inst_norm,
        "counted": [institution_id for institution_id, value in zip(inst_keys, inst_vals) if value > 0.0],
        "finished_but_closed": finished_but_closed}
