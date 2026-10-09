"""Labourer-hours to break a tonne of rock at the face: by hand (and fire), or by drilled and charged
holes when a blasting technique runs. Standalone: hours and effects in, hours out."""

HARDNESS_ORDER = ("soft", "medium", "hard")


def breaking_hours_per_tonne_rock(hand_hours, fire_setting_hours, hardness_class, effects=None):
    """The cheaper of hand breaking with fire-setting and blasting. Blasting is the drilling of the
    holes (faster with machine drills) plus charging, tamping and firing them. The explosive's own
    making is not charged here (BLASTING_EXPLOSIVE_HOURS_NOT_CHARGED in deposits.py)."""
    effects = effects or {}
    by_hand = hand_hours + fire_setting_hours
    blasting = effects.get("blasting")
    if not blasting:
        return by_hand
    drilling_by_hardness, charging = blasting
    drilling = drilling_by_hardness[HARDNESS_ORDER.index(hardness_class)]
    return min(by_hand, drilling / effects.get("drilling_rate_multiple", 1.0) + charging)
