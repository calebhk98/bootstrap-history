"""Plain rules for how far a founder's work has spread into the wider society, called with figures and not a game."""


def spread_share(age_years, half_life_years):
    """0..1: half the society has adopted after one half-life, and never more than all of it."""
    return max(0.0, min(1.0, 1.0 - 0.5 ** (age_years / half_life_years)))


def medical_compliance(compliance_base, state_capacity):
    """The share following public-health guidance: a base with no administration, the rest from state capacity."""
    return compliance_base + (1.0 - compliance_base) * state_capacity


def medical_relief(diffusion_index, compliance_base, state_capacity):
    """Coverage times how far people follow the guidance; no fixed ceiling short of full coverage and compliance."""
    return min(1.0, diffusion_index * medical_compliance(compliance_base, state_capacity))


def weapons_relief(per_weapon, weapons):
    """(multiplier on the harm, reason) for the state holding `weapons` of the founder's weapons; each removes its
    share of what is left."""
    if weapons <= 0:
        return 1.0, None
    return ((1.0 - per_weapon) ** weapons,
            "the state's own armies now carry %d of the weapons you worked out" % weapons)
