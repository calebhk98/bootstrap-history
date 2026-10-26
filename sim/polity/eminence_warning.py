"""When the rising eminence of the household is announced: the one hazard no patron or bribe protects from."""

WARN_FROM_SHARE_OF_DANGER = 0.75
BAND_WIDTH_SHARE_OF_DANGER = 0.15


def eminence_band_to_announce(eminence, danger, band_already_said):
    """The band of eminence to announce this year, or None. Nothing is said at or below the warning share of the
    danger line, and each band is said once, only when eminence has climbed into a higher one than was last said."""
    if eminence <= danger * WARN_FROM_SHARE_OF_DANGER:
        return None
    band = int(eminence / max(1.0, danger * BAND_WIDTH_SHARE_OF_DANGER))
    return band if band > band_already_said else None
