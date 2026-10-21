"""Coverage, disease-burden and roll-out rules as plain functions (Complaint 190)."""

# a rollout asking for fewer units than this more is already covered
ROLLOUT_MINIMUM_UNITS = 0.02


def people_per_unit(annual_staff_hours, staff_hours_per_person_year):
    """How many people one unit serves: its yearly staff hours over the hours each person needs."""
    return annual_staff_hours / staff_hours_per_person_year


def people_who_can_use(population, eligible_share):
    """The people the work could serve: the population times the share eligible, at least one."""
    return max(1.0, population * eligible_share)


def coverage_share(is_running, units, people_per_unit_served, people_eligible):
    """The share of eligible people served, 0 to 1; nothing while the doors are shut."""
    if not is_running:
        return 0.0
    return min(1.0, units * people_per_unit_served / people_eligible)


def units_for_coverage(share, people_eligible, people_per_unit_served):
    """The units that serve `share` of the eligible people."""
    return share * people_eligible / people_per_unit_served


def rollout_units(wanted_units, units_open):
    """Units to open for a rollout: the whole want when nothing is open, else what is still wanted.
    None when what is still wanted is below the minimum (already covered)."""
    if wanted_units - units_open < ROLLOUT_MINIMUM_UNITS:
        return None
    return wanted_units - units_open if units_open > 0.0 else wanted_units


def disease_burden(weights, held_share, pre_industrial_burden):
    """1 less the held share of the total weight, clamped to [0, 1]. `weights` maps technology to its weight;
    `held_share(technology)` is 0 to 1; no weight at all leaves the pre-industrial burden."""
    total_weight = sum(weights.values())
    if total_weight <= 0.0:
        return pre_industrial_burden
    unlocked_weight = sum(weight * held_share(technology) for technology, weight in weights.items())
    return max(0.0, min(1.0, 1.0 - unlocked_weight / total_weight))
