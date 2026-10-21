"""The arithmetic of prominence: the yearly hazard, the chance of ruin, and when and how far withdrawing from public life
lowers it. Plain functions of the figures they are given; the constants are the caller's declared heuristics."""

WITHDRAW_DEAD = "dead"
WITHDRAW_TOO_SOON = "too_soon"
WITHDRAW_UNNOTICED = "unnoticed"
WITHDRAW_ALREADY_OBSCURE = "already_obscure"
OBSCURITY_MARGIN = 0.5   # reputation points above the standing floor at which there is nothing left to give up


def yearly_hazard(reputation, capital, familiarity, danger_weight, reputation_scale, wealth_threshold, base_scale,
                  reputation_share, wealth_share, familiarity_relief, effect_factor):
    """Eminence gained in a year: reputation (squared, so the already famous dominate) and visible wealth mixed, scaled
    by the civilisation's weight, shaped by `effect_factor` (what stands between the founder and the throne), and
    softened by how unsurprising the founder has become."""
    renown = max(0.0, reputation) / reputation_scale
    wealth = min(1.0, max(0.0, capital) / wealth_threshold)
    hazard = base_scale * danger_weight * (reputation_share * renown * renown + wealth_share * wealth)
    hazard = effect_factor(hazard)
    return hazard * (1.0 - familiarity_relief * familiarity)


def chance_of_ruin(eminence, danger, hazard_scale):
    """The chance this year that prominence lands an event: nothing below the danger line, rising linearly above it."""
    return max(0.0, (eminence - danger) / hazard_scale)


def withdrawal_refusal(alive, last_withdrawal, year, wait_years, eminence, danger, min_fraction, reputation, floor):
    """Why withdrawing from public life would buy nothing, or None when it would. It must not take the price when
    there is nothing to buy."""
    if not alive:
        return WITHDRAW_DEAD
    if last_withdrawal is not None and year - last_withdrawal < wait_years:
        return WITHDRAW_TOO_SOON
    if eminence < danger * min_fraction:
        return WITHDRAW_UNNOTICED
    if reputation <= floor + OBSCURITY_MARGIN:
        return WITHDRAW_ALREADY_OBSCURE
    return None


def after_withdrawal(reputation, eminence, floor, reputation_retention, eminence_retention):
    """(reputation, eminence) once withdrawn: reputation keeps part of its gap above the floor the work alone earns, and
    eminence keeps a share."""
    return floor + (reputation - floor) * reputation_retention, eminence * eminence_retention
