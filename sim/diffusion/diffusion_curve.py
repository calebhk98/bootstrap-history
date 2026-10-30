"""The curve of a venture's edge leaking to imitators, as plain functions."""


def leaked_share(age_years, half_life_years, cap):
    """Share of a venture's edge that has leaked after it has run `age_years`: it halves the remainder every half-life
    and is capped, so a first mover never loses all of it."""
    share = 1.0 - 0.5 ** (max(0.0, age_years) / half_life_years)
    return min(cap, max(0.0, share))


def knowledge_half_life(base_half_life_years, corpus_pace, general_literacy, literacy_reference,
                        pace_base, pace_span, pace_cap_ratio, pace_floor):
    """Years for half of those who could copy a technique to have done so: the base half-life over the pace, which
    a dispersed corpus raises and so does the literacy of the country (as a share of the reference, capped)."""
    pace = corpus_pace * (pace_base + pace_span * min(pace_cap_ratio, general_literacy / max(0.02, literacy_reference)))
    return base_half_life_years / max(pace_floor, pace)
