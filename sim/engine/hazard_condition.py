"""What a dated hazard becomes once the household has (or lacks) the techs its `condition` names."""


def hazard_given_condition(hazard, condition_met):
    """The hazard unchanged, or a shallow copy with the condition's one field averted or scaled.

    `outcome` "avert" drops the field; "alter" keeps `alter_scale` of the shortfall (1 minus the
    field for output_factor, the field itself for the rest). Nothing else on the hazard changes."""
    condition = hazard.get("condition")
    if not condition:
        return hazard
    field = condition.get("field")
    if not condition_met or field not in hazard:
        return hazard
    adjusted = dict(hazard)
    outcome = condition.get("outcome")
    scale = condition.get("alter_scale", 1.0)
    if outcome == "avert":
        del adjusted[field]
    elif outcome == "alter":
        if field == "output_factor":
            adjusted[field] = 1.0 - (1.0 - hazard[field]) * scale
        else:
            adjusted[field] = hazard[field] * scale
    return adjusted
